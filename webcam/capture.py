import threading as th
import time
from lib import *


class VideoCapture(th.Thread):

    def __init__(self, device):

        th.Thread.__init__(self, name="Video Capture", daemon=True)

        self.cap = None
        self.grabbed = None
        self.frame = None
        self.lock = th.Lock()
        self.running = True
        self.standby = True
        self.active_time = 0
        self.device = device
        self.retries = 0

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
                    self.cap = init_cam(self.device)
                    if self.cap is None:
                        self.running = False
                        break

                grabbed, frame = self.cap.read()
                with self.lock:
                    self.grabbed = grabbed
                    self.frame = frame
                
                if not grabbed:
                    logger.warning(f"Video capture failed, {self.retries} retries made")
                    self.retries += 1
                    if self.retries > 3:
                        logger.warning("Reinitializing camera")
                        self.cap.release()
                        self.cap = init_cam(self.device)
                        if self.cap is None:
                            self.running = False
                            break
                        self.retries = 0
                        logger.warning("Retry count reset")
                else:
                    self.retries = 0

        except Exception as e:
            logger.error(f"Video capture error: {e}")
            self.running = False

        if self.cap is not None:
            self.cap.release()

    def read(self):

        if not self.standby:
            with self.lock:
                return self.grabbed, self.frame

        cap = init_cam(self.device)
        if cap is None:
            return False, None

        grabbed, frame = cap.read()
        self.grabbed = grabbed
        self.frame = frame
                    
        cap.release()
        cap = None

        return grabbed, frame

