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
start_time = time.time()
frames = 0

# Components
capture = VideoCapture()
video = None
ffmpeg = None


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


def save_photo(frame):

    global last_photo

    path = utils.new_photo(WEBCAM)
    logger.info(f"Saving photo to {path}")
    cv2.imwrite(path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), PHOTO_QUALITY])

    path = utils.new_photo_small(WEBCAM)
    logger.info(f"Saving small photo to {path}")
    resized = cv2.resize(frame, PHOTO_SMALL_SIZE, interpolation=cv2.INTER_AREA)
    cv2.imwrite(path, resized, [int(cv2.IMWRITE_JPEG_QUALITY), PHOTO_SMALL_QUALITY])

    logger.info("Photo saved")


def main():

    global video_mode, live_mode, running, video_start_time, video_frames, last_photo, capture, video, ffmpeg

    capture.start()

    live_mode_changed = False

    time.sleep(WEBCAM * utils.get_interval("photo_offset"))

    mode_thread = th.Thread(target=update_mode, name="Mode Update", daemon=True)
    mode_thread.start()

    while running:
        
        if live_mode != live_mode_new:
            live_mode = live_mode_new
            live_mode_changed = True
            if live_mode:
                logger.info("Starting live stream ...")
                ffmpeg = init_ffmpeg()
                start_time = time.time()
                frames = 0
            else:
                logger.info("Stopping live stream ...")
                if ffmpeg is not None:
                    ffmpeg.stdin.close()
                    ffmpeg.wait(2)
                    ffmpeg.terminate()
                    ffmpeg = None

        if video_mode != video_mode_new or live_mode_changed:
            video_mode = video_mode_new
            if video_mode and not live_mode:
                logger.info("Starting video recording ...")
                video = init_video()
                start_time = time.time()
                frames = 0
            else:
                if video is not None:
                    logger.info("Stopping video recording ...")
                    video.release()
                    video = None
            live_mode_changed = False

        new_standby = not video_mode and not live_mode
        if capture.standby != new_standby:
            capture.standby = new_standby
            if not capture.standby:
                capture.active_time = time.time()

        take_photo = time.time() - last_photo > utils.get_interval("photo_delay")

        if take_photo or video_mode or live_mode:
            grabbed, frame = capture.read()
            if not grabbed:
                if (time.time() - capture.active_time > 6 and not capture.standby) or (take_photo and capture.standby):
                    logger.error("Cannot read frame from webcam")
                    running = False
                    break
                time.sleep(0.1)
                continue
            
        if take_photo:
            logger.info("Schedule photo taking ...")
            last_photo = time.time()
            th.Thread(target=save_photo, args=(frame,), name="Photo Write", daemon=True).start()

        if live_mode:
            resized = cv2.resize(frame, LIVE_SIZE, interpolation=cv2.INTER_NEAREST)
            _, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), LIVE_QUALITY])
            try:
                ffmpeg.stdin.write(buffer.tobytes())
            except OSError as e:
                logger.error(f"Failed to write frame to ffmpeg: {e}")
                if live_mode:
                    logger.info("Restarting live stream ...")
                    if ffmpeg is not None:
                        ffmpeg.stdin.close()
                        ffmpeg.wait(2)
                        ffmpeg.terminate()
                    time.sleep(2)
                    ffmpeg = init_ffmpeg()
                    start_time = time.time()
                    frames = 0

        if video_mode and not live_mode:
            video.write(frame)
            if time.time() - start_time > VIDEO_LENGTH:
                video.release()
                video = init_video()
                start_time = time.time()
                frames = 0
        
        if not capture.running:
            logger.error("Video capture thread stopped, exiting")
            running = False
            break

        if video_mode or live_mode:
            frames += 1
            elapsed_time = time.time() - start_time
            sleep_time = frames * (1 / (LIVE_FPS if live_mode else VIDEO_FPS)) - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        else:
            time.sleep(0.2)

    capture.running = False
    capture.join(2)

    if video is not None:
        logger.info("Releasing video ...")
        video.release()

    if ffmpeg is not None:
        logger.info("Closing ffmpeg ...")
        ffmpeg.stdin.close()
        ffmpeg.wait(2)
        ffmpeg.terminate()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM} ({utils.camera_index(WEBCAM)}) ...")

    main()
