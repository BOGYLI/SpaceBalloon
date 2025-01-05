import os
import time
import requests
from logging import Logger
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


def send_data(name: str, data: dict, logger: Logger) -> None:
    """
    Send data to the data manager
    
    :param name: Name of the sensor
    :param data: Dictionary of data
    """

    try:
        requests.post(f"http://127.0.0.1:8000/{name}", json=data, timeout=0.5)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send data to data manager: {e}")


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


def get_influx_url() -> str:
    """
    Get the InfluxDB URL

    :return: InfluxDB URL
    """

    return CONFIG["influx"]["url"]


def get_influx_org() -> str:
    """
    Get the InfluxDB organization

    :return: InfluxDB organization
    """

    return CONFIG["influx"]["org"]


def get_influx_bucket() -> str:
    """
    Get the InfluxDB bucket

    :return: InfluxDB bucket
    """

    return CONFIG["influx"]["bucket"]


def get_influx_token() -> str:
    """
    Get the InfluxDB token

    :return: InfluxDB token
    """

    return CONFIG["influx"]["token"]


def get_aprs_device() -> str:
    """
    Get the APRS device name

    :return: APRS device name
    """

    return CONFIG["aprs"]["device"]


def get_aprs_src() -> str:
    """
    Get the APRS source callsign

    :return: APRS source callsign
    """

    return CONFIG["aprs"]["src"]


def get_aprs_dst() -> str:
    """
    Get the APRS destination callsign

    :return: APRS destination callsign
    """

    return CONFIG["aprs"]["dst"]


def get_cooling_fan() -> int:
    """
    Get the GPIO pin for the cooling fan

    :return: GPIO pin
    """

    return CONFIG["cooling"]["fan_pin"]


def get_cooling_min_temp() -> float:
    """
    Get the requirement for the minimum temperature of the thermal camera for the cooling fan

    :return: Minimum temperature
    """

    return CONFIG["cooling"]["min_temp"]


def get_cooling_max_temp() -> float:
    """
    Get the requirement for the maximum temperature of the thermal camera for the cooling fan

    :return: Maximum temperature
    """

    return CONFIG["cooling"]["max_temp"]


def get_cooling_cpu_temp() -> float:
    """
    Get the requirement for the CPU temperature for the cooling fan

    :return: CPU temperature
    """

    return CONFIG["cooling"]["cpu_temp"]
