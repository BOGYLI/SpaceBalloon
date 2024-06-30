import os
import time
from .config import CONFIG


def init_csv(name: str, columns: list[str]) -> None:
    """
    Initialize a CSV file with the given name and columns
    
    :param name: Name of the CSV file
    :param columns: List of column names
    """
    
    for path in CONFIG["paths"]["sensor"]:
        if not os.path.exists(path):
            os.makedirs(path)
        with open(f"{path}/{name}.csv", 'w') as file:
            file.write(f"timestamp,{",".join(columns)}\n")


def write_csv(name: str, data: list) -> None:
    """
    Write a row of data to a CSV file with the given name

    :param name: Name of the CSV file
    :param data: List of data to write
    """
    
    for path in CONFIG["paths"]["sensor"]:
        with open(f"{path}/{name}.csv", 'a') as file:
            file.write(f"{time.time():.2f},{",".join([str(value) for value in data])}\n")
