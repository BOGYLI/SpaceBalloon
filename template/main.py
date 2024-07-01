"""
Read data from ### sensor

CSV format:
timestamp, ###
"""

import utils


# Initialize logger
logger = utils.init_logger("template")


# Temporary demonstration #REMOVE
def demo():
    import random
    import time
    while True:
        utils.write_csv("template", [random.randint(0, 100)])
        time.sleep(1)


if __name__ == "__main__":

    demo()
