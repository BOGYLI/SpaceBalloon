"""
Read data from system

CSV format:
timestamp, cpu, memory, temp, sent, received, disk
"""

import time
import utils
import psutil
import gpiozero


# Initialize logger
logger = utils.init_logger("system")


def main():

    while True:

        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        temp = gpiozero.CPUTemperature().temperature
        sent = psutil.net_io_counters().bytes_sent
        received = psutil.net_io_counters().bytes_recv
        disk = [psutil.disk_usage(partition.mountpoint).percent for partition in psutil.disk_partitions()]

        logger.info(f"CPU: {cpu}%, Memory: {memory}%, Temp: {temp}°C, Sent: {sent} bytes, Received: {received} bytes, Disk: {disk}")
        utils.write_csv("system", [cpu, memory, temp, sent, received, f"'{disk}'"])

        time.sleep(utils.get_interval("system"))


if __name__ == "__main__":

    main()
