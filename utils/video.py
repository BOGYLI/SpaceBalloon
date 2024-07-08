import os
import shutil
import datetime
from .config import CONFIG


def camera_index(webcam: int) -> int:
    """
    Get the index of the given webcam in the list of configured cameras

    :return: Index of the webcam
    """

    return CONFIG["webcams"][str(webcam)]


def all_cameras() -> list[int]:
    """
    Get the list of all configured cameras

    :return: List of all configured cameras
    """

    return [int(cam) for cam in CONFIG["webcams"].keys()]


def init_video(webcam: int) -> None:
    """
    Initialize the video directory for the given webcam

    :param webcam: Webcam id
    """
    
    for path in [CONFIG["storage"]["video"]["path"], *CONFIG["storage"]["video"]["backups"]]:
        if os.path.exists(f"{path}/cam{webcam}"):
            shutil.rmtree(f"{path}/cam{webcam}", ignore_errors=True)
        os.makedirs(f"{path}/cam{webcam}")


def new_video(webcam: int) -> str:
    """
    Get the path for a new video file for the given webcam

    :param webcam: Webcam id
    :return: Path to the new video file
    """
    
    if not os.path.exists(f"{CONFIG['storage']['video']['path']}/cam{webcam}"):
        raise FileNotFoundError(f"Video directory cam{webcam} not found! Please initialize it with reset.sh.")

    return os.path.abspath(f"{CONFIG['storage']['video']['path']}/cam{webcam}/video_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4")
