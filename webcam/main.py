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
    cap = cv2.VideoCapture(WEBCAM)

    # Check if the webcam is opened
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return
    
    # Initialize the video writer
    logger.debug(utils.new_video(WEBCAM))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    #TODO

    # Read video from webcam
    while True:

        # Read frame from webcam
        ret, frame = cap.read()

        # Check if the frame is read
        if not ret:
            logger.error("Cannot read frame from webcam")
            break

        # Display the frame
        cv2.imshow(f"Webcam {WEBCAM}", frame)

        # Break the loop
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release the webcam
    cap.release()

    # Close all windows
    cv2.destroyAllWindows()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM}...")

    main()
