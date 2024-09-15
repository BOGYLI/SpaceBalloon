import os
import shutil
import datetime
from .config import CONFIG


def camera_index(webcam: int) -> int:
    """
    Get the index of the given webcam in the list of configured cameras

    :return: Index of the webcam
    """

    return CONFIG["webcams"][webcam]


def all_cameras() -> list[int]:
    """
    Get the list of all configured cameras

    :return: List of all configured cameras
    """

    return [cam for cam in CONFIG["webcams"].keys()]


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


def new_photo(webcam: int) -> str:
    """
    Get the path for a new photo file for the given webcam

    :param webcam: Webcam id
    :return: Path to the new photo file
    """
    
    if not os.path.exists(f"{CONFIG['storage']['video']['path']}/cam{webcam}"):
        raise FileNotFoundError(f"Video directory cam{webcam} not found! Please initialize it with reset.sh.")

    return os.path.abspath(f"{CONFIG['storage']['video']['path']}/cam{webcam}/photo_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg")


def new_photo_small(webcam: int) -> str:
    """
    Get the path for a new small photo file for the given webcam

    :param webcam: Webcam id
    :return: Path to the new photo file
    """
    
    if not os.path.exists(f"{CONFIG['storage']['video']['path']}/cam{webcam}"):
        raise FileNotFoundError(f"Video directory cam{webcam} not found! Please initialize it with reset.sh.")

    return os.path.abspath(f"{CONFIG['storage']['video']['path']}/cam{webcam}/photo_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-small.jpg")


def photo_remote(webcam: int) -> (str):
    """
    Get the path for remote photo files for the given webcam

    :param webcam: Webcam id
    :return: Path to the remote photo directory
    """
    
    return f"{CONFIG['storage']['remote']}/cam{webcam}"
