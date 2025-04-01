import time
import struct
import os
import sys
import base64
from getpass import getpass
import influxdb_client
from aprstools import *
from datetime import datetime
from zoneinfo import ZoneInfo

# Config
influx_url = "https://influx.balloon.nikogenia.de"
influx_org = "makerspace"
influx_bucket = "balloon"
influx_token = ""

print("Space Balloon APRS Reconstruction")
print("=================================")
print("")

print("Login")
print("-----")
print("")

influx_url = input("Influx URL (empty for default): ").strip() or influx_url
influx_org = input("Influx Organisation (empty for default): ").strip() or influx_org
influx_bucket = input("Influx Bucket (empty for default): ").strip() or influx_bucket
influx_token = getpass("Influx Token: ").strip()


def write_to_influx(data, pointtime):

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=influx_url, org=influx_org, token=influx_token) as client:

        points = []

        for measurement in data:
            point = influxdb_client.Point(measurement).time(pointtime, "s")
            for field in data[measurement]:
                if data[measurement][field] != 0:
                    point.field(field, data[measurement][field])
            points.append(point)

        write_api = client.write_api()
        for point in points:
            write_api.write(bucket=influx_bucket, record=point)
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


if __name__ == '__main__':
                            
    print("Enter the path to the file:")
    path = input("> ").strip()
    if not os.path.exists(path):
        print("File not found")
        sys.exit(1)

    with open(path, 'r') as file:
                            
        for line in file:

            repair_gps = False
                            
            if line.startswith("#"):
                repair_gps = True
                line = line[1:]

            timestamp = line[:19]
            path, coords, message = line[24:].split(':')

            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            aware_dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
            utc_dt = aware_dt.astimezone(ZoneInfo("UTC"))
            unix_timestamp = int(utc_dt.timestamp())

            print(timestamp, path, coords, message, unix_timestamp)

            # Decode the sensor data
            sensor_data = decode_sensor_data(message[1:])

            # Extract and convert coordinates
            lat_lon_pattern = r'!(\d{2}\d{2}\.\d+)([NS])\/(\d{3}\d{2}\.\d+)([EW])'
            lat_lon_match = re.search(lat_lon_pattern, coords)

            if lat_lon_match:
                if repair_gps:
                    minutes = -float(lat_lon_match.group(3)[3:])
                    lon = minutes / 60 - 2
                    lon = lon + 6
                    minutes = (lon - 1) * 60
                    raw_longitude = f'01{minutes}E'
                else:
                    raw_longitude = lat_lon_match.group(3) + lat_lon_match.group(4)
                latitude = decode_gps_aprs(lat_lon_match.group(1) + lat_lon_match.group(2), 2)
                longitude = decode_gps_aprs(raw_longitude, 3)
                print(f"Latitude: {latitude}, Longitude: {longitude}")  # Print coordinates
                sensor_data["aprs_gps"]["latitude"] = latitude
                sensor_data["aprs_gps"]["longitude"] = longitude
                sensor_data["aprs_climate"]["latitude"] = latitude
                sensor_data["aprs_climate"]["longitude"] = longitude
            
            write_to_influx(sensor_data, unix_timestamp)

