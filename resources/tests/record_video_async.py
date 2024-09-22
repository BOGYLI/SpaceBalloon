import cv2
from video_capture_async import VideoCaptureAsync
import time
import threading

# Specify width and height of video to be recorded (lower for better performance)
vid_w = 640  # Reduced width
vid_h = 480  # Reduced height

# Video writing flag
writing_video = True

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

def write_video_segment(file_name, frame, fps):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(file_name, fourcc, fps, (vid_w, vid_h))
    out.write(frame)  # Write only the current frame to the video
    out.release()  # Release the video writer

def record_video(duration):
    global writing_video
    try:
        # Find an available camera
        capture = find_available_camera()
        capture.start()

        fps = 15  # Set a lower frame rate for better performance
        segment_duration = 20  # Duration for each video segment in seconds
        time_end = time.time() + duration

        while time.time() <= time_end:
            ret, frame = capture.read()
            if not ret:
                raise ValueError("Error: Failed to capture frame.")

            # Display the frame (optional, remove for faster processing)
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Write the current frame to a video file every `segment_duration`
            if (time.time() % segment_duration) < 0.1:  # Write every 20 seconds
                file_name = f'output_{int(time.time())}.mp4'
                writing_thread = threading.Thread(target=write_video_segment, args=(file_name, frame, fps))
                writing_thread.start()

        capture.stop()
        cv2.destroyAllWindows()
        print("Recording finished.")

    except ValueError as e:
        print(e)

# Example usage
if __name__ == "__main__":
    record_time = 300  # Record video for 300 seconds (5 minutes)
    record_video(record_time)
