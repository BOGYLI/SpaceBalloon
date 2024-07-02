import sys
import logging


def init_logger(name: str) -> logging.Logger:
    """
    Initialize a logger with the given name

    :param name: Name of the logger
    :return: Logger object
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] <%(levelname)s> %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(formatter)
    logger.addHandler(stdout)
    return logger
