"""
Utility functions to be used in multiple modules
"""

from .logging import init_logger
from .data import init_csv, write_csv, get_bus, get_interval, send_data, \
    get_influx_url, get_influx_org, get_influx_bucket, get_influx_token
from .video import init_video, new_video, new_photo, new_photo_small, camera_index, all_cameras
from .config import load_config, CONFIG
