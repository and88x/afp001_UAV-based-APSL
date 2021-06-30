"""Run the simulation"""
from quadcopter import Vehicle

parameters1 = {"id": 1, "lat": 25.645656, "lon": -100.288479}
parameters2 = {"id": 2, "lat": 25.645660, "lon": -100.288479}

with Vehicle(**parameters1) as Vehicle1, Vehicle(**parameters2) as Vehicle2:  # type: ignore
    Vehicle1.set_home()
    Vehicle1.change_mode("GUIDED")
    Vehicle1.takeoff(height=4)

    Vehicle2.set_home()
    Vehicle2.change_mode("GUIDED")
    Vehicle2.takeoff(height=4)
