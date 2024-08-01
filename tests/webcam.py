import cv2
import threading
import time

# Video capture parameters
vid_w = 1280
vid_h = 720
fps = 30  # Desired frames per second
segment_duration = 20  # Duration of each video segment in seconds
video_counter = 0  # Counter for video file naming

class VideoCaptureAsync:
    def __init__(self, src=0, width=1280, height=720):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Use MJPG for better performance
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()
        self.thread = None

    def start(self):
        if self.started:
            return
        self.started = True
        self.thread = threading.Thread(target=self.update)
        self.thread.start()
        print("Started video capturing thread.")

    def update(self):
        while self.started:
            grabbed, frame = self.cap.read()
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self):
        with self.read_lock:
            return self.grabbed, self.frame

    def stop(self):
        self.started = False
        self.thread.join()
        print("Video capturing thread stopped.")

    def release(self):
        self.cap.release()
        print("Video capture released.")

def record_video_segment(segment_duration):
    global video_counter
    print(f"Starting to record video segment {video_counter}...")
    capture = VideoCaptureAsync(src=0, width=vid_w, height=vid_h)
    capture.start()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 container
    video_filename = f'video_segment_{video_counter}.mp4'
    out = cv2.VideoWriter(video_filename, fourcc, fps, (vid_w, vid_h))
    print(f"Video output file initialized: {video_filename}")

    time_end = time.time() + segment_duration
    frames = 0
    start_time = time.time()
    frame_time = 1.0 / fps  # Time per frame

    while True:
        grabbed, frame = capture.read()
        if not grabbed:
            print("Failed to capture frame.")
            break

        out.write(frame)  # Write the current frame to the video
        frames += 1

        # Check if the segment duration has passed
        if time.time() >= time_end:
            break

        # Add a delay to maintain the desired frame rate
        elapsed_time = time.time() - start_time
        sleep_time = frames * frame_time - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

    # Clean up
    capture.stop()
    out.release()
    print(f"Video segment {video_counter} recorded: {frames} frames")

    # Measure actual FPS
    total_time = time.time() - start_time
    actual_fps = frames / total_time if total_time > 0 else 0
    print(f"Actual FPS: {actual_fps:.2f}")

    video_counter += 1  # Increment the video counter

def main():
    try:
        while True:
            record_video_segment(segment_duration)  # Record a 20-second video segment
    except KeyboardInterrupt:
        print("Recording stopped by user.")

if __name__ == "__main__":
    main()
