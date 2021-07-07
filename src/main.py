"""Run the simulation"""
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep
from quadcopter import Vehicle
from cellmap import CellMap
from pollutant import PollutantDistribution
from pilot import Strategy2
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
)

aux_position = None
detection = False
#
def take_measure_and_move(auto_piloto) -> None:
    """Both UAVs need to take a measure from the same plume and save it in the map. Afer
    that, they must go towards their destination"""
    #
    global aux_position, STAGE, detection
    #
    gps_location = auto_piloto.vehicle.location()
    map_x, map_y = reference_map.gps2cell(gps_location)
    pollutant = plume.measure_pollutant(gps_location)
    reference_map.set_sample(
        map_x, map_y, pollutant, auto_piloto.vehicle.alt - 3
    )
    #
    aux_position = (map_x, map_y)
    #
    if auto_piloto.fitness[0] < pollutant > POLLUTANT_THRESHOLD:
        STAGE = "exploitation"
        detection = True
        auto_piloto.fitness[0] = pollutant
        auto_piloto.fitness_position = [map_x, map_y]
        print(
            "Pollutan of %.4f detected on [%i,%i] by UAV%i%-40s\n"
            % (pollutant, map_x, map_y, auto_piloto.vehicle.id, " "*40)
        )
    #
    if CURRENT_TIME % 40 == 0 or detection:
        detection = False
        auto_piloto.select_map_destination(
            limits=reference_map.size(), leader_position=aux_position
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
        "location: ({0},{1})  destiny: {2}  fitness = {3:.4f}  fit_pos = {4}".format(
            map_x,
            map_y,
            auto_piloto.destination_on_the_map,
            auto_piloto.fitness[0],
            auto_piloto.fitness_position
        )
    )
    #
    auto_piloto.go_to_destination()


# Create the probability map
reference_map = CellMap(**CELL_PARAMETERS)

# Instance the plume
plume_location = reference_map.cell2gps(X0_Y0_PLUME_COORD)
plume = PollutantDistribution(*plume_location)

# Simulation zone of the plume
lower_x, lower_y = reference_map.gps2cell((plume.l_lat, plume.l_lon))
upper_x, upper_y = reference_map.gps2cell((plume.u_lat, plume.u_lon))
#
lat1, lon1 = reference_map.cell2gps(INITIAL_DRONE1_LOCATION)
lat2, lon2 = reference_map.cell2gps(INITIAL_DRONE2_LOCATION)
#
drone_parameters_1 = {"id": 1, "lat": lat1, "lon": lon1}
drone_parameters_2 = {"id": 2, "lat": lat2, "lon": lon2}
#
with Vehicle(**drone_parameters_1) as uav_1, Vehicle(**drone_parameters_2) as uav_2:  # type: ignore
    #
    pilot_1 = Strategy2(uav_1, rank="leader")
    pilot_2 = Strategy2(uav_2, rank="folower")
    CURRENT_TIME = 0
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

    while CURRENT_TIME < SIMULATION_TIME:
        take_measure_and_move(pilot_1)
        take_measure_and_move(pilot_2)
        print("\033[F\033[F", end="")

        if STAGE == "exploitation":
            pilot_1.vehicle.stage = "exploitation"
            pilot_2.vehicle.stage = "exploitation"

        CURRENT_TIME += 1
        sleep(1)
    print(" ")

    print(reference_map.gamma.shape)
    print(plume.dispersion.shape)
