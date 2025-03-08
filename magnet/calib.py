"""
Calibrate
"""

import time
import utils
import math
import gy271


def main():

    calib_min = [32767, 32767, 32767]
    calib_max = [-32768, -32768, -32768]

    # Magnetic declination for the approximate location
    # Calculate with https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml?#declination
    # Current value of 3.78 E is based of location: 47.563° N, 9.682° E
    degrees = 3.78
    declination = degrees * (math.pi / 180)

    sensor = gy271.compass(utils.get_bus("magnet"), sens=gy271.SENS_8G, d=declination)

    while True:

        print("Raw", sensor.x, sensor.y, sensor.z)
        calib_min[0] = min(calib_min[0], sensor.x)
        calib_min[1] = min(calib_min[1], sensor.y)
        calib_min[2] = min(calib_min[2], sensor.z)
        calib_max[0] = max(calib_max[0], sensor.x)
        calib_max[1] = max(calib_max[1], sensor.y)
        calib_max[2] = max(calib_max[2], sensor.z)

        print("Raw Gauss", sensor.x / 3000, sensor.y / 3000, sensor.z / 3000)

        print("Calib min", calib_min)
        print("Calib max", calib_max)

        offset = [(calib_max[0] + calib_min[0]) / 2, (calib_max[1] + calib_min[1]) / 2, (calib_max[2] + calib_min[2]) / 2]
        print("Offset", offset)

        corrected = [sensor.x - offset[0], sensor.y - offset[1], sensor.z - offset[2]]
        print("Corrected", corrected)
        print("Corrected Gauss", corrected[0] / 3000, corrected[1] / 3000, corrected[2] / 3000)

        time.sleep(utils.get_interval("magnet"))


if __name__ == "__main__":

    main()
