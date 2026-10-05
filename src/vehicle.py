from models import VehicleState, TimeStamps
import traci
import helper
import random


# TODO: remove visited edges, go only for observed edges
class ObservedEdge():
    def __init__(self, edge, available):
        self.edge = edge
        self.available = available
        self.length = traci.lane.getLength(laneID=edge + "_0")

    def get_edge(self):
        return self.edge

    def get_available(self):
        return self.available

    def set_edge(self, edge):
        self.edge = edge

    def set_available(self, available):
        self.available = available

    def get_length(self):
        return(round(self.length))

    
class Vehicle():
    def __init__(self, state, vid, target_edge, search_radius, price_expectation, distance_expectation, observation_window_size):
        self.state = state
        self.vehicle_id = vid
        self.search_radius = search_radius
        self.price_observations = [price_expectation]
        self.distance_observations = [distance_expectation]
        self.target_edge = target_edge
        self.observed_edges = []
        self.visited_edges = []
        self.recent_edge = None
        self.observation_window_size = observation_window_size
        self.target_position = helper.get_middle_of_edge_position(edge=target_edge)
        self.timestamps = {TimeStamps.START_OF_TRAVEL: None,
                  TimeStamps.START_OF_CRUISING: None,
                  TimeStamps.END_OF_CRUISING: None,
                  TimeStamps.PARK_IN_DONE: None}
    

    def get_state(self):
        return self.state

    def get_vehicle_id(self):
        return self.vehicle_id

    def get_search_radius(self):
        return self.search_radius

    def get_price_observations(self):
        return self.price_observations

    def get_distance_observations(self):
        return self.distance_observations
    
    def get_target_edge(self):
        return self.target_edge
    
    def get_observed_edges(self):
        return self.observed_edges
    
    def get_visited_edges(self):
        return self.visited_edges
    
    def get_target_edge_visited(self):
        return self.target_edge_visited
    
    def get_target_position(self):
        return self.target_position
    
    def get_timestamp(self, key):
        return self.timestamps[key]
    
    def get_distance_average(self):
        return(round(sum(self.distance_observations) / len(self.distance_observations)))
    
    def get_price_average(self):
        return(round(sum(self.price_observations) / len(self.price_observations), 2))
    
    def validate_timestamps(self):
        if self.timestamps[TimeStamps.START_OF_CRUISING] == None:
            return False
        if self.timestamps[TimeStamps.START_OF_TRAVEL] == None:
            return False
        if self.timestamps[TimeStamps.END_OF_CRUISING] == None:
            return False
        return True
    
    def get_cruising_time(self):
        if self.validate_timestamps():
            delta = (self.timestamps[TimeStamps.END_OF_CRUISING] - self.timestamps[TimeStamps.START_OF_CRUISING])
            cruising_time = round((delta // 60) + ((delta % 60) / 60),2)
            return cruising_time
        else:
            return(False)
    
    def get_travel_time(self):
        if self.validate_timestamps():
            delta = (self.timestamps[TimeStamps.START_OF_CRUISING] - self.timestamps[TimeStamps.START_OF_TRAVEL])
            travel_time = round((delta // 60) + ((delta % 60) / 60),2)
            return travel_time
        else:
            return(False)
    
    def get_cruising_time_share(self):
        full_time = self.get_cruising_time() + self.get_travel_time()
        # vehicle spawns inrange, and accepts parking area immediately
        if full_time == 0:
            return(0)
        else:
            return(round(self.get_cruising_time() / full_time * 100))
    
    def get_edge_repeatings(self, edge):
        return(self.visited_edges.count(edge))
    
    def get_observation_length(self):
        length_sum = sum(e.get_length() for e in self.observed_edges)
        return(length_sum)
    
    def get_observation_count(self):
        n = sum(p.get_available() for p in self.observed_edges)
        return(n)
    
    def get_distance_to_target_edge(self, edge):
        return(helper.get_distance_between_edges(edge1=edge,edge2=self.target_edge))
    
    def get_total_track_length(self):
        total_track_length = 0
        for edge in self.visited_edges:
            edge_length = round(traci.lane.getLength(laneID=edge + "_0"))
            total_track_length += edge_length
        return(total_track_length)

    def get_park_in_done_timestamp(self):
        return self.timestamps[TimeStamps.PARK_IN_DONE]
    

    def set_park_in_done_timestamp(self, timestamp):
        self.timestamps[TimeStamps.PARK_IN_DONE] = timestamp

    def set_state(self, state: VehicleState):
        self.state = state

    def set_vehicle_id(self, vid):
        self.vehicle_id = vid

    def set_max_distance(self, max_distance):
        self.max_distance = max_distance

    def set_price_observations(self, price_observations: list):
        self.price_observations = price_observations

    def set_distance_observations(self, distance_observations: list):
        self.distance_observations = distance_observations


    def add_observations(self, distances: list[int], prices: list[int]):
        self.price_observations += prices
        self.distance_observations += distances

    def add_observed_edge(self, edge: ObservedEdge):
        if len(self.observed_edges) > self.observation_window_size:
            self.observed_edges.pop(0)
        
        self.observed_edges.append(edge)

    def add_visited_edge(self, edge: str):
        self.visited_edges.append(edge)
    
    def is_on_new_edge(self, edge):
        if edge != self.recent_edge:
            return True
        else:
            return False
        
    def update_edge_status(self, edge):
        self.recent_edge = edge
    
    def add_timestamp(self, key, value):
        if self.timestamps[key] == None:
            self.timestamps[key] = value
        else:
            pass
        
    def add_vehicle_marker(self):    
        seed = random.randint(0,100)
        traci.poi.add(color=(0,160,0,255), x=self.target_position[0], y=self.target_position[1], poiID=self.vehicle_id + str(seed), 
                        poiType="marker", width=5, height=5, layer=10)

        traci.poi.add(color=(200,160,255,255), x=self.target_position[0], y=self.target_position[1], poiID=self.vehicle_id + str(seed) + "_radius", 
                        poiType="marker", width=int(self.search_radius*2), height=int(self.search_radius*2))




# TODO: fix try catch timestampts