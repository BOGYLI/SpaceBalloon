"""
Read data from spectral sensor

CSV format:
timestamp, temp, violet, blue, green, yellow, orange, red
"""

import time
import utils
from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_as726x import AS726x_I2C


# Initialize logger
logger = utils.init_logger("spectral")


def main():

    i2c = I2C(8)
    sensor = AS726x_I2C(i2c)

    sensor.conversion_mode = sensor.MODE_2

    while True:

        # Wait for data to be ready
        while not sensor.data_ready:
            time.sleep(0.1)

        # Read temperature in Celsius
        temp = sensor.temperature

        # Read spectral data in μW/cm² and convert to mW/cm²
        violet = sensor.violet / 1000
        blue = sensor.blue / 1000
        green = sensor.green / 1000
        yellow = sensor.yellow / 1000
        orange = sensor.orange / 1000
        red = sensor.red / 1000

        logger.info(f"Temperature: {temp}°C, Violet: {violet:.3f}mW/cm², Blue: {blue:.3f}mW/cm², Green: {green:.3f}mW/cm², Yellow: {yellow:.3f}mW/cm², Orange: {orange:.3f}mW/cm², Red: {red:.3f}mW/cm²")
        utils.write_csv("spectral", [temp, violet, blue, green, yellow, orange, red])
        utils.send_data("spectral", {"temp": temp, "violet": violet, "blue": blue, "green": green, "yellow": yellow, "orange": orange, "red": red}, logger)

        time.sleep(utils.get_interval("spectral"))


if __name__ == "__main__":

    main()
