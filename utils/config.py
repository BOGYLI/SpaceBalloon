import yaml


VERSION = 7


def load_config() -> dict:
    """
    Load the configuration file
    
    :return: Configuration dictionary
    """

    with open("config.yml", 'r') as file:
        config = yaml.safe_load(file)

    if config["version"] != VERSION:
        raise Exception("Configuration file version mismatch! Please remove config.yml, run setup.sh and adjust your settings.")

    return config


CONFIG = load_config()
