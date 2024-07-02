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
    
    # Initialize the video writers
    storages = utils.new_video(WEBCAM)
    logger.info(f"Saving video to {', '.join([storage['path'] for storage in storages])}")
    fourcc = cv2.VideoWriter_fourcc(*"DIVX")
    outputs = [cv2.VideoWriter(storage["path"], fourcc, 15.0, (storage["height"], storage["width"])) for storage in storages]

    try:

        # Read video from webcam
        while True:

            # Read frame from webcam
            ret, frame = cap.read()

            # Check if the frame is read
            if not ret:
                logger.error("Cannot read frame from webcam")
                break

            logger.debug(frame.shape)

            # Write the frame to the video writers
            for i, output in enumerate(outputs):
                
                # Resize the frame and write
                resized = cv2.resize(frame, (storages[i]["width"], storages[i]["height"]))
                logger.debug(resized.shape)
                output.write(resized)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
        
    # Release the webcam
    cap.release()

    # Release the video writers
    for output in outputs:
        output.release()

    # Close all windows
    cv2.destroyAllWindows()


if __name__ == "__main__":

    logger.info(f"Starting webcam {WEBCAM}...")

    main()
