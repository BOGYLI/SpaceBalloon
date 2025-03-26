import base64
from aprstools import *
import struct


def encode_gps_aprs_wrong(raw_value):
    """Converts latitude and longitude to APRS format."""

    degrees = int(raw_value[:2])
    minutes = float(raw_value[2:])
    lon = degrees + minutes / 60
    lon = lon - 6

    # Convert longitude to APRS format
    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60
    lon_hemi = 'E' if lon >= 0 else 'W'
    aprs_lon = f'{abs(lon_deg):03d}{lon_min:05.2f}{lon_hemi}'

    return aprs_lon


def encode_gps_aprs(raw_value):
    """Converts latitude and longitude to APRS format."""

    degrees = int(raw_value[:3])
    minutes = float(raw_value[3:])
    lon = degrees + minutes / 60

    # Convert longitude to APRS format
    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60
    lon_hemi = 'E' if lon >= 0 else 'W'
    aprs_lon = f'{abs(lon_deg):03d}{lon_min:05.2f}{lon_hemi}'

    return aprs_lon


print(encode_gps_aprs_wrong("00935.44963"))
print(encode_gps_aprs("00935.44963"))
print(encode_gps_aprs_wrong("01135.44963"))
print(encode_gps_aprs("01135.44963"))


-2 or 2
2

-35.29

lon = -35.29 / 60 + (-2)
lon = lon + 6
print(lon)


minutes = (lon - 1) * 60
print(minutes)


def foo(minutes):
    lon = minutes / 60 - 2
    lon = lon + 6
    minutes = (lon - 1) * 60
    coords = f'01{minutes}'
    degrees = int(coords[:3])
    minutes = float(coords[3:])
    degrees_dec = degrees + minutes / 60
    return degrees_dec


def yeah(lat_deg, lat_min, lon_min):
    lat = lat_deg + lat_min / 60
    lon = foo(lon_min)
    print(f"{lat}°N,{lon}°E")


yeah(48, 4.12, -38.89)
yeah(48, 4.87, -37.74)
yeah(48, 5.48, -36.51)
yeah(48, 5.33, -36.19)
yeah(48, 5.25, -35.99)
yeah(48, 5.31, -35.58)
yeah(48, 5.41, -35.29)







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

"""
print(decode_sensor_data("Ii4AAFgAyQDnALAn/QDbBDkeTqwmvk1NrnxNCD0pKP8CAP/WJgAA//8="))
print(decode_sensor_data("rSkAAFkA8QDlAIwjKQHZBD4eSWKFv03gaH9NBTglJf8DAf9OJwAA//8="))
print(decode_sensor_data("oSUAAFkAHQHqAIogYALcBE8gQ8fqwE1vGIFNAzMhIv8CBP/IJwAA//8="))
print(decode_sensor_data("GyAAAGEAYQHtBAUc3QLhBUIeOu7+wk1zKoNNAywdH/8DAP99KAAA//8="))
print(decode_sensor_data("CxLbF6AASAIAIKgQOgL2CEwhLdFqyU0YkIlNCCMYGv8CBP+YKgAA//8="))
print(decode_sensor_data("KgshBcEA3AIFI3gK1gEACkkgLRL6zE3QG41NDCIZGf8CAf/HKwAA//8="))
print(decode_sensor_data("kAeeD9QANAMMIDUHxAEGCzkeLg8Oz02mLY9NDyMZGv8DBP95LAAA//8="))
print(decode_sensor_data("UQbMBN8AVwMMHekF0wEHDD4dLyG5z00O2I9NECMaGv8CAP+2LAAA//8="))
"""

def decode_aprs_lon(aprs_lon):
    """Decodes APRS formatted longitude back to raw value."""
    lon_deg = int(aprs_lon[:3])
    lon_min = float(aprs_lon[3:8])
    lon_hemi = aprs_lon[8]

    lon = lon_deg + lon_min / 60
    if lon_hemi == 'W':
        lon = -lon

    return lon


def reverse_calculate_wrong_output(aprs_lon):
    """Reverse calculates the wrong output back to the corresponding input."""
    lon = decode_aprs_lon(aprs_lon)
    lon += 6  # Reverse the subtraction of 6 degrees

    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60

    raw_value = f'{abs(lon_deg):02d}{lon_min:07.4f}'
    return raw_value


# Example usage
wrong_output = "002-35.29W"
raw_value = reverse_calculate_wrong_output(wrong_output)
print(raw_value)  # Should print the corresponding input for the wrong output

