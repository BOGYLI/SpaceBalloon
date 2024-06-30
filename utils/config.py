import yaml


def load_config() -> dict:
    """
    Load the configuration file
    
    :return: Configuration dictionary
    """

    with open("config.yml", 'r') as file:
        config = yaml.safe_load(file)
    return config


CONFIG = load_config()
