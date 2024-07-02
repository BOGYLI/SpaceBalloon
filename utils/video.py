import os
import shutil
import datetime
from .config import CONFIG


def init_video(webcam: int) -> None:
    """
    Initialize the video directory for the given webcam

    :param webcam: Webcam id
    """
    
    for storage in CONFIG["storage"]["video"].values():
        if os.path.exists(f"{storage['path']}/cam{webcam}"):
            shutil.rmtree(f"{storage['path']}/cam{webcam}", ignore_errors=True)
        os.makedirs(f"{storage['path']}/cam{webcam}")


def new_video(webcam: int) -> list[dict[str, str | int]]:
    """
    Get a list of storage information for new video files for the given webcam

    :param webcam: Webcam id
    :return: List of storage information
    """
    
    storages = []
    for storage in CONFIG["storage"]["video"].values():
        if not os.path.exists(f"{storage['path']}/cam{webcam}"):
            raise FileNotFoundError(f"Video directory cam{webcam} not found! Please initialize it with reset.sh.")
        storages.append({
            "path": os.path.abspath(f"{storage['path']}/cam{webcam}/video_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"),
            "width": storage["width"],
            "height": storage["height"],
        })
    return storages
