"""Run the simulation"""
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep
from quadcopter import Vehicle
from cellmap import CellMap
from pollutant import PollutantDistribution
from pilot import Strategy4, Strategy2
from Plotter import Plotter
from utils import get_location_meters, get_distance_metres
import csv
from parameters import (
    CELL_PARAMETERS,
    X0_Y0_PLUME_COORD,
    INITIAL_DRONE1_LOCATION,
    INITIAL_DRONE2_LOCATION,
    SIMULATION_TIME,
    HEIGHT_UAV1,
    HEIGHT_UAV2,
    POLLUTANT_THRESHOLD,
    STAGE,
    INITIAL_TIME_4_PLUME,
)

# aux
plume_location = None
source_gps = None

# Summary parameters
first_detection = {
    "value": None,
    "time": None,
    "lat": None,
    "lon": None,
    "alt": None,
    "x": None,
    "y": None,
    "uav": None,
}
best = {
    "value": None,
    "value_time": None,
    "value_lat": None,
    "value_lon": None,
    "value_alt": None,
    "value_x": None,
    "value_y": None,
    "dist2source": None,
}
#
def take_measure_and_move(auto_piloto) -> None:
    """Both UAVs need to take a measure from the same plume and save it in the map. Afer
    that, they must go towards their destination"""
    #
    global STAGE, detection, pos_uavs, first_detection, best
    #
    curt = CURRENT_TIME + INITIAL_TIME_4_PLUME - 1
    gps_location = auto_piloto.vehicle.location()
    map_x, map_y = reference_map.gps2cell(gps_location)
    auto_piloto.update_position((map_x, map_y))
    pollutant = plume.measure_pollutant(
        gps_location, height=auto_piloto.vehicle.alt, time=curt
    )
    reference_map.set_sample(
        map_x, map_y, pollutant, auto_piloto.vehicle.alt - 3
    )
    #
    aux_position = (map_x, map_y)
    #
    if auto_piloto.fitness[0] < pollutant > POLLUTANT_THRESHOLD:
        STAGE = "exploitation"
        auto_piloto.target_distance = 10000
        auto_piloto.fitness[0] = pollutant
        auto_piloto.fitness_position[0] = [map_x, map_y]
        print("")
        #
        best["value"] = pollutant
        best["value_time"] = CURRENT_TIME
        best["value_lat"] = gps_location.lat
        best["value_lon"] = gps_location.lon
        best["value_alt"] = auto_piloto.vehicle.alt
        best["value_x"] = map_x
        best["value_y"] = map_y
        best["dist2source"] = get_distance_metres(
            [gps_location.lat, gps_location.lon], source_gps
        )
        #
        print(
            "fitness  time   lattitude   longitude   alt x   y  distance  UAV"
        )
        print(
            "{0:.4f}   {1}    {2:.6f}  {3:.6f}  {4}  {5}  {6}  {7:.2}   {8}   \n\n".format(
                best["value"],
                best["value_time"],
                best["value_lat"],
                best["value_lon"],
                best["value_alt"],
                best["value_x"],
                best["value_y"],
                best["dist2source"],
                auto_piloto.vehicle.id,
            )
        )
        #
        if not first_detection["value"]:
            first_detection["value"] = pollutant
            first_detection["time"] = CURRENT_TIME
            first_detection["lat"] = gps_location.lat
            first_detection["lon"] = gps_location.lon
            first_detection["alt"] = auto_piloto.vehicle.alt
            first_detection["x"] = map_x
            first_detection["y"] = map_y
            first_detection["uav"] = auto_piloto.vehicle.id
    #
    auto_piloto.select_map_destination(
        limits=reference_map.size(),
        leader_position=aux_position,
        measure=pollutant,
    )
    new_gps_position = reference_map.cell2gps(
        auto_piloto.destination_on_the_map
    )
    auto_piloto.set_gps_destination(gps_point=new_gps_position)
    #
    print(
        "UAV{0}: pollutant = {1:.4f}  time {2}".format(
            auto_piloto.vehicle.id, pollutant, CURRENT_TIME
        ),
        end="  ",
    )
    print(
        "location: ({0},{1})  destiny: {2}  fitness = {3:.4f}  fit_pos = {4}  ".format(
            map_x,
            map_y,
            auto_piloto.destination_on_the_map,
            auto_piloto.fitness[0],
            auto_piloto.fitness_position,
        )
    )
    #
    auto_piloto.go_to_destination()


# Create the probability map
reference_map = CellMap(**CELL_PARAMETERS)

# Instance the plume
plume_location = reference_map.cell2gps(X0_Y0_PLUME_COORD[0])
source_gps = get_location_meters(plume_location, [4, 4])
plume = PollutantDistribution(*plume_location)
#
# Simulation zone of the plume
lower_x, lower_y = reference_map.gps2cell((plume.l_lat, plume.l_lon))
upper_x, upper_y = reference_map.gps2cell((plume.u_lat, plume.u_lon))
#
lat1, lon1 = reference_map.cell2gps(INITIAL_DRONE1_LOCATION)
lat2, lon2 = reference_map.cell2gps(INITIAL_DRONE2_LOCATION)
#
CURRENT_TIME = 0
graph = Plotter()
#
drone_parameters_1 = {"id": 1, "lat": lat1, "lon": lon1}
drone_parameters_2 = {"id": 2, "lat": lat2, "lon": lon2}
#
def show_plume_in_map():
    curt = CURRENT_TIME + INITIAL_TIME_4_PLUME - 1
    for ii in range(0, 100):
        for jj in range(0, 100):
            pos = reference_map.cell2gps((jj, ii), "cell_indices")
            value = plume.measure_pollutant(pos, height=HEIGHT_UAV1, time=curt)
            reference_map.set_sample(ii, jj, value, 0)
            value = plume.measure_pollutant(pos, height=HEIGHT_UAV2, time=curt)
            reference_map.set_sample(ii, jj, value, 1)
            # value = plume.measure_pollutant(pos, height=5, time=curt)
            # reference_map.set_sample(ii, jj, value, 2)


#
with Vehicle(**drone_parameters_1) as uav_1, Vehicle(**drone_parameters_2) as uav_2:  # type: ignore
    pilot_1 = Strategy4(uav_1, rank="leader")
    pilot_2 = Strategy4(uav_2, rank="folower")
    #
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(uav_1.set_home)
        executor.submit(uav_2.set_home)
        #
        executor.submit(uav_1.change_mode, "GUIDED")
        executor.submit(uav_2.change_mode, "GUIDED")
        #
        executor.submit(uav_1.takeoff, height=HEIGHT_UAV1)
        executor.submit(uav_2.takeoff, height=HEIGHT_UAV2)
    #
    while CURRENT_TIME < SIMULATION_TIME:
        show_plume_in_map()
        #
        take_measure_and_move(pilot_1)
        take_measure_and_move(pilot_2)
        print("\033[F\033[F", end="")
        #
        to_graph = {
            "map": reference_map,
            "UAV_1": pilot_1,
            "UAV_2": pilot_2,
            "lower_lon": lower_x,
            "lower_lat": lower_y,
            "upper_lon": upper_x,
            "upper_lat": upper_y,
            "time": CURRENT_TIME,
        }
        graph.plot(**to_graph)
        graph.plt.pause(0.001)
        #
        if STAGE == "exploitation":
            pilot_1.vehicle.stage = "exploitation"
            pilot_2.vehicle.stage = "exploitation"

        CURRENT_TIME += 1
        sleep(1)
        #
        if CURRENT_TIME % 20 == 0:
            graph.fig.savefig("./Strategy4.eps", format="eps", dpi=1200)
#
graph.fig.savefig("./databases/Strategy4.eps", format="eps", dpi=1200)

myFile = open("./databases/Strategy4.csv", "a")
fieldnames = [
    "source_pos_x",
    "source_pos_y",
    "source_lat",
    "source_lon",
    "source_alt",
    "source_released_time",
    "theshold_4_pollutant",
    "termination_time",
    "initial_height_1",
    "initial_height_2",
    "firstDV",
    "firstDT",
    "firstD_lat",
    "firstD_lon",
    "firstD_alt",
    "firstD_x",
    "firstD_y",
    "firstD_uav",
    "best_value",
    "best_value_time",
    "best_value_lat",
    "best_value_lon",
    "best_value_alt",
    "best_value_x",
    "best_value_y",
    "dist_best2source",
]
summary = {
    "source_pos_x": reference_map.gps2cell(source_gps)[0],
    "source_pos_y": reference_map.gps2cell(source_gps)[1],
    "source_lat": source_gps[0],
    "source_lon": source_gps[1],
    "source_alt": 3,
    "source_released_time": INITIAL_TIME_4_PLUME,
    "theshold_4_pollutant": POLLUTANT_THRESHOLD,
    "termination_time": SIMULATION_TIME,
    "initial_height_1": HEIGHT_UAV1,
    "initial_height_2": HEIGHT_UAV2,
    "firstDV": first_detection["value"],
    "firstDT": first_detection["time"],
    "firstD_lat": first_detection["lat"],
    "firstD_lon": first_detection["lon"],
    "firstD_alt": first_detection["alt"],
    "firstD_x": first_detection["x"],
    "firstD_y": first_detection["y"],
    "firstD_uav": first_detection["uav"],
    "best_value": best["value"],
    "best_value_time": best["value_time"],
    "best_value_lat": best["value_lat"],
    "best_value_lon": best["value_lon"],
    "best_value_alt": best["value_alt"],
    "best_value_x": best["value_x"],
    "best_value_y": best["value_y"],
    "dist_best2source": best["dist2source"],
}
with myFile:
    writer = csv.DictWriter(myFile, fieldnames=fieldnames, lineterminator="\n")
    writer.writerow(resumen)

print("************************************************************")
