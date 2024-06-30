"""
Read data from ### sensor

CSV format:
timestamp, ###
"""

import time
import utils


# Initialize logger
logger = utils.init_logger("template")


def demo():
    import random
    while True:
        utils.write_csv("template", [random.randint(0, 100)])
        time.sleep(1)


if __name__ == "__main__":

    demo()
