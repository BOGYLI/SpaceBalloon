import utils
import time
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
import influxdb_client
 

# Initialize logger
logger = utils.init_logger("datamanager")

# Initialize FastAPI
app = FastAPI(title="Data Manager", description="Collect all sensor data via a HTTP server and transmit it", version="1.0")


# Define data models for the sensors
class ADC(BaseModel):
    uv: float
    methane: float


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
    disk: dict[str, float]


class Thermal(BaseModel):
    pixels: list[float]


# Store current sensor data
adc = ADC(uv=0, methane=0)
adc_updated = time.time()
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
system = System(cpu=0, memory=0, temp=0, sent=0, received=0, disk={})
system_updated = time.time()
thermal = Thermal(pixels=[])
thermal_updated = time.time()


@app.post("/adc")
def route_adc(data: ADC):
    global adc, adc_updated
    adc = data
    adc_updated = time.time()
    return {"status": "successfully updated data"}


@app.post("/climate")
def route_climate(data: Climate):
    global climate, climate_updated
    climate = data
    climate_updated = time.time()
    return {"status": "successfully updated data"}


@app.get("/climate")
def route_climate():
    return climate


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


@app.post("/thermal")
def route_thermal(data: Thermal):
    global thermal, thermal_updated
    thermal = data
    thermal_updated = time.time()
    return {"status": "successfully updated data"}


@app.on_event("startup")
@repeat_every(seconds=10)
def debug():

    logger.info(f"ADC ({time.time() - adc_updated:.1f} secs ago): {adc}")
    logger.info(f"Climate ({time.time() - climate_updated:.1f} secs ago): {climate}")
    logger.info(f"CO2 ({time.time() - co2_updated:.1f} secs ago): {co2}")
    logger.info(f"GPS ({time.time() - gps_updated:.1f} secs ago): {gps}")
    logger.info(f"Magnet ({time.time() - magnet_updated:.1f} secs ago): {magnet}")
    logger.info(f"Spectral ({time.time() - spectral_updated:.1f} secs ago): {spectral}")
    logger.info(f"System ({time.time() - system_updated:.1f} secs ago): {system}")
    logger.info(f"Thermal ({time.time() - thermal_updated:.1f} secs ago)")


@app.on_event("startup")
@repeat_every(seconds=2)
def influx():

    logger.debug("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=utils.get_influx_url(), org=utils.get_influx_org(),
                                        token=utils.get_influx_token(), timeout=2500) as client:

        points = [
            influxdb_client.Point("dm_adc").time(int(adc_updated), "s").field("uv", adc.uv).field("methane", adc.methane),
            influxdb_client.Point("dm_climate").time(int(climate_updated), "s").field("pressure", climate.pressure).field("temp", climate.temp).field("humidity", climate.humidity),
            influxdb_client.Point("dm_co2").time(int(co2_updated), "s").field("co2", co2.co2).field("voc", co2.voc),
            influxdb_client.Point("dm_gps").time(int(gps_updated), "s").field("latitude", gps.latitude).field("longitude", gps.longitude).field("altitude", gps.altitude),
            influxdb_client.Point("dm_magnet").time(int(magnet_updated), "s").field("temp", magnet.temp).field("heading", magnet.heading),
            influxdb_client.Point("dm_spectral").time(int(spectral_updated), "s").field("temp", spectral.temp).field("violet", spectral.violet).field("blue", spectral.blue)
            .field("green", spectral.green).field("yellow", spectral.yellow).field("orange", spectral.orange).field("red", spectral.red),
        ]

        system_point = influxdb_client.Point("dm_system").time(int(system_updated), "s").field("cpu", system.cpu).field("memory", system.memory) \
            .field("temp", system.temp).field("sent", system.sent).field("received", system.received)
        for disk_name, disk_usage in system.disk.items():
            system_point.field(disk_name, disk_usage)
        points.append(system_point)

        thermal_point = influxdb_client.Point("dm_thermal").time(int(thermal_updated), "s")
        for i, pixel in enumerate(thermal.pixels):
            thermal_point.field(f"pixel_{i}", pixel)
        points.append(thermal_point)

        write_api = client.write_api()
        for point in points:
            write_api.write(bucket=utils.get_influx_bucket(), record=point)
        write_api.close()

        logger.info("Successfully sent data to InfluxDB")
