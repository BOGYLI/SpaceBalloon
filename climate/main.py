"""
Read data from climate sensor

CSV format:
timestamp, pressure, temp, humidity, altitude
"""

import time
import utils
import board
from adafruit_ms8607 import MS8607

# Define the function to calculate altitude based on pressure
def calculate_altitude(pressure, sea_level_pressure=101325, temperature=288.15, lapse_rate=0.0065, gas_constant=8.31447, gravity=9.80665, molar_mass=0.0289644):
    try:
        # Calculate the altitude using the barometric formula
        altitude = (temperature / lapse_rate) * (1 - (pressure / sea_level_pressure) ** (gas_constant * lapse_rate / (gravity * molar_mass)))
        return altitude
    except ZeroDivisionError:
        return "Error: Division by zero occurred. Check the input values."

# Initialize logger
logger = utils.init_logger("climate")

def main():
    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = MS8607(i2c)

    while True:
        # Read sensor data
        pressure_hpa = sensor.pressure  # Pressure in hPa
        temp = sensor.temperature  # Temperature in °C
        humidity = sensor.relative_humidity  # Humidity in rH

        # Convert pressure from hPa to Pa for altitude calculation
        pressure_pa = pressure_hpa * 100

        # Calculate altitude
        altitude = calculate_altitude(pressure_pa)

        # Log the sensor data and calculated altitude
        logger.info(f"Pressure: {pressure_hpa:.3f}hPa, Temperature: {temp:.3f}°C, Humidity: {humidity:.3f}rH, Estimated Altitude: {altitude:.3f}m")

        # Write data to CSV file
        utils.write_csv("climate", [pressure_hpa, temp, humidity, altitude])
        
        # Send data to the server or other destinations
        utils.send_data("climate", {"pressure": pressure_hpa, "temp": temp, "humidity": humidity, "altitude": altitude}, logger)

        # Wait before taking the next reading
        time.sleep(utils.get_interval("climate"))

if __name__ == "__main__":
    main()
