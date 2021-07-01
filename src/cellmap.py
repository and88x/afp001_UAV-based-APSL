from numpy import (
    load as load_data,
    around,
    linspace,
    ones,
    zeros,
    sum,
    ceil,
    where,
    amin,
    sqrt,
)

from threading import Semaphore
from utils import get_location_meters, split_gps, saturate


class CellMap(object):
    """This object represents the likelihood map"""

    def __init__(self, **kwarg):
        self.n_x = kwarg["cells_in_x"]
        self.n_y = kwarg["cells_in_y"]
        x0 = kwarg["initial_cell_x"]
        y0 = kwarg["initial_cell_y"]
        map_width = kwarg["map_width_in_mtrs"]
        map_long = kwarg["map_long_in_mtrs"]
        home_GPS = kwarg["initial_coordinate"]
        #
        self.Lx = float(map_width) / self.n_x
        self.Ly = float(map_long) / self.n_y
        #
        dis2lim4 = (self.n_x - x0 - 0.5) * self.Lx
        dis2lim3 = (self.n_y - y0 - 0.5) * self.Ly
        dis2lim2 = (x0 + 0.5) * self.Lx
        dis2lim1 = (y0 + 0.5) * self.Ly
        #
        limit3, limit4 = get_location_meters(home_GPS, (dis2lim3, dis2lim4))
        limit1, limit2 = get_location_meters(home_GPS, (-dis2lim1, -dis2lim2))
        y_lat = linspace(limit1, limit3, self.n_y + 1)
        x_lon = linspace(limit2, limit4, self.n_x + 1)
        #
        x_with = abs(x_lon[1] - x_lon[0])
        y_long = abs(y_lat[1] - y_lat[0])
        self.x_lon = around(x_lon[:-1] + x_with / 2, 6)
        self.y_lat = around(y_lat[:-1] + y_long / 2, 6)
        #
        self.t0 = 0
        wind_x = load_data("databases/wind_x.npy")
        wind_y = load_data("databases/wind_y.npy")
        self.wind = sqrt(wind_x * wind_x + wind_y * wind_y)
        #
        self.S_tl_tk = ones((self.n_x, self.n_y)) / (self.n_x * self.n_y)
        self.S_accum = zeros((self.n_x, self.n_y))
        self.gamma = ones((self.n_x, self.n_y)) / (self.n_x * self.n_y)
        #
        self.medidas = [
            zeros((self.n_x, self.n_y)),
            zeros((self.n_x, self.n_y)),
            zeros((self.n_x, self.n_y)),
            zeros((self.n_x, self.n_y)),
        ]
        self.beta = self.S_accum
        self.V = 0
        #
        self.semaphore = Semaphore(1)

    def set_sample(
        self, x_index: int, y_index: int, value: float, index: int = 0
    ):
        """Set the measured value in the corresponding cell"""
        self.measures[index][x_index, y_index] = value

    def update(self, xj: int, yj: int, tk: int, detection: bool = False):
        """Build the source probability map based on one detection or
        nondetection event at time tk"""

        self.semaphore.acquire()
        memory = 7
        if tk - self.t0 > memory:
            t0 = tk - memory
        else:
            t0 = 0
        #
        vx = sum(self.wind[t0:tk, 0])
        vy = 0
        sx = 0.35
        sy = 0.35
        mu = 0.95
        #
        wix = ceil(5 * sqrt(memory) * sx)
        wiy = ceil(5 * sqrt(memory) * sy)
        #
        M = self.Lx * self.Ly
        #
        # From the article:
        for xi in xrange(0, self.n_x):
            for yi in xrange(0, self.n_y):
                if abs(xj - xi - vx) < wix and abs(yj - yi - vy) < wiy:
                    #
                    self.S_tl_tk[xi, yi] = M * (
                        (
                            exp(
                                -((xj - xi - vx) ** 2)
                                / (2 * (memory) * sx ** 2)
                            )
                            * exp(
                                -((yj - yi - vy) ** 2)
                                / (2 * (memory) * sy ** 2)
                            )
                        )
                        / (2 * pi * (tk - self.t0) * sx * sy)
                    )
                else:
                    self.S_tl_tk[xi, yi] = 0

        #
        self.S_tl_tk = self.S_tl_tk / sum(self.S_tl_tk)
        #
        if detection:
            self.S_accum = self.S_accum + self.S_tl_tk
            self.beta = self.S_accum / tk
            self.beta = self.beta / sum(self.beta)
        else:
            self.gamma = self.gamma * (1 - mu * self.S_tl_tk)
            self.gamma = self.gamma / sum(self.gamma)
        #
        self.semaphore.release()
        #

    def gps2cell(self, location):
        """Returns the `location` equivalent indices on the likelihood map"""

        lat, lon = split_gps(location)
        diff_y_lat = abs(self.y_lat - lat)
        diff_x_lon = abs(self.x_lon - lon)
        min_x_lon = where(diff_x_lon == amin(diff_x_lon))[0]
        min_y_lat = where(diff_y_lat == amin(diff_y_lat))[0]
        #
        if type(min_x_lon).__name__ == "ndarray":
            if type(min_y_lat).__name__ == "ndarray":
                a = saturate(min_x_lon[0], 0, 99)
                b = saturate(min_y_lat[0], 0, 99)
            else:
                a = saturate(min_x_lon[0], 0, 99)
                b = saturate(min_y_lat, 0, 99)
        elif type(min_y_lat).__name__ == "ndarray":
            a = saturate(min_x_lon, 0, 99)
            b = saturate(min_y_lat[0], 0, 99)
        else:
            a = saturate(min_x_lon, 0, 99)
            b = saturate(min_y_lat, 0, 99)
        return array([a, b])

    #

    def cell2gps(self, i, dtype="cell_indices"):
        """Returns the global position of grid center"""

        if dtype == "cell_indices":
            if len(i) == 2:
                return [
                    self.y_lat[int(i[1])],
                    self.x_lon[int(i[0])],
                ]
            else:
                print("The indices length must be 2")
        elif dtype == "x_index":
            return self.x_lon[int(i)]
        elif dtype == "y_index":
            return self.y_lat[int(i)]
        else:
            print(
                "The `dtype` argument must be: cell_indices, x_index or y_index."
            )


if __name__ == "__main__":
    cell_parameters = {
        "cells_in_x": 100,
        "cells_in_y": 100,
        "initial_cell_x": 15,
        "initial_cell_y": 15,
        "map_width_in_mtrs": 1000,
        "map_long_in_mtrs": 1000,
        "initial_coordinate": (25.645656, -100.288479),
    }

    li_map = CellMap(**cell_parameters)
    print(li_map.gamma)
