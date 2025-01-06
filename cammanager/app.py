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
live_cam = LiveCam(webcam=-1)
live_cam_updated = time.time()
video_cam = VideoCam(webcam0=-1, webcam1=-1, webcam2=-1)
video_cam_updated = time.time()
offline_auto = utils.CONFIG["mode"]["offline_auto"]
offline_ping = utils.CONFIG["mode"]["offline_ping"]
pop_auto = utils.CONFIG["mode"]["pop_auto"]
pop_pressure = utils.CONFIG["mode"]["pop_pressure"]
pop_altitude = utils.CONFIG["mode"]["pop_altitude"]
offline = False
pop = False
last_ping = time.time()
last_cycle = 0
services_active = []
services_activating = []
services_failed = []
services_inactive = []
uptime = 0
services_updated = time.time()


@app.post("/live")
def route_live(data: LiveCam):
    global live_cam, live_cam_updated
    online()
    live_cam = data
    live_cam_updated = time.time()
    return {"status": "successfully updated data"}


@app.get("/live")
def route_live():
    return live_cam


@app.post("/video")
def route_video(data: VideoCam, response: Response):
    global video_cam, video_cam_updated
    online()
    if pop:
        response.status_code = 400
        return {"status": "cannot update data in pop mode"}
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
        "uptime": uptime,
        "offline": offline,
        "pop": pop,
        "last_ping": last_ping,
        "last_cycle": last_cycle
    }


@app.post("/restart/system")
def route_restart_system(data: RestartSystem, response: Response, background_tasks: BackgroundTasks):
    online()
    if data.code != "2507":
        response.status_code = 403
        return {"status": "wrong code"}
    print("Schedule system reboot")
    background_tasks.add_task(restart_system)
    return {"status": "restarting system"}


@app.post("/restart/service")
def route_restart_service(data: ManageService, response: Response):
    online()
    if data.code != "2507":
        response.status_code = 403
        return {"status": "wrong code"}
    print(f"Restart service {data.service}")
    os.system(f"systemctl restart {data.service}")
    print(f"Restarted service {data.service}")
    return {"status": "restarted service " + data.service}


@app.post("/start/service")
def route_start_service(data: ManageService, response: Response):
    online()
    if data.code != "2507":
        response.status_code = 403
        return {"status": "wrong code"}
    print(f"Start service {data.service}")
    os.system(f"systemctl start {data.service}")
    print(f"Started service {data.service}")
    return {"status": "started service " + data.service}


@app.post("/stop/service")
def route_stop_service(data: ManageService, response: Response):
    online()
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
    logger.info(f"Offline mode: {offline}")
    logger.info(f"Pop mode: {pop}")
    logger.info(f"Last ping: {time.time() - last_ping:.1f} secs ago")
    logger.info(f"Last cycle: {time.time() - last_cycle:.1f} secs ago")


def online():

    global offline, last_ping, last_cycle

    if offline:
        last_cycle = 0
        offline = False
        logger.warning(f"Switched back to online mode due to manual override")

    last_ping = time.time()


def refresh_offline():

    global offline, last_ping, last_cycle

    logger.info(f"Pinging {offline_ping}")
    try:
        response = os.system(f"ping -c 1 -W 5 {offline_ping}")
        if response == 0:
            logger.info(f"Successfully pinged {offline_ping}")
            if offline:
                last_cycle = 0
                offline = False
                logger.warning(f"Switched back to online mode due to successful ping")
            last_ping = time.time()
        else:
            logger.warning(f"Failed to ping {offline_ping}")
    except Exception as e:
        logger.warning(f"Failed to ping {offline_ping}: {e}")
        
    if not offline_auto:
        return

    if time.time() - last_ping > utils.get_interval("ping_fail") and not offline:
        last_cycle = 0
        offline = True
        logger.warning(f"Switched to offline mode due to failing pings for {utils.get_interval('ping_fail')} secs")


def refresh_pop():

    global pop, last_cycle

    logger.info("Fetching current climate and GPS data")
    try:
        response = requests.get(f"http://127.0.0.1:8000/climate", timeout=3)
        data = response.json()
        pressure = data["pressure"] if "pressure" in data else 0
        response = requests.get(f"http://127.0.0.1:8000/gps", timeout=3)
        data = response.json()
        altitude = data["altitude"] if "altitude" in data else 0
    except requests.exceptions.RequestException:
        logger.warning("Failed to fetch current climate and GPS data")
        pop = False
        return
    
    if pressure == 0 and altitude == 0:
        logger.warning("Current climate and GPS data not available")
        pop = False
        return

    logger.info(f"Pressure: {pressure:.1f} hPa / {pop_pressure} hPa")
    logger.info(f"Altitude: {altitude:.1f} m / {pop_altitude} m")

    if not pop_auto:
        return

    if (0 < pressure < pop_pressure or altitude > pop_altitude) and not pop:
        last_cycle = 0
        pop = True
        logger.warning(f"Switched to pop mode due to low pressure or high altitude")
        return

    pressure_only = pressure > pop_pressure + 20 and altitude == 0
    altitude_only = 0 < altitude < pop_altitude - 500 and pressure == 0
    both = pressure > pop_pressure + 20 and 0 < altitude < pop_altitude - 500
    if (pressure_only or altitude_only or both) and pop:
        last_cycle = 0
        pop = False
        logger.warning(f"Switched back to normal mode due to high pressure and low altitude")


@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("cm_mode"))
def mode():

    global live_cam, live_cam_updated, video_cam, video_cam_updated, last_cycle

    refresh_offline()
    refresh_pop()

    if time.time() - last_cycle < utils.get_interval("cam_cycle"):
        return

    if not last_cycle:
        logger.info("Mode changed, triggering camera cycle")
    else:
        logger.info(f"{time.time() - last_cycle} secs passed, triggering camera cycle")

    last_cycle = time.time()

    if pop:

        logger.info(f"Cycle cameras according to pop mode")

        if live_cam.webcam != -1:
            live_cam.webcam = -1
            live_cam_updated = time.time()
            logger.info(f"Disabled live camera")
        video_cam.webcam0 = video_cam.webcam0 + 1 if video_cam.webcam0 < 3 else 0
        logger.info(f"Changed camera slot 0 to webcam {video_cam.webcam0}")
        if video_cam.webcam1 != 4:
            video_cam.webcam1 = 4
            logger.info(f"Changed camera slot 1 to webcam 4")
        if video_cam.webcam2 != -1:
            video_cam.webcam2 = -1
            logger.info(f"Disabled camera slot 2")
        video_cam_updated = time.time()

        return
    
    if offline:

        logger.info(f"Cycle cameras according to offline mode")

        if live_cam.webcam != -1:
            live_cam.webcam = -1
            live_cam_updated = time.time()
            logger.info(f"Disabled live camera")
        video_cam.webcam0 = 3 if video_cam.webcam0 != 3 else 2
        logger.info(f"Changed camera slot 0 to webcam {video_cam.webcam0}")
        if video_cam.webcam1 not in (0, 1, 4):
            video_cam.webcam1 = 0
        else:
            video_cam.webcam1 = 1 if video_cam.webcam1 == 0 else (4 if video_cam.webcam1 == 1 else 0)
        logger.info(f"Changed camera slot 1 to webcam {video_cam.webcam1}")
        if video_cam.webcam2 != -1:
            video_cam.webcam2 = -1
            logger.info(f"Disabled camera slot 2")
        video_cam_updated = time.time()

        return
    
    logger.info(f"No mode active, skipping camera cycle")


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
