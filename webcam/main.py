"""
Read video from webcam
"""

import requests
import threading as th
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

    cap = None
    video = None
    ffmpeg = None

    mode_thread = th.Thread(target=update_mode)
    mode_thread.start()

    video_start_time = time.time()

    last_photo = 0

    while running:

        if video_mode_changed:
            _video_mode = video_mode
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
            _live_mode = live_mode
            live_mode_changed = False
            if live_mode:
                if cap is None:
                    cap = init_cam()
                if cap is None:
                    break
                ffmpeg = None # TODO
            else:
                if cap is not None and not video_mode:
                    cap.release()
                    cap = None
                if ffmpeg is not None:
                    ffmpeg.terminate()
                    ffmpeg = None

        if not video_mode and time.time() - last_photo > 20:
            if cap is None:
                cap = init_cam()
            if cap is None:
                break

        ret, frame = cap.read()

        if not ret:
            logger.error("Cannot read frame from webcam")
            break

        if not video_mode and time.time() - last_photo > 20:
            cv2.imwrite(utils.new_photo(WEBCAM), frame)
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
            pass

    if cap is not None:
        cap.release()
    if video is not None:
        video.release()
    if ffmpeg is not None:
        ffmpeg.terminate()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM} ({utils.camera_index(WEBCAM)}) ...")

    main()
