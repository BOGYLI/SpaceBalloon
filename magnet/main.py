"""
Read data from magnetic field sensor

CSV format:
timestamp, temp, heading
"""

import time
import utils
import gy271


# Initialize logger
logger = utils.init_logger("magnet")


def main():

    sensor = gy271.compass(utils.get_bus("magnet"))

    while True:

        angle = sensor.get_bearing()       
        temp = sensor.read_temp()

        logger.info(f"Temperature: {temp}°C, Heading: {angle}°")
        utils.write_csv("magnet", [temp, angle])
        utils.send_data("magnet", {"temp": temp, "heading": angle}, logger)

        time.sleep(utils.get_interval("magnet"))


if __name__ == "__main__":

    main()
