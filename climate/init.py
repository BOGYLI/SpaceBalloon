"""
Initialize data storage
"""

import utils


if __name__ == "__main__":

    utils.init_csv("climate", ["pressure", "temp", "humidity", "altitude"])
