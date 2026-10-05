import json

class SimConfig():
    def __init__(self, path, debug):
        self.path = path
        self.debug_mode = debug

    def _check_type(self, key, value, expected_type):
        if not isinstance(value, expected_type):
            raise TypeError(f"SimConfig: key: {key} needs type {expected_type}")

    def load_configuration(self):
        # open simconf.json file and validate
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                config = json.load(f)
                print(f"SimConfig: {self.path} syntax valid.")
        except json.JSONDecodeError as e:
            print(f"SimConfig: JSON-Error in {self.path}")
            print(f"SimConfig: Error in Line {e.lineno}, column {e.colno}")
            print(e)

        # load parameters from simconfig
        try:
            # Parking Areas
            self.parking_area_file_path = config["parking_areas"]["parking_area_file_path"]
            self._check_type("parking_areas->parking_area_file_path",self.parking_area_file_path, str)
            
            self.init_occupacity = config["parking_areas"]["initial_occupacity_percentage"]
            self._check_type("parking_areas->initial_occupacity",self.init_occupacity, int)

            self.on_street_capacity= config["parking_areas"]["on_street_capacity_per_100_m"]
            self._check_type("parking_areas->on_street_capacity_per_100_m",self.on_street_capacity, int)

            self.on_street_parking_costs = config["parking_areas"]["parking_costs_euro_per_hour"]["on_street"]
            self._check_type("parking_areas->parking_costs->on_street",self.on_street_parking_costs, float)

            self.off_street_parking_costs = config["parking_areas"]["parking_costs_euro_per_hour"]["off_street"]
            self._check_type("parking_areas->parking_costs->off_street",self.off_street_parking_costs, float)

            # Simulation
            self.sim_start = config["simulation"]["start"]
            self._check_type("simulation->start",self.sim_start, int)

            self.sim_end = config["simulation"]["end"]
            self._check_type("simulation->end",self.sim_end, int)

            self.sim_name = config["simulation"]["name"]
            self._check_type("simulation->name",self.sim_name, str)

            self.sim_description = config["simulation"]["description"]
            self._check_type("simulation->description",self.sim_description, str)

            self.update_interval = config["simulation"]["exporter_update_interval_in_seconds"]
            self._check_type("simulation->exporter_update_interval_in_seconds",self.update_interval, int)


            # Parking Search
            self.park_in_delay_in_seconds = config["parking_search"]["park_in_delay_in_seconds"]
            self._check_type("parking_search->park_in_delay_in_seconds",self.park_in_delay_in_seconds, int)

            self.cost_distribution_distance_weigth = config["parking_search"]["cost_distribution"]["distance"]
            self._check_type("parking_search->coast_distribution->distance",self.cost_distribution_distance_weigth, float)

            self.cost_distribution_price_weigth = config["parking_search"]["cost_distribution"]["price"]
            self._check_type("parking_search->coast_distribution->price",self.cost_distribution_price_weigth, float)

            self.search_radius = config["parking_search"]["max_search_radius_in_meters"]
            self._check_type("parking_search->max_distance",self.search_radius, int)

            self.parking_duration = config["parking_search"]["parking_duration_in_min"]
            self._check_type("parking_search->parking_duration_in_min",self.parking_duration, int)

            self.routing_lookahead_depth = config["parking_search"]["routing_lookahead_depth"]
            self._check_type("parking_search->routing_lookahead_depth",self.routing_lookahead_depth, int)

            self.observation_window_size = config["parking_search"]["observation_window_size"]
            self._check_type("parking_search->observation_window_size",self.observation_window_size, int)

            self.price_expectation = config["parking_search"]["expectation"]["price_in_euro_per_hour"]
            self._check_type("parking_search->expectation->price",self.price_expectation, float)

            self.distance_expectation = config["parking_search"]["expectation"]["distance_in_meters"]
            self._check_type("parking_search->expectation->distance",self.distance_expectation, int)   

            self.city_center_pos_x = config["parking_search"]["city_center"]["pos_x_in_meters"]
            self._check_type("parking_search->city_center->pos_x_in_meters",self.city_center_pos_x, int)   

            self.city_center_pos_y = config["parking_search"]["city_center"]["pos_y_in_meters"]
            self._check_type("parking_search->city_center->pos_y_in_meters",self.city_center_pos_y, int)   

            self.city_center_radius = config["parking_search"]["city_center"]["radius_in_meters"]
            self._check_type("parking_search->city_center->radius_in_meters",self.city_center_radius, int)   


            print(f"SimConfig: Parameters loaded")
        except KeyError as e:
            print("SimConfig: Error on loading Parameters")
            print(f"SimCOnfig: Please make sure that key: '{e.args[0]}' is set in the simconfig.json")
            exit(False)


    def get_path(self) -> str:
        return self.path

    def get_sim_start(self) -> int:
        return self.sim_start

    def get_sim_end(self) -> int:
        return self.sim_end

    def get_initial_occupacity(self) -> int:
        return self.init_occupacity

    def get_on_street_parking_costs(self) -> float:
        return self.on_street_parking_costs

    def get_off_street_parking_costs(self) -> float:
        return self.off_street_parking_costs

    def get_cost_distribution_price_weigth(self) -> float:
        return self.cost_distribution_price_weigth

    def get_cost_distribution_distance_weigth(self) -> float:
        return self.cost_distribution_distance_weigth

    def get_search_radius(self) -> int:
        return self.search_radius

    def get_price_expectation(self) -> float:
        return self.price_expectation

    def get_distance_expectation(self) -> int:
        return self.distance_expectation

    def get_walking_speed(self) -> float:
        return self.walking_speed
    
    def get_on_street_capacity(self) -> int:
        return self.on_street_capacity
    
    def get_debug_mode(self) -> bool:
        return self.debug_mode
    
    def get_sim_name(self) -> str:
        return self.sim_name
    
    def get_parking_area_file_path(self) -> str:
        return self.parking_area_file_path
    
    def get_routing_lookahead_depth(self) -> int:
        return self.routing_lookahead_depth
    
    def get_city_center(self) -> tuple[int]:
        return(self.city_center_pos_x, 
                self.city_center_pos_y, 
                self.city_center_radius)
    
    def get_update_interval(self):
        return self.update_interval
    
    def get_observation_window_size(self):
        return self.observation_window_size
    
    def get_parking_duration(self):
        return self.parking_duration
    
    def get_sim_description(self):
        return self.sim_description
    
    def get_max_parking_price(self):
        return(max(self.on_street_parking_costs, self.off_street_parking_costs))

    def get_park_in_delay_in_seconds(self):
        return self.park_in_delay_in_seconds