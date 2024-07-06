"""
Read video from webcam
"""

import sys
import cv2
import utils


# Webcam device
WEBCAM = int(sys.argv[1]) if len(sys.argv) > 1 else 0

# Initialize logger
logger = utils.init_logger(f"webcam{WEBCAM}")


def main():

    # Open webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Check if the webcam is opened
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return
    
    # Initialize the video writers
    storages = utils.new_video(WEBCAM)
    logger.info(f"Saving video to {', '.join([storage['path'] for storage in storages])}")
    outputs = [cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 15.0, (1920, 1080)) for storage in storages]

    try:

        # Read video from webcam
        while True:

            # Read frame from webcam
            ret, frame = cap.read()

            # Check if the frame is read
            if not ret:
                logger.error("Cannot read frame from webcam")
                break


            # Write the frame to the video writers
            for i, output in enumerate(outputs):
                
                # Resize the frame and write
                #resized = .resize(frame, (storages[i]["width"], storages[i]["height"]))
                output.write(frame)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")

        for output in outputs:
            output.release()

    # Release the webcam
    cap.release()

    # Release the video writers
    for output in outputs:
        output.release()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM}...")

    main()
