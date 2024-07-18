import utils
import time
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
 

# Initialize logger
logger = utils.init_logger("cammanger")

# Initialize FastAPI
app = FastAPI(title="Cam Manager", description="Communicate with cameras and mission control", version="1.0")


# Define data models for requests
class LiveCam(BaseModel):
    webcam: int


class VideoCam(BaseModel):
    webcam0: int
    webcam1: int
    webcam2: int


# Store current camera configuration
live_cam = LiveCam(webcam=0) # TODO get from config
live_cam_updated = time.time()
video_cam = VideoCam(webcam0=0, webcam1=1, webcam2=2)
video_cam_updated = time.time()


@app.post("/live")
def route_live(data: LiveCam):
    global live_cam, live_cam_updated
    live_cam = data
    live_cam_updated = time.time()
    return {"status": "successfully updated data"}


@app.get("/live")
def route_live():
    return live_cam


@app.post("/video")
def route_video(data: VideoCam):
    global video_cam, video_cam_updated
    video_cam = data
    video_cam_updated = time.time()
    return {"status": "successfully updated data"}


@app.get("/video")
def route_video():
    return video_cam


@app.get("/status")
def route_status():
    return {
        "live": live_cam,
        "video": video_cam,
    }


@app.on_event("startup")
@repeat_every(seconds=3)
def debug():

    logger.info(live_cam)
    logger.info(video_cam)
