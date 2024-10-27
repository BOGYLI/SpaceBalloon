import utils
import time
import os
import requests
import subprocess
from fastapi import FastAPI, Response, BackgroundTasks
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


class RestartSystem(BaseModel):
    code: str


class ManageService(BaseModel):
    service: str
    code: str


# Store current camera configuration
live_cam = LiveCam(webcam=utils.CONFIG["default"]["live"])
live_cam_updated = time.time()
video_cam = VideoCam(webcam0=utils.CONFIG["default"]["video0"],
                     webcam1=utils.CONFIG["default"]["video1"],
                     webcam2=utils.CONFIG["default"]["video2"])
video_cam_updated = time.time()
offline_cam = utils.CONFIG["default"]["offline"]
offline_pressure = utils.CONFIG["default"]["offline_pressure"]
offline_altitude = utils.CONFIG["default"]["offline_altitude"]
offline_mode = False
services_active = []
services_activating = []
services_failed = []
services_inactive = []
uptime = 0
services_updated = time.time()


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
    if offline_mode:
        video_cam.webcam1 = offline_cam
        video_cam.webcam2 = -1
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
        "services": {
            "active": services_active,
            "activating": services_activating,
            "failed": services_failed,
            "inactive": services_inactive,
            "alive": len(services_active),
            "dead": len(services_activating) + len(services_failed) + len(services_inactive)
        },
        "uptime": uptime
    }


@app.post("/restart/system")
def route_restart_system(data: RestartSystem, response: Response, background_tasks: BackgroundTasks):
    if data.code != "2507":
        response.status_code = 403
        return {"status": "wrong code"}
    print("Schedule system reboot")
    background_tasks.add_task(restart_system)
    return {"status": "restarting system"}


@app.post("/restart/service")
def route_restart_service(data: ManageService, response: Response):
    if data.code != "2507":
        response.status_code = 403
        return {"status": "wrong code"}
    print(f"Restart service {data.service}")
    os.system(f"systemctl restart {data.service}")
    print(f"Restarted service {data.service}")
    return {"status": "restarted service " + data.service}


@app.post("/start/service")
def route_start_service(data: ManageService, response: Response):
    if data.code != "2507":
        response.status_code = 403
        return {"status": "wrong code"}
    print(f"Start service {data.service}")
    os.system(f"systemctl start {data.service}")
    print(f"Started service {data.service}")
    return {"status": "started service " + data.service}


@app.post("/stop/service")
def route_stop_service(data: ManageService, response: Response):
    if data.code != "2507":
        response.status_code = 403
        return {"status": "wrong code"}
    print(f"Stop service {data.service}")
    os.system(f"systemctl stop {data.service}")
    print(f"Stopped service {data.service}")
    return {"status": "stopped service " + data.service}


def restart_system():
    time.sleep(5)
    print("Rebooting system")
    os.system("reboot")


@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("cm_debug"))
def debug():

    logger.info(f"Live cam ({time.time() - live_cam_updated:.1f} secs ago): {live_cam}")
    logger.info(f"Video cams ({time.time() - video_cam_updated:.1f} secs ago): {video_cam}")
    logger.info(f"Services ({time.time() - services_updated:.1f} secs ago):")
    logger.info(f"  active: {', '.join(services_active)}")
    logger.info(f"  activating: {', '.join(services_activating)}")
    logger.info(f"  failed: {', '.join(services_failed)}")
    logger.info(f"  inactive: {', '.join(services_inactive)}")
    logger.info(f"Uptime: {uptime} secs")


@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("cm_offline"))
def offline():

    global video_cam, video_cam_updated

    try:
        response = requests.get(f"http://127.0.0.1:8000/climate")
        data = response.json()
        if "pressure" in data:
            pressure = data["pressure"]
        response = requests.get(f"http://127.0.0.1:8000/gps")
        if "altitude" in data:
            altitude = data["altitude"]
    except requests.exceptions.RequestException:
        logger.warning("Failed to fetch current climate and GPS data")
        return

    logger.info(f"Pressure: {pressure:.1f} hPa / {offline_pressure} hPa")
    logger.info(f"Altitude: {altitude:.1f} m / {offline_altitude} m")

    if (pressure < offline_pressure or altitude > offline_altitude):
        offline_mode = True
        video_cam.webcam1 = offline_cam
        video_cam.webcam2 = -1
        video_cam_updated = time.time()
        logger.warning(f"Switched to offline camera mode due to low pressure or high altitude")
    else:
        if offline_mode:
            video_cam.webcam1 = utils.CONFIG["default"]["video1"]
            video_cam.webcam2 = utils.CONFIG["default"]["video2"]
            video_cam_updated = time.time()
            logger.warning(f"Switched back to normal camera mode due to high pressure and low altitude")
        offline_mode = False


@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("cm_services"))
def services():

    global services_active, services_activating, services_failed, services_inactive, uptime, services_updated

    try:
        active = subprocess.check_output("systemctl list-units --type=service --state=active | grep 'balloon-.*\.service'", stderr=subprocess.STDOUT, shell=True)
        services_active = [line.strip().split(" ")[0] for line in active.decode().splitlines() if line]
    except subprocess.CalledProcessError:
        services_active = []
    try:
        activating = subprocess.check_output("systemctl list-units --type=service --state=activating | grep 'balloon-.*\.service'", stderr=subprocess.STDOUT, shell=True)
        services_activating = [line.strip().split(" ")[0] for line in activating.decode().splitlines() if line]
    except subprocess.CalledProcessError:
        services_activating = []
    try:
        failed = subprocess.check_output("systemctl list-units --type=service --state=failed | grep 'balloon-.*\.service'", stderr=subprocess.STDOUT, shell=True)
        services_failed = [line.strip().split(" ")[0] for line in failed.decode().splitlines() if line]
    except subprocess.CalledProcessError:
        services_failed = []
    try:
        inactive = subprocess.check_output("systemctl list-units --type=service --state=inactive | grep 'balloon-.*\.service'", stderr=subprocess.STDOUT, shell=True)
        services_inactive = [line.strip().split(" ")[0] for line in inactive.decode().splitlines() if line]
    except subprocess.CalledProcessError:
        services_inactive = []

    with open('/proc/uptime', 'r') as f:
        uptime = float(f.readline().split()[0])

    services_updated = time.time()
