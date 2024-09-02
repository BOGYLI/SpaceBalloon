"""
Read video from webcam
"""

import requests
import threading as th
import time
import cv2
import utils
from capture import VideoCapture
from lib import *


# Mode
video_mode = False
video_mode_new = False
live_mode = False
live_mode_new = False
running = True

# Timer
last_photo = 0
video_start_time = time.time()


def update_mode():
    
    global video_mode_new, live_mode_new
    
    while running:

        try:
            response = requests.get("http://127.0.0.1/live", timeout=1)
            if response.status_code == 200:
                target = response.json()["webcam"] == WEBCAM
                if target != live_mode:
                    live_mode_new = target
            else:
                logger.error(f"Failed to update mode: {response.status_code}")
            response = requests.get("http://127.0.0.1/video", timeout=1)
            if response.status_code == 200:
                target = response.json()["webcam0"] == WEBCAM or response.json()["webcam1"] == WEBCAM or response.json()["webcam2"] == WEBCAM
                if target != video_mode:
                    video_mode_new = target
            else:
                logger.error(f"Failed to update mode: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update mode: {e}")

        time.sleep(1)


def take_photo(frame):

    global last_photo

    path = utils.new_photo(WEBCAM)
    logger.info(f"Saving photo to {path}")
    cv2.imwrite(path, frame)
    last_photo = time.time()


def main():

    global video_mode, live_mode, running

    capture = VideoCapture()
    capture.start()
    video = None
    ffmpeg = None

    time.sleep(WEBCAM * utils.get_interval("photo_offset"))

    mode_thread = th.Thread(target=update_mode, name="Mode Update", daemon=True)
    mode_thread.start()

    while running:
        
        if live_mode != live_mode_new:
            live_mode = live_mode_new
            if live_mode:
                ffmpeg = init_ffmpeg()
            else:
                if ffmpeg is not None:
                    ffmpeg.stdin.close()
                    ffmpeg.wait(2)
                    ffmpeg.terminate()
                    ffmpeg = None

        if video_mode != video_mode_new:
            video_mode = video_mode_new
            if video_mode:
                video = init_video()
                video_start_time = time.time()
            else:
                if video is not None:
                    video.release()
                    video = None

        capture.standby = not video_mode and not live_mode

        take_photo = time.time() - last_photo > utils.get_interval("photo_delay")

        if take_photo or video_mode or live_mode:
            grabbed, frame = capture.read()
            if not grabbed:
                logger.error("Cannot read frame from webcam")
                running = False
                break
            
        if take_photo:
            th.Thread(target=update_mode, name="Photo Write", daemon=True).start()

        if video_mode and not live_mode:
            video.write(frame)
            if time.time() - video_start_time > VIDEO_LENGTH:
                video.release()
                video = init_video()
                video_start_time = time.time()

        if live_mode:
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            ffmpeg.stdin.write(buffer.tobytes())

        if not video_mode and not live_mode:
            time.sleep(0.2)

    capture.running = False
    capture.join(2)

    if video is not None:
        video.release()

    if ffmpeg is not None:
        ffmpeg.stdin.close()
        ffmpeg.wait(2)
        ffmpeg.terminate()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM} ({utils.camera_index(WEBCAM)}) ...")

    main()
