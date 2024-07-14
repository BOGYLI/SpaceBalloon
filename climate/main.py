"""
Read data from climate sensor

CSV format:
timestamp, pressure, temp, humidity
"""

import time
import utils
import board
from adafruit_ms8607 import MS8607


# Initialize logger
logger = utils.init_logger("climate")


def main():

    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = MS8607(i2c)

    while True:

        pressure = sensor.pressure
        temp = sensor.temperature
        humidity = sensor.relative_humidity

        logger.info(f"Pressure: {pressure}hPa, Temperatur: {temp}°C, Humidity: {humidity}rH")
        utils.write_csv("climate", [pressure, temp, humidity])
        utils.send_data("climate", {"pressure": pressure, "temp": temp, "humidity": humidity}, logger)

        time.sleep(utils.get_interval("climate"))


if __name__ == "__main__":

    main()
