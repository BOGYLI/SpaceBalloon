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
        self.active_time = 0

    def run(self):

        try:
            while self.running:

                if self.standby:
                    if self.cap is not None:
                        logger.info("Standby mode")
                        self.cap.release()
                        self.cap = None
                    time.sleep(0.1)
                    continue

                if self.cap is None:
                    logger.info("Active mode")
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

        if not self.standby:
            with self.lock:
                return self.grabbed, self.frame

        cap = init_cam()
        if cap is None:
            return False, None

        grabbed, frame = cap.read()
        self.grabbed = grabbed
        self.frame = frame
                    
        cap.release()
        cap = None

        return grabbed, frame

