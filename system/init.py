"""
Initialize data storage
"""

import utils
import psutil


if __name__ == "__main__":

    disks = [partition.device for partition in psutil.disk_partitions()]

    utils.init_csv("system", ["cpu", "memory", "temp", "sent", "received", *disks])
