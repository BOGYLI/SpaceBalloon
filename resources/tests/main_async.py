from record_video_async import record_video
from multiprocessing import Process

record_time = 20 # Record video for 300 seconds (5 minutes)
try:
    cam_record = Process(target=record_video, args=(record_time,))
    cam_record.start()
    cam_record.join()
    cam_record.close()
except ValueError as e:
    print(e)
