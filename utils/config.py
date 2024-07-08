import yaml
import os


VERSION = 7


def load_config() -> dict:
    """
    Load the configuration file
    
    :return: Configuration dictionary
    """

    if not os.path.exists("config.yml"):
        raise FileNotFoundError("Configuration file not found! Please run setup.sh and adjust your settings.")

    with open("config.yml", 'r') as file:
        config = yaml.safe_load(file)

    if config["version"] != VERSION:
        raise Exception("Configuration file version mismatch! Please remove config.yml, run setup.sh and adjust your settings.")

    return config


CONFIG = load_config()
