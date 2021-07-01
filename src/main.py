"""Run the simulation"""
from quadcopter import Vehicle
from cellmap import CellMap
from pollutant import PollutantDistribution
from parameters import *

# Create the probability map
reference_map = CellMap(**CELL_PARAMETERS)

# Instance the plume
plume_location = reference_map.cell2gps(X0_Y0_PLUME_COORD)
plume  = PollutantDistribution(*plume_location)

# Simulation zone of the plume
lower_x, lower_y = li_map.gps2cell((plume.l_lat, plume.l_lon))
upper_x, upper_y = li_map.gps2cell((plume.u_lat, plume.u_lon))
#
lat1, lon1 = li_map.cell2gps(INITIAL_DRONE1_LOCATION)
lat2, lon2 = li_map.cell2gps(INITIAL_DRONE2_LOCATION)
#
drone_parameters_1 = {"id": 1, "lat": lat1, "lon": lon1}
drone_parameters_2 = {"id": 2, "lat": lat2, "lon": lon2}

with Vehicle(**drone_parameters_1) as uav1, Vehicle(**drone_parameters_2) as uav2:  # type: ignore
    # uav1.set_home()
    # uav1.change_mode("GUIDED")
    # uav1.takeoff(height=4)
    # uav2.set_home()
    # uav2.change_mode("GUIDED")
    # uav2.takeoff(height=4)

    uav1.ctrl.groundspeed = GROUND_SPEED
    uav2.ctrl.groundspeed = GROUND_SPEED

    print(reference_map.gamma.shape)
    print(plume.dispersion.shape)

