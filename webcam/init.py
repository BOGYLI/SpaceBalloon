"""
Initialize data storage
"""

import utils


if __name__ == "__main__":

    for webcam in utils.all_cameras():
        utils.init_video(webcam)
