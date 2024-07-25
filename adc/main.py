"""
Read data from analog digital converter

CSV format:
timestamp, uv, methane
"""

import time
import math
import ADS1x15
import utils


# Initialize logger
logger = utils.init_logger("adc")


def mapfloat(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def main():

    ADS = ADS1x15.ADS1115(utils.get_bus("adc"), 0x48)

    ADS.setGain(ADS.PGA_4_096V)
    f = ADS.toVoltage()

    while True:

        uv = ADS.readADC(1) * f
        ref3_3 = ADS.readADC(2) * f

        uv_adjusted = 3.3 / ref3_3 * uv
        uv_intensity = mapfloat(uv_adjusted, 0.99, 2.8, 0.0, 15.0)

        logger.info(f"UV: {uv_intensity:.3f}mW/cm²")

        utils.write_csv("adc", [uv_intensity])
        utils.send_data("adc", {"uv": uv_intensity}, logger)
        time.sleep(utils.get_interval("adc"))


if __name__ == "__main__":

    main()
