import os
import time
import requests
from .config import CONFIG


def init_csv(name: str, columns: list[str]) -> None:
    """
    Initialize a CSV file with the given name and columns
    
    :param name: Name of the CSV file
    :param columns: List of column names
    """
    
    for storage in CONFIG["storage"]["sensor"].values():
        if not os.path.exists(storage["path"]):
            os.makedirs(storage["path"])
        with open(f"{storage['path']}/{name}.csv", 'w') as file:
            file.write(f"timestamp,{','.join(columns)}\n")


def write_csv(name: str, data: list) -> None:
    """
    Write a row of data to a CSV file with the given name

    :param name: Name of the CSV file
    :param data: List of data to write
    """
    
    for storage in CONFIG["storage"]["sensor"].values():
        if not os.path.exists(f"{storage['path']}/{name}.csv"):
            raise FileNotFoundError(f"CSV file {name}.csv not found! Please initialize it with reset.sh.")
        with open(f"{storage['path']}/{name}.csv", 'a') as file:
            file.write(f"{time.time():.2f},{','.join([str(value) for value in data])}\n")


def send_data(name: str, data: dict) -> None:
    """
    Send data to the data manager
    
    :param name: Name of the sensor
    :param data: Dictionary of data
    """

    requests.post(f"http://localhost:8000/{name}", json=data)


def get_bus(name: str) -> int:
    """
    Get the I2C bus number for the given sensor name

    :param name: Name of the sensor
    :return: I2C bus number
    """

    return CONFIG["bus"][name]


def get_interval(name: str) -> int:
    """
    Get the interval for the given sensor name

    :param name: Name of the sensor
    :return: Interval in seconds
    """

    return CONFIG["interval"][name]
