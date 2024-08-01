import cv2
import numpy as np

# Function to get HSV values of a pixel when clicked
def get_hsv(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        print("HSV values at ({},{}): {}".format(x, y, hsv[y, x]))

# OpenCV video capture from webcam (index 0)
cap = cv2.VideoCapture(0)

while True:
    # Capture frame from webcam
    ret, frame = cap.read()

    # Display the frame
    cv2.imshow("Frame", frame)

    # Set mouse callback function to get HSV values when clicked
    cv2.setMouseCallback("Frame", get_hsv)

    # Press 'q' to exit the program
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()