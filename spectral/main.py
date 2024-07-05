"""
Read data from spectral sensor

CSV format:
timestamp, temp, violet, blue, green, yellow, orange, red
"""

import time
import utils
import board
from adafruit_as726x import AS726x_I2C


# Initialize logger
logger = utils.init_logger("spectral")


def main():

    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = AS726x_I2C(i2c)

    sensor.conversion_mode = sensor.MODE_2

    while True:

        # Wait for data to be ready
        while not sensor.data_ready:
            time.sleep(0.1)

        temp = sensor.temperature
        violet = sensor.violet
        blue = sensor.blue
        green = sensor.green
        yellow = sensor.yellow
        orange = sensor.orange
        red = sensor.red

        logger.info(f"Temperature: {temp}°C, Violet: {violet:.1f}, Blue: {blue:.1f}, Green: {green:.1f}, Yellow: {yellow:.1f}, Orange: {orange:.1f}, Red: {red:.1f}")
        utils.write_csv("spectral", [temp, violet, blue, green, yellow, orange, red])

        time.sleep(utils.get_interval("spectral"))


if __name__ == "__main__":

    main()
