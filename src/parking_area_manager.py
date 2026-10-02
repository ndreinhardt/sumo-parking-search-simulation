import traci
import math
from models import ParkingAreaType
from parking_area import ParkingArea
from simconfig import SimConfig
import json
import helper

class ParkingAreaManager():
    def __init__(self, simconfig: SimConfig):
        self.simconfig = simconfig
        self.parking_areas: list[ParkingArea] = []

    def check_edge_for_parking_areas(self, edge) -> list[ParkingArea]:
        available = []
        for area in self.parking_areas:
            if (area.get_edge() == edge) and (area.get_available() >= 1):
                available.append(area)    
        return available


    # TODO: implement a check for parking areas on this edge
    def check_edge_for_parking_slots(self, edge):
        return None


    def init_parking_areas(self):
        parking_area_count = 0
        initial_occupacity = self.simconfig.get_initial_occupacity()

        # _init_off_street_parking_areas
        off_street_parking_areas = []
        parking_areas_path = self.simconfig.get_parking_area_file_path()
        parking_areas = []
        try:
            with open(parking_areas_path, "r", encoding="utf-8") as f:
                parking_areas = json.load(f)
                print(f"ParseParkingAreas: {parking_areas_path} syntax valid.")
        except json.JSONDecodeError as e:
            print(f"ParseParkingAreas: JSON-Error in {parking_areas_path}")
            print(f"ParseParkingAreas: Error in Line {e.lineno}, column {e.colno}")
            print(e)
        except FileNotFoundError as e:
            print(f"ParseParkingAreas: file {parking_areas_path} not foundss")

        #off_street = traci.parkingarea.getIDList()

        for area in parking_areas:
            edge = traci.lane.getEdgeID(laneID=area["lane"])
            costs = self.simconfig.get_off_street_parking_costs()
            area_type = ParkingAreaType.OFF_STREET
            new_parking_area = ParkingArea(capacity=area["capacity"], costs=costs, edge=edge, 
                                           type=area_type, pid=parking_area_count, initial_occupacity=initial_occupacity)
            parking_area_count +=1
            off_street_parking_areas.append(new_parking_area)

        print(f"InitParkingAreas: added {len(off_street_parking_areas)} off_street parking areas")


        # _init_on_street_parking_areas
        on_street_parking_areas = []
        density = self.simconfig.get_on_street_capacity()

        parking_edges = []
        for edge in traci.edge.getIDList():
            drivable_lane_count = 0
            for lane_number in range (0, traci.edge.getLaneNumber(edge)):
                if ("pedestrian" not in traci.lane.getAllowed(laneID=edge + "_" + str(lane_number))) and (edge[0] != ":"):
                    drivable_lane_count +=1
                    
            if drivable_lane_count == 1:
                parking_edges.append(edge)
                    
        for edge in parking_edges:
            length = traci.lane.getLength(edge + "_0")
            capacity = int(length / 100 * density)
            if capacity <= 0:
                continue

            costs = self.simconfig.get_on_street_parking_costs()
            area_type = ParkingAreaType.ON_STREET
            new_parking_area = ParkingArea(capacity=capacity, costs=costs, edge=edge, 
                                           type=area_type, pid=parking_area_count, initial_occupacity=initial_occupacity)
            parking_area_count +=1
            on_street_parking_areas.append(new_parking_area)


        print(f"InitParkingAreas: added {len(on_street_parking_areas)} on_street parking areas")

        self.parking_areas = on_street_parking_areas + off_street_parking_areas

        print(f"InitParkingAreas: initialized {len(self.parking_areas)} total parking areas")

        if self.simconfig.get_debug_mode():
            for area in self.parking_areas:
                area.add_poi()
            print(f"InitParkingAreas: added POIs to all Parking areas")

        # add city center marker
        if self.simconfig.get_debug_mode():
            city_center = self.simconfig.get_city_center()
            traci.poi.add(color=(0,155,0,255), x=city_center[0], y=city_center[1], poiID="city_center", 
                                poiType="marker", width=city_center[2]*2, height=city_center[2]*2, layer=0)

    def park_vehicle(self, area_id, release_timestamp):
        area = next(
                    (a for a in self.parking_areas
                    if a.area_id == area_id),
                    None
                )
        area.reservate_parking_slot(release_timestamp=release_timestamp)


    def get_overall_parking_area_occupacity(self):
        on_street_nominal_max = 0
        on_street_nominal_occupacity = 0
        off_street_nominal_max = 0
        off_street_nominal_occupacity = 0

        for area in self.parking_areas:
            if area.get_type() == ParkingAreaType.ON_STREET:
                on_street_nominal_max += area.get_capacity()
                on_street_nominal_occupacity += area.get_occupacity()
            elif area.get_type() == ParkingAreaType.OFF_STREET:
                off_street_nominal_max += area.get_capacity()
                off_street_nominal_occupacity += area.get_occupacity()
        
        # calc on street metrics
        if on_street_nominal_max == 0:
            on_street_share = 0
        else:
            on_street_share = round(on_street_nominal_occupacity / on_street_nominal_max * 100)
        
         # calc off street metrics
        if off_street_nominal_max == 0:
            off_street_share = 0
        else:
            off_street_share = round(off_street_nominal_occupacity / off_street_nominal_max * 100)

        # calc global metrics
        global_nominal_max = on_street_nominal_max + off_street_nominal_max
        global_nominal_occupacity = on_street_nominal_occupacity + off_street_nominal_occupacity

        if global_nominal_max == 0:
            global_share = 0
        else:
            global_share = round(global_nominal_occupacity / global_nominal_max * 100)

        data = {"on_street_nominal_max": on_street_nominal_max,
                "on_street_nominal_occupacity": on_street_nominal_occupacity,
                "on_street_occupacity_share": on_street_share,
                "off_street_nominal_max": off_street_nominal_max,
                "off_street_nominal_occupacity": off_street_nominal_occupacity,
                "off_street_occupacity_share": off_street_share,
                "global_nominal_max": global_nominal_max,
                "global_nominal_occupacity": global_nominal_occupacity,
                "global_occupacity_share": global_share}
        
        return(data)
    
    def clear_parking_areas(self, time_now):
        global_releases = 0
        for area in self.parking_areas:
            area_releases = 0
            delete_timestamps = []
            release_timestamps = area.get_release_timestamps() 
            for timestamp in release_timestamps:
                if time_now >= timestamp:
                    area_releases +=1
                    delete_timestamps.append(timestamp)

            area.release_parking_slots(area_releases)
            for remove in delete_timestamps:
                area.remove_release_timestamp(remove)
            global_releases += area_releases

            area.update_poi_image()