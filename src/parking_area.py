from models import ParkingAreaType
import traci
import os
import helper

class ParkingArea():
    def __init__(self, type, costs, capacity, edge, pid, initial_occupacity):
        self.type = type
        self.costs = costs
        self.capacity = capacity
        self.edge = edge
        self.area_id = pid
        self.occupacity = round(capacity * initial_occupacity / 100)
        self.release_timestamps = []     
        self.target_position = helper.get_middle_of_edge_position(edge=edge)


    def get_type(self):
        return self.type

    def get_costs(self):
        return self.costs

    def get_capacity(self):
        return self.capacity
    
    def get_occupacity(self):
        return self.occupacity

    def get_edge(self):
        return self.edge
    
    def get_area_id(self):
        return self.area_id

    def get_vehicle_list(self):
        return self.vehicle_list    
    
    def get_available(self) -> int:
        return(int(self.get_capacity() - self.get_occupacity()))
    
    def reservate_parking_slot(self, release_timestamp):
        self.occupacity +=1
        self.release_timestamps.append(release_timestamp)
        self.update_poi_image()
        return True
    
    def get_release_timestamps(self):
        return self.release_timestamps
    
    def remove_release_timestamp(self, timestamp):
        self.release_timestamps.remove(timestamp)
    
    def release_parking_slots(self, amount):
        self.occupacity -=amount

    def add_poi(self):
        if self.type == ParkingAreaType.OFF_STREET:
            imgFile=os.path.abspath("./src/img/off_street_0.png")
            size = 10
            layer = 11
        elif self.type == ParkingAreaType.ON_STREET:
            imgFile=os.path.abspath("./src/img/on_street_0.png")
            size = 10
            layer = 10

        x_offset = 0
        if self.edge[0] == "-":
            x_offset = 10

        poi_id = "pid" + str(self.area_id)
        traci.poi.add(color=(100,255,255,255), x=self.target_position[0]+x_offset, y=self.target_position[1], poiID=poi_id, 
                      poiType="parking", width=size, height=size, layer=layer, imgFile=imgFile)
        self.update_poi_image()


    def update_poi_image(self):

        amount = self.get_available()

        if self.type == ParkingAreaType.OFF_STREET:
            img_prefix = "off_street_"
        elif self.type == ParkingAreaType.ON_STREET:
            img_prefix = "on_street_"

        if amount > 50:
            imgFile = os.path.abspath(f"./src/img/{img_prefix}50_plus.png")
        elif amount > 20:
            imgFile = os.path.abspath(f"./src/img/{img_prefix}20_plus.png")
        elif amount > 10:
            imgFile = os.path.abspath(f"./src/img/{img_prefix}10_plus.png")
        elif amount > 5:
            imgFile = os.path.abspath(f"./src/img/{img_prefix}5_plus.png")
        else:
            imgFile = os.path.abspath(f"./src/img/{img_prefix}{amount}.png")

        poi_id = "pid" + str(self.area_id)

        traci.poi.setImageFile(imageFile=imgFile, poiID=poi_id)