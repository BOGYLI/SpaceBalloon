"""
Initialize data storage
"""

import utils


if __name__ == "__main__":

    utils.init_csv("thermal", ["min", "max", "avg", "median", *[str(i) for i in range(768)]])
