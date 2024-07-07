"""
Read video from webcam
"""

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


def main():

    # Open webcam
    cap = cv2.VideoCapture(WEBCAM, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Check if the webcam is opened
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return
    
    # Initialize the FFmpeg processes
    path = utils.new_video(WEBCAM)
    logger.info(f"Saving video to {path}")
    output = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, SIZE)

    # Video start time
    start_time = time.time()

    try:

        # Read video from webcam
        while True:

            # Read frame from webcam
            ret, frame = cap.read()

            # Check if the frame is read
            if not ret:
                logger.error("Cannot read frame from webcam")
                break

            # Write the frame to the video file
            output.write(frame)

            # Check if the video length is reached
            if time.time() - start_time > LENGTH:
                
                # Close the video file
                output.release()

                # Start a new video file
                path = utils.new_video(WEBCAM)
                logger.info(f"Saving video to {path}")
                output = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, SIZE)

                # Update the start time
                start_time = time.time()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")

        output.release()

    # Release the webcam
    cap.release()

    # Release the video writers
    output.release()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM}...")

    main()
