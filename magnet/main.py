"""
Read data from magnetic field sensor

CSV format:
timestamp, temp, heading
"""

import time
import utils
import math
import gy271


# Initialize logger
logger = utils.init_logger("magnet")


def main():

    # Magnetic declination for the approximate location
    # Calculate with https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml?#declination
    # Current value of 3.78 E is based of location: 47.563° N, 9.682° E
    degrees = 3.78
    declination = degrees * (math.pi / 180)

    sensor = gy271.compass(utils.get_bus("magnet"), sens=gy271.SENS_8G, d=declination)

    while True:

        angle = sensor.get_bearing()       
        temp = sensor.read_temp()

        logger.info(f"Temperature: {temp:.3f}°C, Heading: {angle}°, X: {sensor.x}, Y: {sensor.y}, Z: {sensor.z}")
        utils.write_csv("magnet", [temp, angle, sensor.x, sensor.y, sensor.z])
        utils.send_data("magnet", {"temp": temp, "heading": angle, "x": sensor.x, "y": sensor.y, "z": sensor.z}, logger)

        time.sleep(utils.get_interval("magnet"))


if __name__ == "__main__":

    main()
