import threading
import cv2

# Define video capture class
class VideoCaptureAsync:
    def __init__(self, src=0, width=640, height=480, driver=None):
        self.src = src
        if driver is None:
            self.cap = cv2.VideoCapture(self.src)
        else:
            self.cap = cv2.VideoCapture(self.src, driver)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Set MJPG codec

        if not self.cap.isOpened():
            print(f"Trying video device: /dev/video{self.src}")
            self.cap.release()
            self.cap = cv2.VideoCapture(f"/dev/video{self.src}")
            if not self.cap.isOpened():
                raise ValueError(f"Error: Could not open video device /dev/video{self.src}")
        else:
            print(f"Successfully opened video device: /dev/video{self.src}")

        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()
        self.thread = None

    def get(self, var1):
        return self.cap.get(var1)

    def set(self, var1, var2):
        self.cap.set(var1, var2)

    def start(self):
        if self.started:
            print('[!] Asynchronous video capturing has already been started.')
            return None
        self.started = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.started:
            grabbed, frame = self.cap.read()
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self):
        with self.read_lock:
            frame = self.frame
            grabbed = self.grabbed
        if frame is None:
            raise ValueError("Error: Failed to capture frame.")
        return grabbed, frame

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cap.release()
