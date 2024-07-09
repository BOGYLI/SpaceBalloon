import cv2
from video_capture_async import VideoCaptureAsync
import time

# Specify width and height of video to be recorded
vid_w = 1280
vid_h = 720

def find_available_camera():
    indices = [0, 1, 2, 3, 4, 5]  # List of possible camera indices to try

    for index in indices:
        try:
            # Initiate Video Capture object
            capture = VideoCaptureAsync(src=index, width=vid_w, height=vid_h)
            print(f"Successfully opened video device: /dev/video{index}")
            return capture  # Return the valid capture object
        except ValueError as e:
            print(e)
            continue

    raise ValueError("Error: Could not find an available video capture device.")

def record_video(duration):
    try:
        # Find an available camera
        capture = find_available_camera()

        # Initiate codec for Video recording object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 container

        # Start video capture
        capture.start()
        time_end = time.time() + duration

        frames = 0
        # Create array to hold frames from capture
        images = []
        # Capture for duration defined by variable 'duration'
        while time.time() <= time_end:
            ret, new_frame = capture.read()
            if not ret:
                raise ValueError("Error: Failed to capture frame.")

            frames += 1
            images.append(new_frame)

            # Display the frame (optional, remove for faster processing)
            cv2.imshow('frame', new_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        capture.stop()
        cv2.destroyAllWindows()

        # Calculate fps
        fps = frames / duration
        print(f"Frames captured: {frames}, Average FPS: {fps:.2f}")

        # Initiate the video object and video file named 'video.mp4'
        out = cv2.VideoWriter('video.mp4', fourcc, fps, (vid_w, vid_h))
        print("Creating video")
        # Write images to the video file
        for img in images:
            out.write(img)
        out.release()
        images = []
        print("Done")

    except ValueError as e:
        print(e)

# Example usage
if __name__ == "__main__":
    record_time = 300 # Record video for 300 seconds (5 minutes)
    record_video(record_time)
