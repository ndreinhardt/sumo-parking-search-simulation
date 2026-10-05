from simconfig import SimConfig
import math
from data_exporter import DataExporter
from models import ParkingAreaType, VehicleState, TimeStamps
from parking_area import ParkingArea
from vehicle import Vehicle, ObservedEdge
from vehicle_manager import VehicleManager
from parking_area_manager import ParkingAreaManager
from parking_area_utility_calculator import ParkingAreaCostCalculator
import traci
from datetime import datetime
import helper


class SumoStepListener(traci.StepListener):
    vehicle_manager: VehicleManager
    simconfig: SimConfig
    parking_area_manager: ParkingAreaManager
    cost_calculator: ParkingAreaCostCalculator

    def __init__(self, vehicle_manager, simconfig: SimConfig, parking_area_manager, exporter: DataExporter, debug_vehicle: str):
        super().__init__()
        self.vehicle_manager = vehicle_manager
        self.simconfig = simconfig
        self.parking_area_manager = parking_area_manager
        self.exporter = exporter
        self.debug_vehicle = debug_vehicle
        self.cost_calculator = ParkingAreaCostCalculator(simconfig=self.simconfig)

    # do a step in simulation
    def step(self, t):
        now = traci.simulation.getTime()

        # iterate trough all persons
        for person in traci.person.getIDList():
            # get  vehicle id
            vid = traci.person.getVehicle(person)
            # ignore persons who are not in a vehicle
            if vid == "":                                           
                continue

            # get route informations
            route = traci.vehicle.getRoute(vid)
            route_index = traci.vehicle.getRouteIndex(vid)

            # get vehicle and position
            vehicle = self.vehicle_manager.get_vehicle_by_id(vid)
            current_lane = traci.vehicle.getLaneID(vid)
            # ignore vehicles which are not on the road
            if current_lane == "":
                continue
            current_edge = traci.lane.getEdgeID(current_lane)

            # ------------------------------------------------------------------------------------------
            # do state transitions
            # ------------------------------------------------------------------------------------------
            if vehicle != None:
                vehicle_state = vehicle.get_state()
                remaining_distance = vehicle.get_distance_to_target_edge(edge=current_edge)

                # ignore vehicle outside city
                if vehicle_state == VehicleState.IGNORE:
                    continue

                # generate new routes if current edge is last edge
                if (route_index >= len(route)-1) and (vehicle_state != VehicleState.PARKING_MANEUVER):
                    self.vehicle_manager.set_vehicle_state(vid=vid, state=VehicleState.ROUTING)

                # set vehicles to observating when they get inrange           
                elif (remaining_distance <= vehicle.get_search_radius()) and (vehicle_state == VehicleState.INCOMING):
                    traci.vehicle.highlight(vid, (0,160,255,255)) # blue
                    self.vehicle_manager.set_vehicle_state(vid=vid, state=VehicleState.CRUISING_TO_TARGET)
                    vehicle.add_timestamp(key=TimeStamps.START_OF_CRUISING, value=now)
    
            # create vehicle objects       
            else:
                # check if vehicle target is in the city
                vehicle_targe_edge = route[-1]
                city_center = self.simconfig.get_city_center()
                if helper.check_if_edge_in_city(edge=vehicle_targe_edge, city_center=city_center) and "bus" not in vid:
                    new_vehicle_state = VehicleState.INCOMING
                else:
                    new_vehicle_state = VehicleState.IGNORE

                # add vehicle to python
                self.vehicle_manager.add_vehicle(vid=vid,state=new_vehicle_state, 
                                                    target_edge=vehicle_targe_edge)
                new_vehicle = self.vehicle_manager.get_vehicle_by_id(vid=vid)
                new_vehicle.add_timestamp(key=TimeStamps.START_OF_TRAVEL, value=now)

                # print target dot and search radius of vehicle
                if self.simconfig.get_debug_mode() and new_vehicle_state != VehicleState.IGNORE:
                    new_vehicle.add_vehicle_marker()

                continue

            # ------------------------------------------------------------------------------------------
            # handle vehicle states
            # ------------------------------------------------------------------------------------------
            vehicle_state = vehicle.get_state()

            # ignore connector edges
            if current_edge[0] == ":":
                        continue

            # check edge only once (step listener is checking edge n times) 
            # but check same edge if vehicle is in parking maneuver
            # thats why below if-statements are used instead of elif
            if (not vehicle.is_on_new_edge(current_edge)) and (vehicle_state != VehicleState.PARKING_MANEUVER):
                continue

            # generate new section for cruising    
            if vehicle_state == VehicleState.ROUTING:
                self.vehicle_manager.generate_cruising_route(vid=vid, 
                                                            current_edge=current_edge, 
                                                            current_lane=current_lane)
                
                self.vehicle_manager.set_vehicle_state(vid=vid,state=VehicleState.CRUISING_FOR_PARKING)      
                #traci.vehicle.highlight(vid, (100,255,0,255)) # green    

            # check parking areas
            if (vehicle_state == VehicleState.CRUISING_TO_TARGET) or (vehicle_state == VehicleState.CRUISING_FOR_PARKING):
                available = self.parking_area_manager.check_edge_for_parking_areas(edge=current_edge)

                # no parking areas on current edge or outside radius
                if (len(available) == 0) or (remaining_distance > vehicle.get_search_radius()):
                    # TODO: ovserved edge removen, ist outside radius
                    new_observed_edge = ObservedEdge(edge=current_edge, available=0)
                    vehicle.add_observed_edge(new_observed_edge)

                # check / analyse all parking opportunities
                for area in available:
                    price_observations= vehicle.get_price_observations()
                    distance_observations = vehicle.get_distance_observations()

                    remaining_distance = helper.get_distance_between_edges(edge1=area.get_edge(), edge2=vehicle.get_target_edge())

                    # vehicle debugging
                    if self.debug_vehicle != None and self.debug_vehicle == vid:
                        print(f"\n---\narea option {area.get_edge()} evaluate {remaining_distance}m/{area.get_costs()}€")
                        print(f"vid {vehicle.get_vehicle_id()} observation average {vehicle.get_distance_average()}m/{vehicle.get_price_average()}€")
                        print(f"full observations {vehicle.get_observation_count()}c/{vehicle.get_distance_observations()}/{vehicle.get_price_observations()}")

                    choose_area = self.cost_calculator.evaluate_parking_area(distance_obervations=distance_observations, 
                                    price_obersvations=price_observations, parking_area_price=area.get_costs(),
                                    parking_area_distance=remaining_distance, scoutings=vehicle.get_observation_count(),
                                    observation_length=vehicle.get_observation_length(), distance_to_target=remaining_distance,
                                    vehicle_state=vehicle_state)
                    
                    # take parking area
                    if choose_area:
                        # vehicle debugging
                        if self.debug_vehicle != None and self.debug_vehicle == vid:
                            print(f"vid {vid} takes parking area {area.get_area_id()}")

                        self.vehicle_manager.set_vehicle_state(vid=vid, state=VehicleState.PARKING_MANEUVER)
                        traci.vehicle.setColor(vid, (255,60,0,255))  # red 
                        self.vehicle_manager.park_in(vid=vid, current_edge=current_edge, current_lane=current_lane)
                        # +1 is buffer to remove vehicle before it starts driving again
                        park_in_timestamp = now + self.simconfig.get_park_in_delay_in_seconds() + 1 
                        vehicle.set_park_in_done_timestamp(timestamp=park_in_timestamp)
                        release_timestamp =  park_in_timestamp + self.simconfig.get_parking_duration() * 60
                        self.parking_area_manager.park_vehicle(area_id=area.get_area_id(), release_timestamp=release_timestamp)
                        break

                    # dont take parking area
                    else:
                        # vehicle debugging
                        if self.debug_vehicle != None and self.debug_vehicle == vid:
                            print(f"vid {vid} dont takes parking area {area.get_area_id()}")

                        price_observations = []
                        distance_observations = []

                        occupacity = area.get_available()
                        target_edge = vehicle.get_target_edge()
                        distance = helper.get_distance_between_edges(edge1=current_edge, edge2=target_edge)
                        price = area.get_costs()
            
                        vehicle.add_observations(distances=[distance], prices=[price])
                        new_observed_edge = ObservedEdge(edge=current_edge, available=occupacity)
                        vehicle.add_observed_edge(new_observed_edge)

                vehicle.update_edge_status(edge=current_edge)  
            
            elif (vehicle_state == VehicleState.PARKING_MANEUVER) and (now - vehicle.get_park_in_done_timestamp() > -1):
                try:
                    traci.vehicle.remove(vehID=vid)
                except:
                    print(f"DEBUG: vehicle konnte nicht removed werden (schon weg)")

                vehicle.add_timestamp(key=TimeStamps.END_OF_CRUISING, value=now)
                if vehicle.validate_timestamps():
                    self.exporter.add_arrived_vehicle(cruising_time=vehicle.get_cruising_time(), remaining_distance=remaining_distance,
                                                    travel_time=vehicle.get_travel_time(), vid=vid, cruising_time_share=vehicle.get_cruising_time_share(),
                                                    track_length=vehicle.get_total_track_length(), 
                                                    departure_timestamp=vehicle.get_timestamp(key=TimeStamps.START_OF_CRUISING), arrival_timestamp=now)
                break


        # clear parking areas
        if traci.simulation.getTime() % 60 == 0:
            self.parking_area_manager.clear_parking_areas(time_now=now)

        # add global metrics
        if traci.simulation.getTime() % self.simconfig.get_update_interval() == 0:
            self.exporter.add_global_metric(timestamp=now)
            self.exporter.export_global_metrics()
            self.exporter.export_vehicle_metrics()

            sim_duration = self.simconfig.get_sim_end() - self.simconfig.get_sim_start()
            sim_done = now - self.simconfig.get_sim_start()
            progress = math.ceil(sim_done / sim_duration * 100)
            print(f"\rSimulation-Progress: {progress}%   ", end="")

            # export current stats
            self.exporter.export_live_metrics(progress=progress)

            # clear overseen vehicles
            self.vehicle_manager.clear_unremoved_vehicles()

        return True