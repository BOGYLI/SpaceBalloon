"""
APRS Receiver
"""


import time
import struct
import os
import sys
import base64
import socket
from getpass import getpass
import threading as th
from fastapi import FastAPI
import paramiko
import influxdb_client
from aprstools import *


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


# Initialize FastAPI
app = FastAPI(title="APRS Receiver", description="APRS ground station receiving packets", version="1.0")
running = True

# Config
influx_url = "https://influx.balloon.nikogenia.de"
influx_org = "makerspace"
influx_bucket = "balloon"
try:
    with open("key.txt", "r") as f:
        influx_token = f.read().strip()
except OSError:
    influx_token = ""
kiss_server = "127.0.0.1:8100"
aprs_dm_src = "DN5WA-2"
aprs_pico_src = "DN5WA-11"
ssh_active = True
ssh_host = "192.168.25.2"
ssh_port = 22
ssh_user = "admin"
try:
    with open("pass.txt", "r") as f:
        ssh_pass = f.read().strip()
except OSError:
    ssh_pass = ""

print("Space Balloon APRS Receiver")
print("===========================")
print("")

print("Login")
print("-----")
print("")

if "-c" in sys.argv or "--custom" in sys.argv:
    aprs_dm_src = input("APRS Source Data Manager (empty for default): ").strip() or aprs_dm_src
    aprs_pico_src = input("APRS Source PicoAPRS (empty for default): ").strip() or aprs_pico_src
    kiss_server = input("Kiss Server (empty for default): ").strip() or kiss_server
    influx_url = input("Influx URL (empty for default): ").strip() or influx_url
    influx_org = input("Influx Organisation (empty for default): ").strip() or influx_org
    influx_bucket = input("Influx Bucket (empty for default): ").strip() or influx_bucket
    ssh_active = input("Activate MikroTik SSH monitoring? (y/n): ").strip().lower() == "y"
    ssh_host = input("MikroTik SSH Host (empty for default): ").strip() or ssh_host
    ssh_port = input("MikroTik SSH Port (empty for default): ").strip() or ssh_port
    ssh_user = input("MikroTik SSH User (empty for default): ").strip() or ssh_user

old_token = influx_token
if influx_token:
    print("Influx Token already configured")
    change = input("Change it? (y/n): ").strip().lower()
if not influx_token or change == "y":
    influx_token = getpass("Influx Token: ").strip()
if not influx_token:
    print("Empty token detected, exiting")
    sys.exit(1)
if old_token != influx_token:
    save = input("Save token to key.txt? (y/n): ").strip().lower()
    if save == "y":
        with open("key.txt", "w") as f:
            f.write(influx_token)
        print(f"Token saved to {os.path.abspath('key.txt')}")

if ssh_active:
    old_pass = ssh_pass
    if ssh_pass:
        print("MikroTik SSH Password already configured")
        change = input("Change it? (y/n): ").strip().lower()
    if not ssh_pass or change == "y":
        ssh_pass = getpass("MikroTik SSH Password: ").strip()
    if not ssh_pass:
        print("Empty password detected, exiting")
        sys.exit(1)
    if old_pass != ssh_pass:
        save = input("Save password to pass.txt? (y/n): ").strip().lower()
        if save == "y":
            with open("pass.txt", "w") as f:
                f.write(ssh_pass)
            print(f"Password saved to {os.path.abspath('pass.txt')}")

if len(kiss_server.split(":")) != 2:
    print("Invalid Kiss Host, exiting")
    sys.exit(1)
try:
    kiss_host, kiss_port = kiss_server.split(":")
    kiss_port = int(kiss_port)
except ValueError:
    print("Invalid Kiss Host, exiting")
    sys.exit(1)
print("")

print("Configuration:")
print(f"APRS Source Data Manager: {aprs_dm_src}")
print(f"APRS Source PicoAPRS: {aprs_pico_src}")
print(f"Influx URL: {influx_url} (organisation: {influx_org}, bucket: {influx_bucket}, token: {'*' * len(influx_token)})")
print(f"Kiss Server: {kiss_host}:{kiss_port}")
if ssh_active:
    print(f"MikroTik SSH: {ssh_host}:{ssh_port} (user: {ssh_user}, password: {'*' * len(ssh_pass)})")
print("")

live_cam = -1
video_cam0 = -1
video_cam1 = -1
video_cam2 = -1
uptime = 0
active_services = []
inactive_services = []


@app.get("/status")
def route_status():
    return {
        "live": {
            "webcam": live_cam
        },
        "video": {
            "webcam0": video_cam0,
            "webcam1": video_cam1,
            "webcam2": video_cam2
        },
        "uptime": uptime,
        "services": {
            "active": active_services,
            "inactive": inactive_services,
            "alive": len(active_services),
            "dead": len(inactive_services)
        }
    }


def write_to_influx(data):

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=influx_url, org=influx_org, token=influx_token) as client:

        points = []

        for measurement in data:
            point = influxdb_client.Point(measurement).time(int(time.time()), "s")
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


def decode_wifi_data(command_output):

    data = {}
    lines = command_output.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        matches = re.findall(r'(\S+)=("[^"]*"|\S+)', line)
        for key, value in matches:

            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            
            if key in {"packets", "bytes", "frames", "frame-bytes"}:
                rx, tx = value.split(",")
                data[key] = {"rx": int(rx), "tx": int(tx)}
            elif key == "uptime":
                    hours = 0
                    minutes = 0
                    if "h" in value:
                        hours, value = value.split("h")
                    if "m" in value:
                        minutes, value = value.split("m")
                    seconds = value.removesuffix("s")
                    data[key] = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            else:
                try:
                    value = value.removesuffix("dBm").removesuffix("dB").removesuffix("%")
                    value = int(value)
                except ValueError:
                    pass
                
                data[key] = value
        
        if "strength-at-rates=" in line:
            rates = re.findall(r'(-?\d+dBm@[^\s]+ \d+[ms]+)', line)
            if rates:
                data["strength-at-rates"] = rates
    
    return data


def aprs():
    
    while running:

        try:

            # Open socket connection
            print("Open socket connection")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((kiss_host, kiss_port))
            s.settimeout(2)

            # Receive buffer
            buffer = bytearray()

            while running:

                # Read data from the socket connection
                try:
                    byte = s.recv(1)
                except socket.timeout:
                    continue

                if byte:
                    print(f"Received byte: {to_hex_bytes(byte)}")
                else:
                    continue

                if byte == KISS_FEND:

                    print("Received KISS frame FEND")
                    if buffer:

                        print(f"KISS frame complete: {to_hex_bytes(buffer)}")
                        kiss_frame = kiss_unescape(buffer)
                        
                        # Skip the KISS command byte (first byte)
                        ax25_frame = kiss_frame[1:]
                        
                        # Decode AX.25 frame
                        source_call, dest_call, path, message = decode_ax25_frame(ax25_frame)
                        
                        print(f"Received message from {source_call}: {message}")
                        print(f"Destination: {dest_call}, Path: {path}")

                        if source_call == aprs_dm_src:

                            print("Decoding datamanager packet")

                            # Decode the sensor data
                            encoded_sensor_data = message.split(': ')[1]  # Assuming the sensor data is the last part of the message
                            sensor_data = decode_sensor_data(encoded_sensor_data)

                            # Extract and convert coordinates
                            lat_lon_pattern = r'!(\d{2}\d{2}\.\d+)([NS])\/(\d{3}\d{2}\.\d+)([EW])'
                            lat_lon_match = re.search(lat_lon_pattern, message)

                            if lat_lon_match:
                                latitude = decode_gps_aprs(lat_lon_match.group(1) + lat_lon_match.group(2), 2)
                                longitude = decode_gps_aprs(lat_lon_match.group(3) + lat_lon_match.group(4), 3)
                                print(f"Latitude: {latitude}, Longitude: {longitude}")  # Print coordinates
                                sensor_data["aprs_gps"]["latitude"] = latitude
                                sensor_data["aprs_gps"]["longitude"] = longitude
                                sensor_data["aprs_climate"]["latitude"] = latitude
                                sensor_data["aprs_climate"]["longitude"] = longitude
                            
                            write_to_influx(sensor_data)

                        elif source_call == aprs_pico_src and message.startswith("`"):

                            print("Decoding PicoAPRS packet")

                            packet_data = parse_mice(dest_call, message[1:])[1]
                            print(f"Decoded data: {packet_data}")
                            measurement_data = {
                                "aprs_pico": {
                                    "latitude": packet_data["latitude"],
                                    "longitude": packet_data["longitude"],
                                    "altitude": float(packet_data["altitude"]),
                                    "speed": packet_data["speed"],
                                    "course": packet_data["course"],
                                }
                            }
                            write_to_influx(measurement_data)
                        
                        buffer.clear()

                else:
                    buffer += byte

        except Exception as e:
            print(f"An unexpected error occurred in the APRS thread: {e}")
        finally:
            print(f"Closing socket connection")
            s.close()

        if running:
            print("Retrying in 10 seconds")
            time.sleep(10)


def ssh():
    
    while running:

        try:

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ssh_host, port=ssh_port, username=ssh_user, password=ssh_pass)
            print(f"Connected to '{ssh_host}' as '{ssh_user}'")

            while running:

                command = "/interface wireless registration-table print stats"
                response = client.exec_command(command)[1].read().decode("utf-8")

                wifi_data = decode_wifi_data(response)

                if wifi_data:

                    rx_signal = wifi_data.get("signal-strength", 0)
                    rx_signal_a0 = wifi_data.get("signal-strength-ch0", 0)
                    rx_signal_a1 = wifi_data.get("signal-strength-ch1", 0)
                    tx_signal = wifi_data.get("tx-signal-strength", 0)
                    tx_signal_a0 = wifi_data.get("tx-signal-strength-ch0", 0)
                    tx_signal_a1 = wifi_data.get("tx-signal-strength-ch1", 0)
                    rx_quality = wifi_data.get("rx-ccq", 0)
                    tx_quality = wifi_data.get("tx-ccq", 0)
                    tx_packets = wifi_data.get("packets", {}).get("tx", 0)
                    rx_packets = wifi_data.get("packets", {}).get("rx", 0)
                    tx_bytes = wifi_data.get("bytes", {}).get("tx", 0)
                    rx_bytes = wifi_data.get("bytes", {}).get("rx", 0)
                    noise = wifi_data.get("signal-to-noise", 0)
                    uptime = wifi_data.get("uptime", 0)

                    print("WiFi stats:")
                    print(f"RX {rx_signal}dBm {rx_quality}% {rx_packets} packets {rx_bytes} bytes")
                    print(f"TX {tx_signal}dBm {tx_quality}% {tx_packets} packets {tx_bytes} bytes")

                    data = {
                        "wifi_stats": {
                            "rx_signal": rx_signal,
                            "rx_signal_a0": rx_signal_a0,
                            "rx_signal_a1": rx_signal_a1,
                            "tx_signal": tx_signal,	
                            "tx_signal_a0": tx_signal_a0,
                            "tx_signal_a1": tx_signal_a1,
                            "rx_quality": rx_quality,
                            "tx_quality": tx_quality,
                            "tx_packets": tx_packets,
                            "rx_packets": rx_packets,
                            "tx_bytes": tx_bytes,
                            "rx_bytes": rx_bytes,
                            "noise": noise,
                            "uptime": uptime
                        }
                    }

                    write_to_influx(data)

                time.sleep(5)

        except Exception as e:
            print(f"An unexpected error occurred in the SSH thread: {e}")
        finally:
            print(f"Closing SSH connection")
            client.close()

        if running:
            print("Retrying in 10 seconds")
            time.sleep(10)


@app.on_event("startup")
def start_aprs():

    th.Thread(target=aprs).start()
    th.Thread(target=ssh).start()


@app.on_event("shutdown")
def stop_aprs():

    global running
    running = False
