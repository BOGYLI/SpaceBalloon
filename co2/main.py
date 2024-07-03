"""
Read data from CO2 sensor

CSV format:
timestamp, co2, voc
"""

import time
import utils
from sgp30 import SGP30


# Initialize logger
logger = utils.init_logger("co2")


def main():

    sgp30 = SGP30()

    sgp30.start_measurement(lambda: None)

    while True:

        result = sgp30.get_air_quality()

        logger.info(f"CO2: {result.equivalent_co2}ppm, VOC: {result.total_voc}ppb")
        utils.write_csv("co2", [result.equivalent_co2, result.total_voc])

        time.sleep(1)


if __name__ == "__main__":

    main()
