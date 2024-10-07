import utils
import time
import serial
import struct
import base64
import threading as th
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
import influxdb_client
from aprslib import *


# Initialize logger
logger = utils.init_logger("datamanager")

# Initialize FastAPI
app = FastAPI(title="Data Manager", description="Collect all sensor data via a HTTP server and transmit it", version="1.0")
running = True


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


@app.get("/gps")
def route_gps():
    return gps


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


def encode_aprs_comment():
    
    # Compress values to bytes
    gps_altitude = struct.pack('H', min(max(int(gps.altitude), 0), 65535))  # 2 bytes, 0-65535
    adc_uv = struct.pack('H', min(max(int(adc.uv * 1000), 0), 65535))  # 2 bytes, 0-65535
    adc_methane = struct.pack('H', min(max(int(adc.methane), 0), 65535))  # 2 bytes, 0-65535
    climate_pressure = struct.pack('H', min(max(int(climate.pressure), 0), 65535))  # 2 bytes, 0-65535
    climate_temp = struct.pack('b', min(max(int(climate.temp), -128), 127))  # 1 byte, -128-127
    climate_humidity = struct.pack('B', min(max(int(climate.humidity), 0), 255))  # 1 byte, 0-255
    climate_altitude = struct.pack('H', min(max(int(climate.altitude), 0), 65535))  # 2 bytes, 0-65535
    co2_co2 = struct.pack('H', min(max(int(co2.co2), 0), 65535))  # 2 bytes, 0-65535
    co2_voc = struct.pack('H', min(max(int(co2.voc), 0), 65535))  # 2 bytes, 0-65535
    magnet_heading = struct.pack('H', min(max(int(magnet.heading), 0), 65535))  # 2 bytes, 0-65535
    system_cpu = struct.pack('B', min(max(int(system.cpu), 0), 255))  # 1 byte, 0-255
    system_memory = struct.pack('B', min(max(int(system.memory), 0), 255))  # 1 byte, 0-255
    system_temp = struct.pack('b', min(max(int(system.temp), -128), 127))  # 1 byte, -128-127
    thermal_min = struct.pack('b', min(max(int(thermal.min), -128), 127))  # 1 byte, -128-127
    thermal_max = struct.pack('b', min(max(int(thermal.max), -128), 127))  # 1 byte, -128-127
    thermal_avg = struct.pack('b', min(max(int(thermal.avg), -128), 127))  # 1 byte, -128-127
    thermal_median = struct.pack('b', min(max(int(thermal.median), -128), 127))  # 1 byte, -128-127

    # Concatenate all data (total 25 bytes)
    data = gps_altitude + adc_uv + adc_methane + climate_pressure + climate_temp + climate_humidity + \
        climate_altitude + co2_co2 + co2_voc + magnet_heading + system_cpu + system_memory + system_temp + \
        thermal_min + thermal_max + thermal_avg + thermal_median

    # Base64 encode the data
    return base64.b64encode(data).decode()

    
def aprs():
    
    last_sent = 0

    while running:

        try:

            # Open serial connection
            logger.info("Open serial connection")
            ser = serial.Serial('/dev/ttyUSB0', 115200)

            # Ensure RTS and DTR are set low
            ser.rts = False
            ser.dtr = False

            # Receive buffer
            buffer = bytearray()

            while running:

                # Check if it is time to send an APRS packet
                if time.time() - last_sent > utils.get_interval("dm_aprs"):

                    # Construct an APRS packet
                    try:
                        aprs_src = utils.get_aprs_src().split("-")[0]
                        aprs_src_ssid = int(utils.get_aprs_src().split("-")[1])
                        aprs_dest = utils.get_aprs_dst().split("-")[0]
                        aprs_dest_ssid = int(utils.get_aprs_dst().split("-")[1])
                    except (IndexError, ValueError):
                        logger.error("Invalid APRS source or destination")
                    aprs_lat, aprs_lon = encode_gps_aprs(gps.latitude, gps.longitude)
                    aprs_comment = encode_aprs_comment()
                    aprs_message = f"!{aprs_lat}/{aprs_lon}OSpace Balloon Mission Data: {aprs_comment}"
                    logger.info(f"APRS packet data: {aprs_src}-{aprs_src_ssid} > {aprs_dest}-{aprs_dest_ssid} | {aprs_message}")

                    # Construct a AX.25 frame
                    ax25_frame = encode_ax25_frame(aprs_src, aprs_src_ssid, aprs_dest, aprs_dest_ssid, aprs_message)
                    logger.info(f"AX.25 Frame: {to_hex_bytes(ax25_frame)}")

                    # Construct a KISS frame
                    kiss_frame = construct_kiss_frame(ax25_frame)
                    logger.info(f"KISS Frame: {to_hex_bytes(kiss_frame)}")

                    # Send the KISS frame over the serial connection
                    logger.info("Write data to APRS")
                    ser.write(kiss_frame)

                    last_sent = time.time()

                # Read data from the serial connection
                byte = ser.read(1)

                if byte == KISS_FEND:

                    print("Received KISS frame FEND")
                    if buffer:

                        print(f"KISS frame complete: {buffer.hex()}")
                        kiss_frame = kiss_unescape(buffer)
                        
                        # Skip the KISS command byte (first byte)
                        ax25_frame = kiss_frame[1:]
                        
                        # Decode AX.25 frame
                        source_call, dest_call, path, message = decode_ax25_frame(ax25_frame)
                        
                        print(f"Received message from {source_call}: {message}")
                        print(f"Destination: {dest_call}, Path: {path}")

                        if dest_call == utils.get_aprs_src():
                            print("Received message for me!")
                        
                        buffer.clear()

                else:
                    buffer += byte
                

            logger.info(f"Closing serial connection")
            ser.close()

        except Exception as e:
            logger.error(f"An unexpected error occurred in the APRS thread: {e}")
            logger.error("Retrying in 20 seconds")
            time.sleep(20)


@app.on_event("startup")
def start_aprs():

    th.Thread(target=aprs).start()


@app.on_event("shutdown")
def stop_aprs():

    running = False


@app.on_event("startup")
@repeat_every(seconds=utils.get_interval("dm_influx"))
def influx():

    logger.info("Connecting to InfluxDB")
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
                .field("avg", thermal.avg).field("median", thermal.median).field("pixels", ",".join([str(int(x)) for x in thermal.pixels]))
            points.append(thermal_point)

        if points:

            logger.info("Sending data to InfluxDB")

            write_api = client.write_api()
            for point in points:
                write_api.write(bucket=utils.get_influx_bucket(), record=point)
            write_api.close()

            logger.info("Successfully sent data to InfluxDB")
