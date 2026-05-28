## About this Project
This repository contains a simulation-based evaluation of urban parking search behavior conducted as part of a student research project. It analyzes how parameters such as parking duration, occupancy, and search radius affect search time, travel distance, and overall traffic dynamics.

## Licenses
This project is licensed under BSD 2-Clause, except for third-party components.
It includes MoSTScenario, which is licensed under the GNU GPL.

## Installation Guide (Linux)

1. Clone the repository: `git clone git@github.com:ndreinhardt/sumo-parking-search-simulation.git`  
2. Move into the directory: `cd sumo-parking-search-simulation`  
3. Create and activate a virtual environment: `python3 -m venv .venv` and `source .venv/bin/activate`  
4. Install dependencies: `pip3 install -r requirements.txt`  
5. Configure the simulation by editing `simconfig.json` (see section "Simulation Parameters")  
6. Run the simulation: `python3 src/main.py` (see section "Additional Arguments" for options)  
7. Results will be saved in `sim_results/`
8. For live data use: `watch cat sim_results/<simulation>/live_info.json`

## Simulation Parameters
#### parking_areas

| Parameter | Default value | Data type | Value range / description |
|----------|--------------|----------|---------------------------|
| parking_area_file_path | parking_areas.json | string | Path to JSON file |
| initial_occupacity_percentage | 10 | integer | 0–100 (%) initial occupancy |
| on_street_capacity_per_100_m | 7 | integer | ≥ 0 (capacity per 100 meters) |
| parking_costs_euro_per_hour.on_street | 2.0 | float | ≥ 0 (€ per hour) |
| parking_costs_euro_per_hour.off_street | 2.0 | float | ≥ 0 (€ per hour) |

#### simulation

| Parameter | Default value | Data type | Value range / description |
|----------|--------------|----------|---------------------------|
| start | 14400 | integer | Simulation start time in seconds (e.g. 0–86400) |
| end | 50400 | integer | Simulation end time in seconds (must be > start) |
| name | "Basissimulation" | string | Simulation name |
| description | "Basissimulation" | string | Simulation description |
| exporter_update_interval_in_seconds | 100 | integer | > 0 (export interval in seconds) |

#### parking_search

| Parameter | Default value | Data type | Value range / description |
|----------|--------------|----------|---------------------------|
| routing_lookahead_depth | 10 | integer | ≥ 0 |
| observation_window_size | 20 | integer | ≥ 0 |
| max_search_radius_in_meters | 1000 | integer | > 0 |
| parking_duration_in_min | 300 | integer | > 0 |
| city_center.pos_x_in_meters | 5332 | float | X coordinate of the city center in meters |
| city_center.pos_y_in_meters | 2081 | float | Y coordinate of the city center in meters |
| city_center.radius_in_meters | 1500 | float | > 0 (city radius in meters) |
| cost_distribution.price | 0.5 | float | 0.0–1.0 (weight factor) |
| cost_distribution.distance | 0.5 | float | 0.0–1.0 (weight factor) |
| expectation.price_in_euro_per_hour | 2.0 | float | ≥ 0 |
| expectation.distance_in_meters | 500 | integer | ≥ 0 |


## Additional Arguments
#### Python CLI Arguments

| Argument | Default value | Data type | Description |
|----------|--------------|----------|-------------|
| --sumo-mode | "gui" | string | Run mode: "cli" or "gui" |
| --sim-config | "simconfig.json" | string | Simulation configuration file |
| --sumo-config | "./MoSTScenario/scenario/most.sumocfg" | string | SUMO configuration file |
| --debug | False | boolean | Enable debug mode to show parking area locations |
| --debug-vehicle | None | string / null | Vehicle ID for debug output filtering |
