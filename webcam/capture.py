import threading as th
import time
from lib import *


class VideoCapture(th.Thread):

    def __init__(self):

        th.Thread.__init__(self, name="Video Capture", daemon=True)

        self.cap = None
        self.grabbed = None
        self.frame = None
        self.lock = th.Lock()
        self.running = True
        self.standby = True

    def run(self):

        try:
            while self.running:

                if self.standby:
                    if self.cap is not None:
                        self.cap.release()
                        self.cap = None
                    time.sleep(0.1)
                    continue

                if self.cap is None:
                    self.cap = init_cam()
                    if self.cap is None:
                        self.running = False
                        break

                grabbed, frame = self.cap.read()
                with self.lock:
                    self.grabbed = grabbed
                    self.frame = frame
        except Exception as e:
            logger.error(f"Video capture error: {e}")
            self.running = False

        if self.cap is not None:
            self.cap.release()

    def read(self):

        if self.standby:
            
            if self.cap is None:
                self.cap = init_cam()
                if self.cap is None:
                    return False, None

            grabbed, frame = self.cap.read()
            with self.lock:
                self.grabbed = grabbed
                self.frame = frame
                        
            self.cap.release()
            self.cap = None

            return grabbed, frame

        with self.lock:
            return self.grabbed, self.frame
