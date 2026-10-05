from simconfig import SimConfig
from models import VehicleState, TimeStamps
from vehicle import Vehicle
import traci
import math
import random
import helper

class VehicleManager():
    def __init__(self, simconfig):
        self.simconfig: SimConfig = simconfig
        self.vehicle_list: list[Vehicle] = []
        self.vehicles_added_in_current_interval = 0

    def add_vehicle(self, vid, target_edge, state):
        if any(v.get_vehicle_id() == vid for v in self.vehicle_list):
            return(False)

        new_vehicle = Vehicle(
            vid=vid,
            distance_expectation=self.simconfig.get_distance_expectation(),
            search_radius=self.simconfig.get_search_radius(),
            price_expectation=self.simconfig.get_price_expectation(),
            state=state,
            target_edge=target_edge,
            observation_window_size=self.simconfig.get_observation_window_size()
        )

        self.vehicle_list.append(new_vehicle)
        self.vehicles_added_in_current_interval +=1
        return(True)


    def generate_cruising_route(self, vid, current_edge, current_lane):
        new_route = [(current_edge, current_lane)]
        vehicle = self.get_vehicle_by_id(vid=vid)
        vehicle_max_distance = vehicle.get_search_radius()
        vehicle_target_pos = vehicle.get_target_position()

        used_edge = current_edge

        routing_recursion_depth = self.simconfig.get_routing_lookahead_depth()
        edges_planed = 0

        new_route = [(current_edge, current_lane)]

        while edges_planed < routing_recursion_depth:
            used_junction = traci.edge.getToJunction(edgeID=used_edge)

            junction_pos = traci.junction.getPosition(junctionID=used_junction)
            target_vektor = helper.get_vektor_of_two_points(junction_pos, vehicle_target_pos)

            lane_count = traci.edge.getLaneNumber(edgeID=used_edge)
            lanes_available = []
            for lane_number in range(0, lane_count):
                lane_name = used_edge + "_" + str(lane_number)
                if "passenger" in traci.lane.getAllowed(laneID=lane_name):
                    lanes_available.append(lane_name)

            amount_of_usable_lanes = len(lanes_available)

            lane_links = ()
            for lane_link_runner in lanes_available:
                lane_links += traci.lane.getLinks(laneID=lane_link_runner)

            local_options = []

            for available_links in lane_links:
                available_lane = available_links[0]

                if "passenger" not in traci.lane.getAllowed(laneID=available_lane):
                    continue

                available_edge = traci.lane.getEdgeID(laneID=available_lane)

                edge_vektor = helper.get_edge_vektor(available_edge)
                angle_to_target = helper.calc_crossproduct(edge_vektor, target_vektor)

                edge_repeatings = vehicle.get_edge_repeatings(available_edge)

                local_option = {"edge": available_edge,
                                "lane": available_lane,
                                "angle": round(angle_to_target / 45) * 45,
                                "repeatings": edge_repeatings,
                                "seed": random.randint(1, 100)}
                local_options.append(local_option)
            
            distance_to_target = traci.simulation.getDistance2D(x1=vehicle_target_pos[0], y1=vehicle_target_pos[1],
                                                                x2=junction_pos[0], y2=junction_pos[1], isDriving=False)
            
            if len(local_options) == 0:
                break

            # inside max distance
            if distance_to_target < vehicle_max_distance:
                best_option = min(local_options, key=lambda option: (option["repeatings"], option["angle"], option["seed"]))

            # outside max distance 
            else:
                best_option = min(local_options, key=lambda option: (option["angle"], option["repeatings"], option["seed"]))
            
            # append new edge
            new_edge = best_option["edge"]
            new_lane = best_option["lane"]
            new_route.append((new_edge, new_lane))
            vehicle.add_visited_edge(new_edge)
            edges_planed += 1
            used_edge = new_edge

            # prevent short last edge
            edge_length = traci.lane.getLength(new_route[-1][0] + "_" + new_route[-1][1][-1])
            if (len(new_route) >= routing_recursion_depth) and (edge_length < 20):
                routing_recursion_depth +=1

            # prevent end on higway
            elif amount_of_usable_lanes > 1:
                routing_recursion_depth +=1
    
        # apply new route
        new_route_only_edges = [e[0] for e in new_route]

        traci.vehicle.setRoute(vehID=vid, edgeList=new_route_only_edges)
        edge_length = traci.lane.getLength(new_route[-1][1])

        # set stop markers at the end of the edge
        stops = list(traci.vehicle.getStops(vehID=vid))
        try:
            if len(stops) >= 1:
                traci.vehicle.replaceStop(nextStopIndex=0, edgeID=new_route[-1][0], duration=7, vehID=vid, laneIndex=new_route[-1][1][-1], pos=int(edge_length*0.5))
            else:
                traci.vehicle.setStop(edgeID=new_route[-1][0], duration=0, vehID=vid, laneIndex=new_route[-1][1][-1], pos=int(edge_length*0.9))
        except traci.exceptions.TraCIException as e:
            pass
            
        # reapply route to prevent rerouting by stops
        traci.vehicle.setRoute(vehID=vid, edgeList=new_route_only_edges)


    def park_in(self, vid, current_edge, current_lane):
        # generate a valid parking stop
        edge_length = traci.lane.getLength(laneID=current_lane)
        duration = self.simconfig.get_park_in_delay_in_seconds() + 1
        #TODO: needs testing
        while True:    
            if edge_length < 20:
                parking_position = int(edge_length)
            else:
                parking_position = max(20, int(edge_length * (random.randint(0, 100) / 100)))
            print(f"{vid} parking position={parking_position}")
            traci.vehicle.setRoute(vehID=vid, edgeList=[(current_edge)])
            try:
                traci.vehicle.setStop(edgeID=current_edge,duration=duration,vehID=vid, laneIndex=current_lane[-1],pos=parking_position)
                break
            except traci.exceptions.TraCIException:
                print("parking stop to close to break")


    
    def get_vehicle_by_id(self, vid) -> Vehicle:
        vehicle = next(
                    (v for v in self.vehicle_list if v.get_vehicle_id() == vid),
                    None)
        return(vehicle)
    
    def _get_vehicle_count_by_state(self, state: VehicleState) -> int:
        return(sum(1 for v in self.vehicle_list if v.get_state() == state))
    
    def set_vehicle_state(self, vid, state):
        vehicle = self.get_vehicle_by_id(vid)
        vehicle.set_state(state)


    def get_cruising_traffic_share(self):
        all_vehicles = traci.vehicle.getIDCount()
        cruising_traffic = self._get_vehicle_count_by_state(VehicleState.CRUISING_FOR_PARKING)
        
        if all_vehicles == 0:
            cruising_traffic_share = 0
        else:
            cruising_traffic_share = int(cruising_traffic / all_vehicles * 100)
        
        return(cruising_traffic_share)
    
    def remove_vehicle(self, vid):
        vehicle = self.get_vehicle_by_id(vid)
        self.vehicle_list.remove(vehicle)

    def clear_unremoved_vehicles(self):
        traci_vehicles = traci.vehicle.getIDList()
        for vehicle in self.vehicle_list:
            vid = vehicle.get_vehicle_id()
            if vid not in traci_vehicles:
                self.remove_vehicle(vid=vid)

    def get_vehicle_count(self):
        return(len(self.vehicle_list))
    
    def get_vehicles_added(self):
        return self.vehicles_added_in_current_interval
    
    def clear_vehicles_added(self):
        self.vehicles_added_in_current_interval = 0