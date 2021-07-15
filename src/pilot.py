"""To set the strategy"""
from abc import ABCMeta, abstractmethod
from typing import Tuple, Type
from random import randint
from quadcopter import Vehicle
from parameters import GROUND_SPEED
from numpy.random import rand, randint
from numpy.linalg import norm
from numpy import spacing, clip, array, append, empty
from dronekit import LocationGlobalRelative
from utils import (
    bearing_to_current_waypoint,
    distance_to_current_waypoint,
    add_up_angles,
    condition_yaw,
    set_velocity_body,
    saturate,
    get_distance_metres,
)

Map_Point = Tuple[int, int]


class Pilot(metaclass=ABCMeta):
    """Abstract class to move a quadcopter"""

    fitness = [-float("inf")]
    fitness_position = [[50, 50]]

    def __init__(self, vehicle: Type[Vehicle], rank: str):
        self.vehicle = vehicle
        self.destination_on_the_map = None
        self.gps_destination = [25.645656, -100.288479]
        self.rank = rank
        self.position_on_the_map = None
        self.previous_positions = empty((0, 2))

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

    @abstractmethod
    def set_gps_destination(self, gps_point) -> None:
        pass

    def update_position(self, position: Map_Point) -> None:
        self.position_on_the_map = position
        self.previous_positions = append(
            self.previous_positions, array([position]), axis=0
        )

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

    def __init__(self, vehicle: Type[Vehicle], rank: str = "folower"):
        super(Strategy2, self).__init__(vehicle, rank)
        self.direction = -1
        self.radius = 5
        self.max_lat_speed = 4
        self.proportional_error_k = 0.2

    def set_gps_destination(self, gps_point) -> None:
        self.gps_destination = gps_point

    def exploration_destination(self, **kwargs) -> Map_Point:
        aux_h, aux_l = kwargs["limits"]
        return (
            randint(aux_h // 5, 4 * aux_h // 5),
            randint(aux_l // 5, 4 * aux_l // 5),
        )

    def exploitation_destination(self, **kwargs) -> Map_Point:
        if self.rank == "leader":
            # return tuple(self.fitness_position)
            return (self.fitness_position[0][0], self.fitness_position[0][1])
        elif self.rank == "folower":
            return kwargs["leader_position"]
        return (-1, -1)

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


class Strategy4(Pilot):
    """docstring for Strategy4"""

    def __init__(self, vehicle: Type[Vehicle], rank: str = "folower"):
        super(Strategy4, self).__init__(vehicle, rank)
        self.target_distance = 10000.0
        self.vehicle.groundspeed = GROUND_SPEED

    def set_gps_destination(self, gps_point) -> None:
        if self.gps_destination != gps_point:
            self.gps_destination = gps_point
            current_location = self.vehicle.ctrl.location.global_relative_frame
            self.target_distance = get_distance_metres(
                current_location, gps_point
            )

    def go_to_destination(self) -> None:
        current_location = self.vehicle.ctrl.location.global_relative_frame
        # lat, lon = self.gps_destination
        target_location = LocationGlobalRelative(
            *self.gps_destination, self.vehicle.alt
        )
        #
        target_location.lat = (
            3 * target_location.lat - 2 * current_location.lat
        )
        target_location.lon = (
            3 * target_location.lon - 2 * current_location.lon
        )
        #
        self.vehicle.ctrl.simple_goto(target_location)

    def exploration_destination(self, **kwargs) -> Map_Point:
        current_location = self.vehicle.ctrl.location.global_relative_frame
        remaining_dist = get_distance_metres(
            current_location, self.gps_destination
        )
        #
        if remaining_dist <= self.target_distance * 0.3:
            limit = kwargs["limits"]
            new_lower_limit = limit[0] // 2 * (self.vehicle.id - 1)
            new_upper_limit = limit[0] // 2 + new_lower_limit + 1
            # print(f"new_lower_limit {self.vehicle.id} = ",new_lower_limit)
            #
            step = 12
            rand_num = 2 * rand(1, 2) - 1
            next_position = self.position_on_the_map + rand_num * step / (
                spacing(0) + norm(rand_num)
            )
            next_position = next_position[0]

            if next_position[0] < new_lower_limit:
                next_position[0] = 2 * new_lower_limit - next_position[0]

            if next_position[0] > new_upper_limit:
                next_position[0] = 2 * new_upper_limit - next_position[0]

            next_position = clip(
                next_position,
                [new_lower_limit, 0],
                [new_upper_limit, limit[1]],
            )
            return (int(next_position[0]), int(next_position[1]))
        return self.destination_on_the_map

    def exploitation_destination(self, **kwargs) -> Map_Point:
        current_location = self.vehicle.ctrl.location.global_relative_frame
        remaining_dist = get_distance_metres(
            current_location, self.gps_destination
        )
        #
        if remaining_dist <= self.target_distance * 0.3:
            step = 6
            new_lower_limit = [
                self.fitness_position[0][0] - step,
                self.fitness_position[0][1] - step,
            ]
            new_upper_limit = [
                self.fitness_position[0][0] + step,
                self.fitness_position[0][1] + step,
            ]
            #
            if kwargs["measure"] > self.fitness[0]:
                rand_num = (
                    2 * array(self.position_on_the_map)
                    - self.previous_positions[-2, 0]
                )
            else:
                rand_num = 2 * rand(1, 2) - 1

            next_position = self.position_on_the_map + rand_num * step / (
                spacing(0) + norm(rand_num)
            )
            next_position = next_position[0]

            if next_position[0] < new_lower_limit[0]:
                next_position[0] = 2 * new_lower_limit[0] - next_position[0]

            if next_position[0] > new_upper_limit[0]:
                next_position[0] = 2 * new_upper_limit[0] - next_position[0]

            if next_position[1] < new_lower_limit[1]:
                next_position[1] = 2 * new_lower_limit[1] - next_position[1]

            if next_position[1] > new_upper_limit[1]:
                next_position[1] = 2 * new_upper_limit[1] - next_position[1]

            next_position = clip(
                next_position, new_lower_limit, new_upper_limit
            )
            next_position = clip(next_position, 0, kwargs["limits"])

            return (int(next_position[0]), int(next_position[1]))

        return self.destination_on_the_map
