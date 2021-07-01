from dronekit import LocationGlobalRelative, LocationGlobal
from math import cos, pi


def get_location_meters(original_location, next_position):
    """
    Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the specified `original_location`. The returned LocationGlobal has the same `alt` value as `original_location`.
    The function is useful when you want to move the vehicle around specifying locations relative to the current vehicle position.
    The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.
    """

    dNorth, dEast = next_position

    if (type(original_location) is LocationGlobal) or (
        type(original_location) is LocationGlobalRelative
    ):
        _lat = original_location.lat
        _long = original_location.lon
    else:
        _lat, _long = original_location

    earth_radius = 6378137.0  # Radius of "spherical" earth
    # Coordinate offsets in radians
    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius * cos(pi * _lat / 180))

    # New position in decimal degrees
    newlat = round(_lat + (dLat * 180 / pi), 6)
    newlon = round(_long + (dLon * 180 / pi), 6)

    if type(original_location) is LocationGlobal:
        return LocationGlobal(newlat, newlon, original_location.alt)
    elif type(original_location) is LocationGlobalRelative:
        # return LocationGlobalRelative(
        #    newlat, newlon, original_location.alt)
        return (newlat, newlon)
    else:
        return (newlat, newlon)


def split_gps(aLocation):
    if (type(aLocation) is LocationGlobal) or (
        type(aLocation) is LocationGlobalRelative
    ):
        _lat1 = aLocation.lat
        _long1 = aLocation.lon
    else:
        _lat1, _long1 = aLocation
    return _lat1, _long1


def saturate(value, minimum, maximum):
    if value > maximum:
        value = maximum
    if value < minimum:
        value = minimum
    return value
