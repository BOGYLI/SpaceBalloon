"""
Read video from webcam
"""

import requests
import threading as th
import subprocess
import time
import sys
import cv2
import utils


# Webcam device
WEBCAM = int(sys.argv[1]) if len(sys.argv) > 1 else 0

# Video settings
LENGTH = 300
FPS = 15
SIZE = (1920, 1080)

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

# Mode
_video_mode = False
video_mode = False
video_mode_changed = True
_live_mode = False
live_mode = False
live_mode_changed = True
running = True


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
    output = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, SIZE)

    return output


def init_ffmpeg():

    # Initialize the FFmpeg process
    ffmpeg = subprocess.Popen(FFMPEG, stdin=subprocess.PIPE)

    return ffmpeg


def update_mode():
    
    global _video_mode, _live_mode, video_mode_changed, live_mode_changed
    
    while running:

        try:
            response = requests.get("http://127.0.0.1/live", timeout=1)
            if response.status_code == 200:
                target = response.json()["webcam"] == WEBCAM
                if target != live_mode:
                    _live_mode = target
                    live_mode_changed = True
            else:
                logger.error(f"Failed to update mode: {response.status_code}")
            response = requests.get("http://127.0.0.1/video", timeout=1)
            if response.status_code == 200:
                target = response.json()["webcam0"] == WEBCAM or response.json()["webcam1"] == WEBCAM or response.json()["webcam2"] == WEBCAM
                if target != video_mode:
                    _video_mode = target
                    video_mode_changed = True
            else:
                logger.error(f"Failed to update mode: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update mode: {e}")

        time.sleep(1)


def main():

    global video_mode, video_mode_changed, live_mode, live_mode_changed, running

    cap = None
    video = None
    ffmpeg = None

    time.sleep(WEBCAM * 4)

    mode_thread = th.Thread(target=update_mode, name="Mode Update", daemon=True)
    mode_thread.start()

    video_start_time = time.time()

    last_photo = 0

    while running:

        if video_mode_changed:
            video_mode = _video_mode
            video_mode_changed = False
            if video_mode:
                if cap is None:
                    cap = init_cam()
                if cap is None:
                    break
                video = init_video()
                if video is None:
                    break
                video_start_time = time.time()
            else:
                if cap is not None and not live_mode:
                    cap.release()
                    cap = None
                if video is not None:
                    video.release()
                    video = None

        if live_mode_changed:
            live_mode = _live_mode
            live_mode_changed = False
            if live_mode:
                if cap is None:
                    cap = init_cam()
                if cap is None:
                    break
                ffmpeg = init_ffmpeg()
            else:
                if cap is not None and not video_mode:
                    cap.release()
                    cap = None
                if ffmpeg is not None:
                    ffmpeg.stdin.close()
                    ffmpeg.wait(2)
                    ffmpeg.terminate()
                    ffmpeg = None

        take_photo = not video_mode and time.time() - last_photo > utils.get_interval("photo")

        if take_photo:
            if cap is None:
                cap = init_cam()
            if cap is None:
                break

        if cap is not None:
            ret, frame = cap.read()

        if not ret:
            logger.error("Cannot read frame from webcam")
            break

        if take_photo:
            path = utils.new_photo(WEBCAM)
            logger.info(f"Saving photo to {path}")
            cv2.imwrite(path, frame)
            last_photo = time.time()
            if not live_mode:
                cap.release()
                cap = None

        if video_mode:
            video.write(frame)
            if time.time() - video_start_time > LENGTH:
                video.release()
                video = init_video()
                video_start_time = time.time()

        if live_mode:
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            ffmpeg.stdin.write(buffer.tobytes())

        if not video_mode and not live_mode:
            time.sleep(0.2)

    if cap is not None:
        cap.release()
    if video is not None:
        video.release()
    if ffmpeg is not None:
        ffmpeg.stdin.close()
        ffmpeg.wait(2)
        ffmpeg.terminate()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM} ({utils.camera_index(WEBCAM)}) ...")

    main()
