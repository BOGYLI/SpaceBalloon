import utils
import time
from fastapi import FastAPI, BackgroundTasks
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
 

# Initialize logger
logger = utils.init_logger("datamanager")

# Initialize FastAPI
app = FastAPI(title="Data Manager", description="Collect all sensor data via a HTTP server and transmit it", version="1.0")


# Define data models for the sensors
class Climate(BaseModel):
    pressure: float
    temp: float
    humidity: float


class CO2(BaseModel):
    co2: float
    voc: float


class GPS(BaseModel):
    latitude: float
    longitude: float
    altitude: float


class Magnet(BaseModel):
    temp: float
    heading: float


class Spectral(BaseModel):
    temp: float
    violet: float
    blue: float
    green: float
    yellow: float
    orange: float
    red: float


class System(BaseModel):
    cpu: float
    memory: float
    temp: float
    sent: float
    received: float
    disk: list[float]


# Store current sensor data
climate = Climate(pressure=0, temp=0, humidity=0)
climate_updated = time.time()
co2 = CO2(co2=0, voc=0)
co2_updated = time.time()
gps = GPS(latitude=0, longitude=0, altitude=0)
gps_updated = time.time()
magnet = Magnet(temp=0, heading=0)
magnet_updated = time.time()
spectral = Spectral(temp=0, violet=0, blue=0, green=0, yellow=0, orange=0, red=0)
spectral_updated = time.time()
system = System(cpu=0, memory=0, temp=0, sent=0, received=0, disk=[])
system_updated = time.time()


@app.post("/climate")
def route_climate(data: Climate):
    global climate, climate_updated
    climate = data
    climate_updated = time.time()
    return {"status": "successfully updated data"}


@app.post("/co2")
def route_co2(data: CO2):
    global co2, co2_updated
    co2 = data
    co2_updated = time.time()
    return {"status": "successfully updated data"}


@app.post("/gps")
def route_gps(data: GPS):
    global gps, gps_updated
    gps = data
    gps_updated = time.time()
    return {"status": "successfully updated data"}


@app.post("/magnet")
def route_magnet(data: Magnet):
    global magnet, magnet_updated
    magnet = data
    magnet_updated = time.time()
    return {"status": "successfully updated data"}


@app.post("/spectral")
def route_spectral(data: Spectral):
    global spectral, spectral_updated
    spectral = data
    spectral_updated = time.time()
    return {"status": "successfully updated data"}


@app.post("/system")
def route_system(data: System):
    global system, system_updated
    system = data
    system_updated = time.time()
    return {"status": "successfully updated data"}


@app.on_event("startup")
@repeat_every(seconds=3)
def transmit():
    logger.info(climate)
    logger.info(co2)
    logger.info(gps)
    logger.info(magnet)
    logger.info(spectral)
    logger.info(system)
