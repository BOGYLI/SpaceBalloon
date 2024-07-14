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
        disk_names = [partition.device for partition in psutil.disk_partitions()]
        disk_usages = [psutil.disk_usage(partition.mountpoint).percent for partition in psutil.disk_partitions()]

        logger.info(f"CPU: {cpu}%, Memory: {memory}%, Temp: {temp}°C, Sent: {sent} bytes, Received: {received} bytes, Disk: {disk_usages}")
        utils.write_csv("system", [cpu, memory, temp, sent, received, *disk_usages])
        api_data = {"cpu": cpu, "memory": memory, "temp": temp, "sent": sent, "received": received, "disk": {}}
        for disk_name, disk_usage in zip(disk_names, disk_usages):
            api_data["disk"][disk_name] = disk_usage
        utils.send_data("system", api_data, logger)

        time.sleep(utils.get_interval("system"))


if __name__ == "__main__":

    main()
