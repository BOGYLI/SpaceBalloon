"""
Read data from CO2 sensor

CSV format:
timestamp, temp_c, temp_f, temp_k, co2_avg, co2_raw, co2_avg_npc, co2_raw_npc, pressure_mbar, pressure_psi
"""

import time
import utils
import smbus2
from modbus import *


# Initialize logger
logger = utils.init_logger("co2")

# Define the float registers (addresses given in HEX)
FLOAT_REGISTERS = {
    "temp_c": 0x3EA,
    "temp_f": 0x3EC,
    "temp_k": 0x3F0,
    "co2_avg": 0x424,
    "co2_raw": 0x426,
    "co2_avg_npc": 0x428,
    "co2_raw_npc": 0x42A,
    "pressure_mbar": 0x4B0,
    "pressure_psi": 0x4B2,
}

# Sensor’s I²C (Modbus) slave address (unshifted)
DEVICE_ADDRESS = 0x5F

# The CO₂ measuring interval is stored in register 0x1450.
# Scale: 1:10, so 10 seconds → 10 * 10 = 100. Range: 100-36000 (10-3600 seconds)
INTERVAL_SCALED = 100


def main():

    # Open the I²C bus
    with SMBus(utils.get_bus("co2")) as bus:

        print("Setting CO₂ measuring interval to 3 seconds...")
        if modbus_write_register(bus, DEVICE_ADDRESS, 0x1450, INTERVAL_SCALED):
            print("  Measuring interval set successfully.")
        else:
            print("  Error setting measuring interval.")

        print("\nStarting continuous sensor readout\n")
        try:

            while True:

                data = {}
                data_list = []

                for name, reg_addr in FLOAT_REGISTERS.items():
                    # Each float is stored in 2 registers (4 bytes total)
                    regs = modbus_read_registers(bus, DEVICE_ADDRESS, reg_addr, 2)
                    if regs is None:
                        data[name] = -100  # Error reading
                        data_list.append(-100)  # Error reading
                    else:
                        try:
                            value = registers_to_float(regs)
                            data[name] = value
                            data_list.append(value)
                        except Exception as e:
                            data[name] = -110  # Error decoding
                            data_list.append(-110)  # Error decoding

                logger.info(f"Temp: {data['temp_c']:.2f}°C {data['temp_f']:.2f}°F {data['temp_k']:.2f}K, " +
                            f"CO2: {int(data['co2_avg'])}ppm {int(data['co2_raw'])}ppm, CO2 NPC: {int(data['co2_avg_npc'])}ppm {int(data['co2_raw_npc'])}ppm, " +
                            f"Pressure: {data['pressure_mbar']:.1f}mbar {data['pressure_psi']:.1f}psi")
                utils.write_csv("co2", data_list)
                utils.send_data("co2", data, logger)

                time.sleep(utils.get_interval("co2"))

        except KeyboardInterrupt:
            print("\nExiting continuous readout.")


if __name__ == "__main__":

    main()
