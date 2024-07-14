"""
Read data from CO2 sensor

CSV format:
timestamp, co2, voc
"""

import time
import utils
import smbus2
from sgp30 import SGP30


# Initialize logger
logger = utils.init_logger("co2")


def main():

    bus = smbus2.SMBus(utils.get_bus("co2"))
    sgp30 = SGP30(bus, smbus2.i2c_msg)

    sgp30.start_measurement(lambda: None)

    while True:

        result = sgp30.get_air_quality()

        logger.info(f"CO2: {result.equivalent_co2}ppm, VOC: {result.total_voc}ppb")
        utils.write_csv("co2", [result.equivalent_co2, result.total_voc])
        utils.send_data("co2", {"co2": result.equivalent_co2, "voc": result.total_voc}, logger)

        time.sleep(utils.get_interval("co2"))


if __name__ == "__main__":

    main()
