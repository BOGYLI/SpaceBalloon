import utils
import time
import serial
import struct
import base64
import requests
import threading as th
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
import influxdb_client
from gpiozero import OutputDevice
from aprslib import *


SERVICE_MAP = ["balloon-adc.service",
               "balloon-cammanager.service",
               "balloon-climate.service",
               "balloon-co2.service",
               "balloon-datamanager.service",
               "balloon-gps.service",
               "balloon-magnet.service",
               "balloon-spectral.service",
               "balloon-system.service",
               "balloon-thermal.service",
               "balloon-webcam0.service",
               "balloon-webcam1.service",
               "balloon-webcam2.service",
               "balloon-webcam3.service",
               "balloon-webcam4.service"]


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
cool = False


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

    live_cam = -1
    video_cam0 = -1
    video_cam1 = -1
    video_cam2 = -1
    uptime = 0
    services = 0b0000000000000000
    try:
        status = requests.get("http://127.0.0.1/status").json()
        live_cam = status["live"]["webcam"]
        video_cam0 = status["video"]["webcam0"]
        video_cam1 = status["video"]["webcam1"]
        video_cam2 = status["video"]["webcam2"]
        uptime = status["uptime"]
        for i, service in enumerate(SERVICE_MAP):
            if service in status["services"]["active"]:
                services |= 1 << i
        services |= 1 << 15  # Set the last bit to indicate valid status data
    except requests.exceptions.RequestException:
        logger.warning("Failed to fetch status data")
    
    # Compress values to bytes
    gps_altitude = struct.pack('H', min(max(int(gps.altitude), 0), 65535))  # 2 bytes, 0-65535
    adc_uv = struct.pack('H', min(max(int(adc.uv * 1000), 0), 65535))  # 2 bytes, 0-65535
    adc_methane = struct.pack('H', min(max(int(adc.methane * 1000), 0), 65535))  # 2 bytes, 0-65535
    climate_pressure = struct.pack('H', min(max(int(climate.pressure), 0), 65535))  # 2 bytes, 0-65535
    climate_temp = struct.pack('b', min(max(int(climate.temp), -128), 127))  # 1 byte, -128-127
    climate_humidity = struct.pack('B', min(max(int(climate.humidity), 0), 255))  # 1 byte, 0-255
    climate_altitude = struct.pack('H', min(max(int(climate.altitude), 0), 65535))  # 2 bytes, 0-65535
    co2_co2 = struct.pack('H', min(max(int(co2.co2), 0), 65535))  # 2 bytes, 0-65535
    co2_voc = struct.pack('H', min(max(int(co2.voc), 0), 65535))  # 2 bytes, 0-65535
    system_cpu = struct.pack('B', min(max(int(system.cpu), 0), 255))  # 1 byte, 0-255
    system_memory = struct.pack('B', min(max(int(system.memory), 0), 255))  # 1 byte, 0-255
    system_temp = struct.pack('b', min(max(int(system.temp), -128), 127))  # 1 byte, -128-127
    system_sent = struct.pack('f', float(system.sent))  # 4 bytes, float
    system_received = struct.pack('f', float(system.received))  # 4 bytes, float
    thermal_min = struct.pack('b', min(max(int(thermal.min), -128), 127))  # 1 byte, -128-127
    thermal_max = struct.pack('b', min(max(int(thermal.max), -128), 127))  # 1 byte, -128-127
    thermal_avg = struct.pack('b', min(max(int(thermal.avg), -128), 127))  # 1 byte, -128-127
    thermal_median = struct.pack('b', min(max(int(thermal.median), -128), 127))  # 1 byte, -128-127
    live_cam = struct.pack('b', min(max(int(live_cam), -128), 127))  # 1 byte, -128-127
    video_cam0 = struct.pack('b', min(max(int(video_cam0), -128), 127))  # 1 byte, -128-127
    video_cam1 = struct.pack('b', min(max(int(video_cam1), -128), 127))  # 1 byte, -128-127
    video_cam2 = struct.pack('b', min(max(int(video_cam2), -128), 127))  # 1 byte, -128-127
    uptime = struct.pack('I', int(uptime))  # 4 bytes, 0-4294967295
    services = struct.pack('H', int(services))  # 2 bytes, 0-65535

    # Concatenate all data
    data = gps_altitude + adc_uv + adc_methane + climate_pressure + climate_temp + climate_humidity + \
        climate_altitude + co2_co2 + co2_voc + system_cpu + system_memory + system_temp + system_sent + system_received + \
        thermal_min + thermal_max + thermal_avg + thermal_median + live_cam + video_cam0 + video_cam1 + video_cam2 + \
        uptime + services

    logger.info(f"Unencoded comment data: {to_hex_bytes(data)} ({len(data)} bytes)")

    # Base64 encode the data
    return base64.b64encode(data).decode()

    
def aprs():
    
    last_sent = 0

    while running:

        try:

            # Open serial connection
            logger.info("Open serial connection")
            ser = serial.Serial(f'/dev/serial/by-id/{utils.get_aprs_device()}', 115200, timeout=2)

            # Ensure RTS and DTR are set low
            ser.rts = False
            ser.dtr = False

            # Receive buffer
            buffer = bytearray()

            while running:

                # Check if it is time to send an APRS packet
                if time.time() - last_sent > utils.get_interval("dm_aprs"):

                    last_sent = time.time()

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
                    aprs_message = f"!{aprs_lat}/{aprs_lon}OSpace Balloon: {aprs_comment}"
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

                # Temporary deactivation of receiving data
                # Sorry for everyone reading this
                # It isn't our fault but the weird behavior of the PicoAPRS V4
                # :/
                if False:

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

                time.sleep(0.2)
                
        except Exception as e:
            print(f"An unexpected error occurred in the APRS thread: {e}")
        finally:
            print(f"Closing serial connection")
            ser.close()

        if running:
            print("Retrying in 10 seconds")
            time.sleep(10)


def cooling():

    global cool

    last_update = 0

    while running:

        try:

            logger.info(f"Initialize cooling fan on GPIO pin {utils.get_cooling_fan()}")
            fan = OutputDevice(utils.get_cooling_fan(), initial_value=None)

            logger.info("Turn fan on for 5 seconds")
            fan.on()
            time.sleep(5)
            fan.off()
            logger.info("Fan turned off, testing complete")

            while running:

                if time.time() - last_update < utils.get_interval("dm_cooling"):
                    time.sleep(1)
                    continue

                last_update = time.time()

                if time.time() - thermal_updated < 120:
                    cool = thermal.min > utils.get_cooling_min_temp() and thermal.max > utils.get_cooling_max_temp()
                    logger.info(f"Cooling mode {'ON' if cool else 'OFF'} based on thermal {thermal.min:.1f} °C / {utils.get_cooling_min_temp()} °C and {thermal.max:.1f} °C / {utils.get_cooling_max_temp()} °C")
                elif time.time() - system_updated < 120:
                    logger.warning(f"No thermal data received since {time.time() - thermal_updated:.1f} seconds. Fallback to CPU temperature")
                    cool = system.temp > utils.get_cooling_cpu_temp()
                    logger.info(f"Cooling mode {'ON' if cool else 'OFF'} based on system {system.temp:.1f} °C / {utils.get_cooling_cpu_temp()} °C")
                else:
                    logger.warning("No thermal or system data received. Fallback to default value")
                    cool = False

                if cool != fan.value:
                    logger.info(f"Update cooling fan mode from {'ON' if fan.value else 'OFF'} to {'ON' if cool else 'OFF'}")
                    fan.value = cool

                utils.write_csv("datamanager", [int(cool)])

        except Exception as e:
            logger.error(f"An unexpected error occurred in the cooling thread: {e}")
        finally:
            logger.info("Closing cooling fan")
            fan.close()

        if running:
            print("Retrying in 10 seconds")
            time.sleep(10)


@app.on_event("startup")
def startup():

    th.Thread(target=aprs).start()
    th.Thread(target=cooling).start()


@app.on_event("shutdown")
def shutdown():

    global running
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
                          .field("temp", climate.temp).field("humidity", climate.humidity).field("altitude", climate.altitude)
                          .field("latitude", gps.latitude).field("longitude", gps.longitude))
        
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

        points.append(influxdb_client.Point("wifi_datamanager").time(int(time.time()), "s").field("cool", int(cool)))

        if points:

            logger.info("Sending data to InfluxDB")

            write_api = client.write_api()
            for point in points:
                write_api.write(bucket=utils.get_influx_bucket(), record=point)
            write_api.close()

            logger.info("Successfully sent data to InfluxDB")
