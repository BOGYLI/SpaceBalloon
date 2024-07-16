"""
Backup video files
"""

import time
import shutil
import utils
import os


# Initialize logger
logger = utils.init_logger("backup")


def main():

    while True:
        
        # Copy all video files to backup directories that haven't been touched in the last 5 minutes
        for cam in os.listdir(utils.CONFIG["storage"]["video"]["path"]):
            for video in os.listdir(f"{utils.CONFIG["storage"]["video"]["path"]}/{cam}"):
                if time.time() - os.path.getmtime(f"{utils.CONFIG["storage"]["video"]["path"]}/{cam}/{video}") > 300:
                    for backup in utils.CONFIG["storage"]["video"]["backups"]:
                        if not os.path.exists(f"{backup}/{cam}"):
                            os.makedirs(f"{backup}/{cam}")
                        if not os.path.exists(f"{backup}/{cam}/{video}"):
                            shutil.copy(f"{utils.CONFIG["storage"]["video"]["path"]}/{cam}/{video}", f"{backup}/{cam}/{video}")
                    logger.info(f"Backed up {cam}/{video}")
        time.sleep(60)


if __name__ == "__main__":

    main()
