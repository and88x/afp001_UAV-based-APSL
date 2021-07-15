"""Represents the pollutan plume"""
from random import random
from numpy import load as load_data
from utils import get_location_meters, split_gps, saturate
from parameters import INITIAL_TIME_4_PLUME


class PollutantDistribution:
    """Distribution of pollutats in a 400x10x10 m^3 volume"""

    def __init__(self, lat: float, lon: float):
        file_path = "databases/plume_dispersion_real_wind.npy"
        coord_00 = (lat, lon)
        self.dispersion = load_data(file_path)
        x_dim, y_dim, _, _ = self.dispersion.shape
        self.l_lat, self.l_lon = coord_00
        self.u_lat, self.u_lon = get_location_meters(coord_00, (y_dim, x_dim))

    def measure_pollutant(self, position, height=5, time=0):
        """Returns a sample from the simulated plume if the position is into
        the plume simulation boundaries
        """
        lat, lon = split_gps(position)
        if (self.l_lon < lon < self.u_lon) and (self.l_lat < lat < self.u_lat):
            #
            disx = lat - self.l_lat
            disy = lon - self.l_lon
            #
            l_1, l_2, _, _ = self.dispersion.shape
            #
            x_index = int((disx * 3.14 / 180) * 6378137) - 1
            y_index = int((disy * 3.14 / 180) * 6378137) - 1
            x_index = saturate(x_index, 0, l_2 - 1)
            y_index = saturate(y_index, 0, l_1 - 1)
            #
            return self.dispersion[y_index, x_index, height, time]
        return random() * 0.009

    #


if __name__ == "__main__":
    plume = PollutantDistribution(lat=25.645656, lon=-100.288479)
    print(plume.dispersion.shape)
