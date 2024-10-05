import sys
import cv2
import os
import subprocess
import utils


# Webcam device
WEBCAM = int(sys.argv[1]) if len(sys.argv) > 1 else 0

# Camera settings
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_SIZE = (CAMERA_WIDTH, CAMERA_HEIGHT)
CAMERA_FOURCC = cv2.VideoWriter_fourcc(*'MJPG')

# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_SIZE = (VIDEO_WIDTH, VIDEO_HEIGHT)
VIDEO_FOURCC = cv2.VideoWriter_fourcc(*'mp4v')
VIDEO_FPS = 15
VIDEO_LENGTH = 300

# Livestream settings
LIVE_WIDTH = 576
LIVE_HEIGHT = 324
LIVE_SIZE = (LIVE_WIDTH, LIVE_HEIGHT)
LIVE_FPS = 15
LIVE_QUALITY = 70

# Photo settings
PHOTO_WIDTH = 1920
PHOTO_HEIGHT = 1080
PHOTO_SIZE = (PHOTO_WIDTH, PHOTO_HEIGHT)
PHOTO_QUALITY = 90
PHOTO_SMALL_WIDTH = 768
PHOTO_SMALL_HEIGHT = 432
PHOTO_SMALL_SIZE = (PHOTO_SMALL_WIDTH, PHOTO_SMALL_HEIGHT)
PHOTO_SMALL_QUALITY = 60

# FFmpeg command
FFMPEG = [
    'ffmpeg',
    '-re',
    '-f', 'image2pipe',
    '-vcodec', 'mjpeg',
    '-i', '-',
    '-f', 'mpegts',
    '-vcodec', 'h264',
    '-bf', '0',
    utils.CONFIG["stream"]["url"]
    .replace("#PATH", f"cam{WEBCAM}")
    .replace("#USERNAME", utils.CONFIG["stream"]["username"])
    .replace("#PASSWORD", utils.CONFIG["stream"]["password"])
]

# Initialize logger
logger = utils.init_logger(f"webcam{WEBCAM}")


def init_cam(device):

    # Open webcam
    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, CAMERA_FOURCC)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    # Check if the webcam is opened
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return

    return cap


def init_video():

    # Initialize the video writer
    path = utils.new_video(WEBCAM)
    logger.info(f"Saving video to {path}")
    output = cv2.VideoWriter(path, VIDEO_FOURCC, VIDEO_FPS, VIDEO_SIZE)

    return output


def init_ffmpeg():

    # Initialize the FFmpeg process
    ffmpeg = subprocess.Popen(FFMPEG, stdin=subprocess.PIPE)

    return ffmpeg


def get_camera_devices():
    video_devices = []
    for device in os.listdir('/dev'):
        if device.startswith('video'):
            video_devices.append(f"/dev/{device}")
    return video_devices


def get_usb_port_for_video_device(video_device):
    try:
        cmd = f"udevadm info --query=all --name={video_device} | grep ID_PATH="
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        usb_path = result.stdout.decode().strip()
        if usb_path:
            return usb_path.split('=')[-1]  # Extract the ID_PATH value
    except Exception as e:
        print(f"Error getting USB port for {video_device}: {e}")
    return None


def get_camera_index_by_usb_port(usb_port):
    devices = get_camera_devices()
    for device in devices:
        usb_path = get_usb_port_for_video_device(device)
        if usb_path and usb_port in usb_path:
            return device  # Return the corresponding /dev/video* device
    return None
