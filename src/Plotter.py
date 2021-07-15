from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import use

use("WXAgg")  # set the backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation

plt.rcParams["animation.ffmpeg_path"] = "C:/FFmpeg/bin/ffmpeg.exe"
#


class Plotter:
    """Plot the needed graphs"""

    def __init__(self) -> None:
        self.plt = plt
        self.fig = self.plt.figure(figsize=(6, 6))
        left, bottom, width, height = 0.1, 0.1, 0.8, 0.8
        self.ax = self.fig.add_axes([left, bottom, width, height])
        #
        div = make_axes_locatable(self.ax)
        self.cax = div.append_axes("right", size="5%", pad="5%")
        #
        self.fig.canvas.manager.window.SetPosition((700, 50))
        self.cont = 0

    def plot(self, **kwargs):
        """Docstring"""
        self.ax.clear()
        cp = self.ax.contourf(kwargs["map"].measures[0], cmap="Reds")

        # pl = self.ax.contour(kwargs["map"].measures[0], cmap="Reds")

        self.cax.cla()
        cb = self.fig.colorbar(cp, cax=self.cax)
        self.cax.set_title("$\gamma_{prob}$")
        self.ax.plot(*kwargs["UAV_1"].position_on_the_map, "Xg", markersize=8)
        self.ax.plot(*kwargs["UAV_2"].position_on_the_map, "Xb", markersize=8)
        self.ax.plot(
            kwargs["UAV_1"].previous_positions[:, 0],
            kwargs["UAV_1"].previous_positions[:, 1],
            "-.g",
        )
        self.ax.plot(
            kwargs["UAV_2"].previous_positions[:, 0],
            kwargs["UAV_2"].previous_positions[:, 1],
            "-.b",
        )
        self.ax.text(
            kwargs["UAV_1"].position_on_the_map[0] + 2,
            kwargs["UAV_1"].position_on_the_map[1],
            1,
            fontsize=7,
            bbox=dict(facecolor="w", alpha=0.6, pad=0.7),
        )
        self.ax.text(
            kwargs["UAV_2"].position_on_the_map[0] + 2,
            kwargs["UAV_2"].position_on_the_map[1],
            2,
            fontsize=7,
            bbox=dict(facecolor="w", alpha=0.6, pad=0.7),
        )
        self.ax.set_xlabel("x [east]")
        self.ax.set_ylabel("y [north]")
        #
        self.ax.plot(
            *kwargs["UAV_1"].destination_on_the_map,
            "*g",
            markersize=7,
            label="$Destiny_{1}$"
        )
        self.ax.plot(
            *kwargs["UAV_2"].destination_on_the_map,
            "*b",
            markersize=7,
            label="$Destiny_{2}$"
        )
        #        leg = self.ax.legend(loc="lower left")
        #        #
        #        self.ax.plot(
        #            kwargs["lower_lon"], kwargs["lower_lat"], "xk", markersize=3
        #        )
        #        #
        #        self.ax.plot(
        #            kwargs["lower_lon"], kwargs["upper_lat"], "xk", markersize=3
        #        )
        #        self.ax.plot(
        #            kwargs["upper_lon"], kwargs["lower_lat"], "xk", markersize=3
        #        )
        #        self.ax.plot(
        #            kwargs["upper_lon"], kwargs["upper_lat"], "xk", markersize=3
        #        )
        self.fig.suptitle(
            "Strategy 4, Time = %i [sec]" % (kwargs["time"]), fontsize=16
        )
