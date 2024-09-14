"""
Initialize data storage
"""

import utils
import psutil


if __name__ == "__main__":

    disk = []
    for partition in psutil.disk_partitions():
        disk.append(f"{partition.device}_total")
        disk.append(f"{partition.device}_used")

    utils.init_csv("system", ["cpu", "memory", "temp", "sent", "received", *disk])
