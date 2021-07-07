"""To set the strategy"""
from abc import ABCMeta, abstractmethod
from typing import Tuple, Type
from random import randint
from quadcopter import Vehicle
from parameters import GROUND_SPEED
from utils import (
    bearing_to_current_waypoint,
    distance_to_current_waypoint,
    add_up_angles,
    condition_yaw,
    set_velocity_body,
    saturate,
)

Map_Point = Tuple[int, int]


class Pilot(metaclass=ABCMeta):
    """Abstract class to move a quadcopter"""

    fitness = [-float("inf")]
    fitness_position = [50, 50]

    def __init__(self, vehicle:Type[Vehicle], rank:str):
        self.vehicle = vehicle
        self.destination_on_the_map = None
        self.gps_destination = None
        self.rank = rank

    def select_map_destination(self, **kwargs) -> None:
        """Select the next point according the stage of the simulation"""
        if self.vehicle.stage == "exploration":
            self.destination_on_the_map = self.exploration_destination(
                **kwargs
            )
        elif self.vehicle.stage == "exploitation":
            self.destination_on_the_map = self.exploitation_destination(
                **kwargs
            )

    def set_gps_destination(self, gps_point) -> None:
        self.gps_destination = gps_point

    @abstractmethod
    def go_to_destination(self) -> None:
        pass

    @abstractmethod
    def exploration_destination(self, **kwargs) -> Map_Point:
        pass

    @abstractmethod
    def exploitation_destination(self, **kwargs) -> Map_Point:
        pass


class Strategy2(Pilot):
    """Class that states how the strategy select the movement behavior and the destination"""

    def __init__(self, vehicle:Type[Vehicle], rank:str="folower"):
        super(Strategy2, self).__init__(vehicle, rank)
        self.direction = -1
        self.radius = 5
        self.max_lat_speed = 4
        self.proportional_error_k = 0.2

    def exploration_destination(self, **kwargs) -> Map_Point:
        aux_h, aux_l = kwargs["limits"]
        return (
            randint(aux_h // 5, 4 * aux_h // 5),
            randint(aux_l // 5, 4 * aux_l // 5),
        )

    def exploitation_destination(self, **kwargs) -> Map_Point: 
        if self.rank == "leader":
            return tuple(self.fitness_position)
        elif self.rank == "folower":
            return kwargs["leader_position"]
        return None

    def go_to_destination(self) -> None:
        lat, lon = self.gps_destination
        alt = self.vehicle.alt
        #
        bearing = bearing_to_current_waypoint(self.vehicle.ctrl, lat, lon, alt)
        remaining_distance = distance_to_current_waypoint(
            self.vehicle.ctrl, lat, lon, alt
        )
        heading = add_up_angles(bearing, -self.direction * 0.5 * 3.14)
        condition_yaw(self.vehicle.ctrl, heading * 180 / 3.14)
        #
        v_x = GROUND_SPEED
        v_y = (
            -self.direction
            * self.proportional_error_k
            * (self.radius - remaining_distance)
        )
        v_y = saturate(v_y, -self.max_lat_speed, self.max_lat_speed)
        #
        set_velocity_body(self.vehicle.ctrl, v_x, v_y, 0.0)
