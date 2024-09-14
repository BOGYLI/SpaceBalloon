import utils
import time
import serial
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
import influxdb_client


# Initialize logger
logger = utils.init_logger("datamanager")

# Initialize FastAPI
app = FastAPI(title="Data Manager", description="Collect all sensor data via a HTTP server and transmit it", version="1.0")

# KISS protocol
KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'
KISS_DATA_FRAME = b'\x00'


# Define data models for the sensors
class ADC(BaseModel):
    uv: float
    methane: float


class Climate(BaseModel):
    pressure: float
    temp: float
    humidity: float
    altitude: float


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
    x: float
    y: float
    z: float


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


class Thermal(BaseModel):
    min: float
    max: float
    avg: float
    median: float
    pixels: list[float]


# Store current sensor data
adc = ADC(uv=0, methane=0)
adc_updated = 0
climate = Climate(pressure=0, temp=0, humidity=0, altitude=0)
climate_updated = 0
co2 = CO2(co2=0, voc=0)
co2_updated = 0
gps = GPS(latitude=0, longitude=0, altitude=0)
gps_updated = 0
magnet = Magnet(temp=0, heading=0, x=0, y=0, z=0)
magnet_updated = 0
spectral = Spectral(temp=0, violet=0, blue=0, green=0, yellow=0, orange=0, red=0)
spectral_updated = 0
system = System(cpu=0, memory=0, temp=0, sent=0, received=0, disk=[])
system_updated = 0
thermal = Thermal(min=0, max=0, avg=0, median=0, pixels=[])
thermal_updated = 0


@app.post("/adc")
def route_adc(data: ADC):
    global adc, adc_updated
    adc = data
    adc_updated = time.time()
    return {"status": "successfully updated data"}


@app.post("/climate")
def route_climate_post(data: Climate):
    global climate, climate_updated
    climate = data
    climate_updated = time.time()
    return {"status": "successfully updated data"}


@app.get("/climate")
def route_climate_get():
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


def kiss_escape(data):
    """Escape special KISS characters in data."""
    data = data.replace(KISS_FEND, KISS_FESC + KISS_TFEND)
    data = data.replace(KISS_FESC, KISS_FESC + KISS_TFESC)
    return data


def construct_kiss_frame(aprs_packet):
    """Construct a KISS frame for an APRS packet."""
    kiss_frame = KISS_DATA_FRAME + aprs_packet
    kiss_frame = kiss_escape(kiss_frame)
    return KISS_FEND + kiss_frame + KISS_FEND


def convert_to_aprs_format(lat, lon):
    # Convert latitude to APRS format
    lat_deg = int(lat)
    lat_min = (lat - lat_deg) * 60
    lat_hemi = 'N' if lat >= 0 else 'S'
    aprs_lat = f'{abs(lat_deg):02d}{lat_min:05.2f}{lat_hemi}'

    # Convert longitude to APRS format
    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60
    lon_hemi = 'E' if lon >= 0 else 'W'
    aprs_lon = f'{abs(lon_deg):03d}{lon_min:05.2f}{lon_hemi}'

    return aprs_lat, aprs_lon


@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("dm_debug"))
def debug():

    logger.info(f"ADC ({time.time() - adc_updated:.1f} secs ago): {adc}")
    logger.info(f"Climate ({time.time() - climate_updated:.1f} secs ago): {climate}")
    logger.info(f"CO2 ({time.time() - co2_updated:.1f} secs ago): {co2}")
    logger.info(f"GPS ({time.time() - gps_updated:.1f} secs ago): {gps}")
    logger.info(f"Magnet ({time.time() - magnet_updated:.1f} secs ago): {magnet}")
    logger.info(f"Spectral ({time.time() - spectral_updated:.1f} secs ago): {spectral}")
    logger.info(f"System ({time.time() - system_updated:.1f} secs ago): {system}")
    logger.info(f"Thermal ({time.time() - thermal_updated:.1f} secs ago): min={thermal.min}, max={thermal.max}, avg={thermal.avg}, median={thermal.median}")
    
    
@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("dm_aprs"))
def aprs():

    for i in range(2):
    
        # Replace '/dev/ttyUSB0' with the appropriate serial port for your device
        logger.info("Open serial connection")
        ser = serial.Serial('/dev/ttyUSB0', 115200)

        # Ensure RTS and DTR are set low
        ser.rts = False
        ser.dtr = False

        # Construct an APRS packet
        src = "DN5WA-11"
        dest = "DN5WA-0"
        path = "WIDE1-1,WIDE2-2"
        aprs_lat, aprs_lon = convert_to_aprs_format(gps.latitude, gps.longitude)
        info = f"!{aprs_lat}/{aprs_lon}-{gps.altitude:.1f};{adc.uv:.1f};{adc.methane:.1f};{climate.pressure:.1f};{climate.temp:.1f};{climate.humidity:.1f};{climate.altitude:.1f};{co2.co2:.1f};{co2.voc:.1f};{magnet.temp:.1f};{magnet.heading:.1f};{spectral.temp:.1f};{spectral.violet:.1f};{spectral.blue:.1f};{spectral.green:.1f};{spectral.yellow:.1f};{spectral.orange:.1f};{spectral.red:.1f};{system.cpu:.1f};{system.memory:.1f};{system.temp:.1f};{system.sent:.1f};{system.received:.1f}"
        for disk_name, disk_usage in system.disk.items():
            info += f";{disk_name}:{disk_usage:.1f}"
        aprs_packet = f"{src}>{dest},{path}:{info}".encode('ascii')

        # Construct a KISS frame
        kiss_frame = construct_kiss_frame(aprs_packet)

        # Send the KISS frame over the serial connection
        logger.info("Write data to APRS")
        ser.write(kiss_frame)

        logger.info(f"Sent APRS packet: {aprs_packet.decode('ascii')}")

        ser.close()


@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("dm_influx"))
def influx():

    logger.debug("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=utils.get_influx_url(), org=utils.get_influx_org(),
                                        token=utils.get_influx_token(), timeout=2500) as client:

        points = []
        
        if adc_updated != 0:
            points.append(influxdb_client.Point("wifi_adc").time(int(adc_updated), "s").field("uv", adc.uv).field("methane", adc.methane))
        
        if climate_updated != 0:
            points.append(influxdb_client.Point("wifi_climate").time(int(climate_updated), "s").field("pressure", climate.pressure)
                          .field("temp", climate.temp).field("humidity", climate.humidity).field("altitude", climate.altitude))
        
        if co2_updated != 0:
            points.append(influxdb_client.Point("wifi_co2").time(int(co2_updated), "s").field("co2", co2.co2).field("voc", co2.voc))
        
        if gps_updated != 0:
            points.append(influxdb_client.Point("wifi_gps").time(int(gps_updated), "s").field("latitude", gps.latitude)
                          .field("longitude", gps.longitude).field("altitude", gps.altitude))
        
        if magnet_updated != 0:
            points.append(influxdb_client.Point("wifi_magnet").time(int(magnet_updated), "s").field("temp", magnet.temp).field("heading", magnet.heading)
                          .field("x", magnet.x).field("y", magnet.y).field("z", magnet.z))
            
        if spectral_updated != 0:
            points.append(influxdb_client.Point("wifi_spectral").time(int(spectral_updated), "s").field("temp", spectral.temp)
                          .field("violet", spectral.violet).field("blue", spectral.blue).field("green", spectral.green)
                          .field("yellow", spectral.yellow).field("orange", spectral.orange).field("red", spectral.red))
        
        if system_updated != 0:
            system_point = influxdb_client.Point("wifi_system").time(int(system_updated), "s").field("cpu", system.cpu).field("memory", system.memory) \
                .field("temp", system.temp).field("sent", system.sent).field("received", system.received)
            for i, value in enumerate(system.disk):
                if i % 2 == 0:
                    system_point.field(f"disk{i//2}_total", value)
                else:
                    system_point.field(f"disk{i//2}_used", value)
            points.append(system_point)

        if thermal_updated != 0:
            thermal_point = influxdb_client.Point("wifi_thermal").time(int(thermal_updated), "s").field("min", thermal.min).field("max", thermal.max) \
                .field("avg", thermal.avg).field("median", thermal.median).field("pixels", ",".join([int(x) for x in thermal.pixels]))
            points.append(thermal_point)

        if points:

            logger.info("Sending data to InfluxDB")

            write_api = client.write_api()
            for point in points:
                write_api.write(bucket=utils.get_influx_bucket(), record=point)
            write_api.close()

            logger.info("Successfully sent data to InfluxDB")
