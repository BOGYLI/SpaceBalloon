import sys
import cv2
import subprocess
import utils


# Webcam device
WEBCAM = int(sys.argv[1]) if len(sys.argv) > 1 else 0

# Video settings
VIDEO_LENGTH = 120
VIDEO_FPS = 15
VIDEO_SIZE = (1920, 1080)

# FFmpeg command
FFMPEG = [
    'ffmpeg',
    '-re',
    '-f', 'image2pipe',
    '-vcodec', 'mjpeg',
    '-i', '-',
    '-f', 'mpegts',
    utils.CONFIG["stream"]["url"]
    .replace("#PATH", f"cam{WEBCAM}")
    .replace("#USERNAME", utils.CONFIG["stream"]["username"])
    .replace("#PASSWORD", utils.CONFIG["stream"]["password"])
]

# Initialize logger
logger = utils.init_logger(f"webcam{WEBCAM}")


def init_cam():

    # Open webcam
    cap = cv2.VideoCapture(utils.camera_index(WEBCAM), cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    # Check if the webcam is opened
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return

    return cap


def init_video():

    # Initialize the video writer
    path = utils.new_video(WEBCAM)
    logger.info(f"Saving video to {path}")
    output = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), VIDEO_FPS, VIDEO_SIZE)

    return output


def init_ffmpeg():

    # Initialize the FFmpeg process
    ffmpeg = subprocess.Popen(FFMPEG, stdin=subprocess.PIPE)

    return ffmpeg
