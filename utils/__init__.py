"""
Utility functions to be used in multiple modules
"""

from .logging import init_logger
from .data import init_csv, write_csv
from .video import init_video, new_video
from .config import load_config, CONFIG
