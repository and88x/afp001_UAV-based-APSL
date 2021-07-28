"""Functions used by various classes"""
from math import cos, pi, atan2, sin, sqrt
from dronekit import LocationGlobalRelative, LocationGlobal
from pymavlink import mavutil
from time import time

def tic():
    #Homemade version of matlab tic and toc functions
    global startTime_for_tictoc
    startTime_for_tictoc = time()

def toc():
    if 'startTime_for_tictoc' in globals():
        val = time() - startTime_for_tictoc
        print("Elapsed time is %f seconds." % val)
        return val
    else:
        print("Toc: start time not set")
        return None

def get_location_meters(original_location, next_position):
    """
    Returns a LocationGlobal object containing the latitude/longitude `d_north`
    and `d_east` metres from the specified `original_location`. The returned
    LocationGlobal has the same `alt` value as `original_location`.
    The function is useful when you want to move the vehicle around specifying
    locations relative to the current vehicle position.
    The algorithm is relatively accurate over small distances (10m within 1km)
    except close to the poles.
    """

    d_north, d_east = next_position

    if isinstance(original_location, (LocationGlobal, LocationGlobalRelative)):
        _lat = original_location.lat
        _long = original_location.lon
    else:
        _lat, _long = original_location

    earth_radius = 6378137.0  # Radius of "spherical" earth
    # Coordinate offsets in radians
    d_at = d_north / earth_radius
    d_lon = d_east / (earth_radius * cos(pi * _lat / 180))

    # New position in decimal degrees
    newlat = round(_lat + (d_at * 180 / pi), 6)
    newlon = round(_long + (d_lon * 180 / pi), 6)

    if isinstance(original_location, LocationGlobal):
        return LocationGlobal(newlat, newlon, original_location.alt)
    if isinstance(original_location, LocationGlobalRelative):
        return LocationGlobalRelative(newlat, newlon, original_location.alt)
    return (newlat, newlon)


def split_gps(a_location):
    """Separates the coordinates of the object in latitude and longitude"""
    if isinstance(a_location, (LocationGlobal, LocationGlobalRelative)):
        _lat1 = a_location.lat
        _long1 = a_location.lon
    else:
        _lat1, _long1 = a_location
    return _lat1, _long1


def saturate(value, minimum, maximum):
    """Limits the value variable"""
    value = min(value, maximum)
    value = max(value, minimum)
    return value


def bearing_to_current_waypoint(vehicle, lat, lon, alt):
    """Turn the vahicle frame towards the destination"""
    target_waypoint_location = LocationGlobalRelative(lat, lon, alt)
    bearing = get_bearing(
        vehicle.location.global_relative_frame, target_waypoint_location
    )
    return bearing


def set_velocity_body(vehicle, v_x, v_y, v_z):
    """Remember: v_z is positive downward!!!
    http://ardupilot.org/dev/docs/copter-commands-in-guided-mode.html

    Bitmask to indicate which dimensions should be ignored by the vehicle
    (a value of 0b0000000000000000 or 0b0000001000000000 indicates that
    none of the setpoint dimensions should be ignored). Mapping:
    bit 1: x,  bit 2: y,  bit 3: z,
    bit 4: v_x, bit 5: v_y, bit 6: v_z,
    bit 7: ax, bit 8: ay, bit 9:
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,
        0,
        0,
        mavutil.mavlink.MAV_FRAME_BODY_NED,
        0b0000111111000111,  # -- BITMASK -> Consider only the velocities
        0,
        0,
        0,  # -- POSITION
        v_x,
        v_y,
        v_z,  # -- VELOCITY
        0,
        0,
        0,  # -- ACCELERATIONS
        0,
        0,
    )
    vehicle.send_mavlink(msg)
    vehicle.flush()


def get_bearing(my_location, tgt_location):
    """
    Aproximation of the bearing for medium latitudes and sort distances
    """
    _lat1, _long1 = split_gps(my_location)
    _lat2, _long2 = split_gps(tgt_location)
    dlat = _lat2 - _lat1
    dlong = _long2 - _long1
    return atan2(dlong, dlat)


def distance_to_current_waypoint(vehicle, lat, lon, alt):
    """
    Gets distance in metres to the current waypoint.
    It returns None for the first waypoint (Home location).
    """
    target_waypoint_location = LocationGlobalRelative(lat, lon, alt)
    distancetopoint = get_distance_metres(
        vehicle.location.global_frame, target_waypoint_location
    )
    return distancetopoint


def get_distance_metres(location_1, location_2):
    """
    Returns the ground distance in metres beteen two LocationGlobal objects.
    This method is an approximation, and will not be accurate over large
    distances and close to the earth's poles.
    """
    earth_radius = 6378137
    _lat1, _long1 = split_gps(location_1)
    _lat2, _long2 = split_gps(location_2)

    dlat = _lat2 - _lat1
    dlong = _long2 - _long1

    aux_a = sin(dlat / 2) ** 2 + cos(_lat1 * pi / 180) * cos(
        _lat1 * pi / 180
    ) * sin(dlong / 2) * sin(dlong / 2)
    aux_c = 2 * atan2(sqrt(aux_a), sqrt(1 - aux_a)) * pi / 180
    return round(earth_radius * aux_c, 2)


def add_up_angles(ang1, ang2):
    """Sum two angles from 0 to 2*pi"""
    ang = ang1 + ang2
    if ang > 2.0 * pi:
        ang -= 2.0 * pi
    elif ang < -0.0:
        ang += 2.0 * pi
    return ang


def condition_yaw(vehicle, heading, relative=False):
    """
    Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).
    This method sets an absolute heading by default, but you can set the `relative` parameter
    to `True` to set yaw relative to the current yaw heading.
    By default the yaw of the vehicle will follow the direction of travel. After setting
    the yaw using this function there is no way to return to the default yaw "follow direction
    of travel" behaviour (https://github.com/diydrones/ardupilot/issues/2427)
    For more information see:
    http://copter.ardupilot.com/wiki/common-mavlink-mission-command-messages-mav_cmd/#mav_cmd_condition_yaw
    """
    if relative:
        is_relative = 1  # yaw relative to direction of travel
    else:
        is_relative = 0  # yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0,
        0,  # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,  # confirmation
        heading,  # param 1, yaw in degrees
        0,  # param 2, yaw speed deg/s
        1,  # param 3, direction -1 ccw, 1 cw
        is_relative,  # param 4, relative offset 1, absolute angle 0
        0,
        0,
        0,
    )  # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)
