import requests
import influxdb_client
import struct
import os
import base64
import time


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

# Configuration
CALLSIGN_DM = os.getenv('CALLSIGN_DM') or "DN5WA-2"
CALLSIGN_PICO = os.getenv('CALLSIGN_PICO') or "DN5WA-11"
API_TOKEN = os.getenv('API_TOKEN')
APRS_URL = f"https://api.aprs.fi/api/get?name={CALLSIGN_DM},{CALLSIGN_PICO}&what=loc&apikey={API_TOKEN}&format=json"

INFLUX_URL = os.getenv('INFLUX_URL') or f"https://influx.balloon.nikogenia.de"
ORG = os.getenv('INFLUX_ORG') or "makerspace"
BUCKET = os.getenv('INFLUX_BUCKET') or "balloon"
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')

INTERVAL = int(os.getenv('INTERVAL')) or 60

if API_TOKEN is None or INFLUX_TOKEN is None:
    print("Missing configuration via environment variables")
    exit(1)

# State
live_cam = -1
video_cam0 = -1
video_cam1 = -1
video_cam2 = -1
uptime = 0
active_services = []
inactive_services = []


def to_hex_bytes(data):
    """Converts data to hex bytes for display purposes."""

    return " ".join(f"0x{data.hex()[i:i+2]}" for i in range(0, len(data.hex()), 2))


def write_to_influx(timestamp, data):

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=INFLUX_URL, org=ORG, token=INFLUX_TOKEN) as client:

        points = []

        for measurement in data:
            point = influxdb_client.Point(measurement).time(int(timestamp), "s")
            for field in data[measurement]:
                if data[measurement][field] != 0:
                    point.field(field, data[measurement][field])
            points.append(point)

        write_api = client.write_api()
        for point in points:
            write_api.write(bucket=BUCKET, record=point)
        write_api.close()

        print("Successfully sent data to InfluxDB")


def decode_sensor_data(encoded_data):
    """Decode the Base64 encoded sensor data back to its original values."""

    global live_cam, video_cam0, video_cam1, video_cam2, uptime
    
    print(f"Decoding sensor data: {encoded_data}")

    # Decode the Base64 string
    data_bytes = base64.b64decode(encoded_data)

    print(f"Base64 decoded bytes: {to_hex_bytes(data_bytes)} ({len(data_bytes)} bytes)")
    
    # Unpack the bytes into respective sensor values
    gps_altitude, adc_uv, adc_methane, climate_pressure, climate_temp, climate_humidity, climate_altitude, \
        co2_co2, co2_temp, co2_pressure, system_cpu, system_memory, system_temp, system_sent, system_received, \
        thermal_min, thermal_max, thermal_avg, thermal_median, live_cam, video_cam0, video_cam1, video_cam2, \
        uptime, services = struct.unpack('=HHHHbBHHbBBBbffbbbbbbbbIH', data_bytes)

    # Decode service state with bitwise operations
    active_services.clear()
    inactive_services.clear()
    for i, service in enumerate(SERVICE_MAP):
        if services & (1 << i):
            active_services.append(service)
        else:
            inactive_services.append(service)

    # Create a dictionary ready to be sent to InfluxDB
    sensor_data = {
        "aprs_gps": {
            "altitude": float(gps_altitude),
        },
        "aprs_adc": {
            "uv": adc_uv / 1000,
            "methane": adc_methane / 1000
        },
        "aprs_climate": {
            "pressure": climate_pressure,
            "temp": climate_temp,
            "humidity": climate_humidity,
            "altitude": climate_altitude
        },
        "aprs_co2": {
            "co2": co2_co2,
            "temp": co2_temp,
            "pressure": co2_pressure
        },
        "aprs_system": {
            "cpu": system_cpu,
            "memory": system_memory,
            "temp": system_temp,
            "sent": int(system_sent),
            "received": int(system_received)
        },
        "aprs_thermal": {
            "min": thermal_min,
            "max": thermal_max,
            "avg": thermal_avg,
            "median": thermal_median
        }
    }

    return sensor_data


def parse_entry(entry):

    print(f"Received message from {entry['srccall']}: {entry['comment']}")
    print(f"Destination: {entry['dstcall'] or '-'}, Path: {entry['path']}")
    print(f"Time: {entry['time']}")

    if entry["name"] == CALLSIGN_DM:

        print("Parsing datamanager packet")

        data = decode_sensor_data(entry["comment"].split(": ")[1])
        data["aprs_gps"]["latitude"] = float(entry["lat"])
        data["aprs_gps"]["longitude"] = float(entry["lng"])

        write_to_influx(entry["time"], data)

        print("System Status:")
        print(f"  Live Camera: {live_cam}")
        print(f"  Video Camera 0: {video_cam0}")
        print(f"  Video Camera 1: {video_cam1}")
        print(f"  Video Camera 2: {video_cam2}")
        print(f"  Uptime: {uptime}")
        print("  Services:")
        print(f"    Active: {active_services}")
        print(f"    Inactive: {inactive_services}")

    elif entry["name"] == CALLSIGN_PICO:

        print("Parsing PicoAPRS packet")

        data = {
            "aprs_pico": {
                "latitude": float(entry["lat"]),
                "longitude": float(entry["lng"]),
                "altitude": float(entry["altitude"]),
                "course": int(entry["course"]),
                "speed": float(entry["speed"])
            }
        }

        write_to_influx(entry["time"], data)

    else:
        print("No matching callsign found")


def main():

    while True:

        print("Fetching data from APRS")
        response = requests.get(APRS_URL)

        if response.status_code == 200:
            data = response.json()
            if data["result"] == "ok":
                print("Received data from APRS")
                print(f"Raw data: {data}")
                for entry in data["entries"]:
                    try:
                        parse_entry(entry)
                    except Exception as e:
                        print(f"Error parsing entry: {e}")
                        print(entry)
            else:
                print("Error fetching data from APRS")
                print(data)
        else:
            print("Error fetching data from APRS")
            print(f"{response.status_code}: {response.text}")

        print(f"Cycle done, waiting {INTERVAL} seconds until next cycle")
        
        time.sleep(INTERVAL)


if __name__ == "__main__":

    main()
