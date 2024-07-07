import os
import shutil
import datetime
from .config import CONFIG


def connected_cameras() -> list[int]:
    """
    Get all connected cameras

    :return: List of connected cameras
    """

    return CONFIG["webcams"]


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
