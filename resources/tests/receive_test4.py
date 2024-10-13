import serial
import re
import struct
import base64

# KISS protocol constants
KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'

# Your callsign to filter for
CALLSIGN = "DN5WA-2"

# Convert to hex bytes
def to_hex_bytes(data):
    return " ".join(f"0x{data.hex()[i:i+2]}" for i in range(0, len(data.hex()), 2))

# Function to decode the received message
def decode_sensor_data(encoded_data):
    """Decode the Base64 encoded sensor data back to its original values."""
    
    print(f"Decoding sensor data: {encoded_data}")

    # Decode the Base64 string
    data_bytes = base64.b64decode(encoded_data)

    print(f"Base64 decoded bytes: {to_hex_bytes(data_bytes)}")
    
    # Unpack the bytes into respective sensor values
    gps_altitude, adc_uv, adc_methane, climate_pressure, climate_temp, climate_humidity, climate_altitude, \
        co2_co2, co2_voc, magnet_heading, system_cpu, system_memory, system_temp, thermal_min, thermal_max, \
        thermal_avg, thermal_median = struct.unpack('HHHHbBHHHHBBbbbbb', data_bytes)

    # Create a dictionary or print the values directly
    sensor_data = {
        'GPS Altitude': gps_altitude,
        'ADC UV': adc_uv,
        'ADC Methane': adc_methane,
        'Climate Pressure': climate_pressure,
        'Climate Temperature': climate_temp,
        'Climate Humidity': climate_humidity,
        'Climate Altitude': climate_altitude,
        'CO2 CO2': co2_co2,
        'CO2 VOC': co2_voc,
        'Magnet Heading': magnet_heading,
        'System CPU': system_cpu,
        'System Memory': system_memory,
        'System Temperature': system_temp,
        'Thermal Min': thermal_min,
        'Thermal Max': thermal_max,
        'Thermal Average': thermal_avg,
        'Thermal Median': thermal_median
    }

    return sensor_data

# Unescape KISS special characters
def kiss_unescape(data):
    """Unescape KISS special characters in data."""
    data = data.replace(KISS_FESC + KISS_TFEND, KISS_FEND)
    data = data.replace(KISS_FESC + KISS_TFESC, KISS_FESC)
    return data

# Function to convert latitude and longitude from APRS format to decimal degrees
def convert_aprs_coords(coord_str, degrees_pos=2):
    """Convert latitude/longitude from APRS format to decimal degrees."""
    match = re.match(r'(\d{' + str(degrees_pos) + r'})(\d{2}\.\d+)([NSEW])', coord_str)
    if match:
        degrees = int(match.group(1))  # Degrees part
        minutes = float(match.group(2))  # Minutes part
        direction = match.group(3)  # N/S/E/W

        decimal_degrees = degrees + minutes / 60
        if direction in 'SW':  # South or West, make negative
            decimal_degrees *= -1

        return decimal_degrees
    return None

# Decode the AX.25 frame to extract the source, destination, path, and message
def decode_ax25_frame(frame):
    """Extracts the source, destination, path, and message from an AX.25 frame."""
    try:
        # Extract destination callsign (first 7 bytes)
        dest_call = "".join([chr(b >> 1) for b in frame[0:6]]).strip()
        dest_ssid = (frame[6] >> 1) & 0x0F
        dest_full = f"{dest_call}-{dest_ssid}"

        # Extract source callsign (next 7 bytes)
        source_call = "".join([chr(b >> 1) for b in frame[7:13]]).strip()
        source_ssid = (frame[13] >> 1) & 0x0F
        source_full = f"{source_call}-{source_ssid}"

        # Extract digipeater path (each address is 7 bytes)
        path_start = 14
        path = []
        while not frame[path_start + 6] & 0x01:  # Check if this is the last address
            digi_call = "".join([chr(b >> 1) for b in frame[path_start:path_start + 6]]).strip()
            digi_ssid = (frame[path_start + 6] >> 1) & 0x0F
            path.append(f"{digi_call}-{digi_ssid}")
            path_start += 7

        # Add the final digipeater in the path
        last_digi_call = "".join([chr(b >> 1) for b in frame[path_start:path_start + 6]]).strip()
        last_digi_ssid = (frame[path_start + 6] >> 1) & 0x0F
        path.append(f"{last_digi_call}-{last_digi_ssid}")

        # Control and protocol fields are after the addresses
        message_start = path_start + 7 + 2  # Control field (1 byte) + protocol ID (1 byte)
        message = frame[message_start:].decode('ascii', errors='ignore')

        return source_full, dest_full, path, message
    except Exception as e:
        print(f"Failed to decode AX.25 frame: {e}")
        return None, None, None, None

# Main function to read and filter for your callsign
def read_kiss_frames(port):
    """Reads incoming KISS frames, decodes them, and filters for a specific callsign."""
    try:
        with serial.Serial(port, 115200, timeout=1) as ser:
            buffer = bytearray()

            # Deactivate RTS and DTR
            ser.rts = False
            ser.dtr = False
            
            while True:
                byte = ser.read(1)
                print(f"Read byte: {byte.hex()}")
                if byte == KISS_FEND:
                    print("Received KISS frame FEND")
                    if buffer:
                        print(f"KISS frame complete: {buffer.hex()}")
                        # Unescape and process the frame
                        kiss_frame = kiss_unescape(buffer)
                        
                        # Skip the KISS command byte (first byte)
                        ax25_frame = kiss_frame[1:]

                        print(f"Data: {ax25_frame.decode("ascii")}")
                        buffer.clear()
                        continue
                        
                        # Decode AX.25 frame
                        source_call, dest_call, path, message = decode_ax25_frame(ax25_frame)
                        
                        print(f"Received message from {source_call}: {message}")
                        print(f"Destination: {dest_call}, Path: {path}")

                        if source_call and CALLSIGN in source_call:

                            # Extract and convert coordinates
                            lat_lon_pattern = r'!(\d{2}\d{2}\.\d+)([NS])\/(\d{3}\d{2}\.\d+)([EW])'
                            lat_lon_match = re.search(lat_lon_pattern, message)

                            if lat_lon_match:
                                latitude = convert_aprs_coords(lat_lon_match.group(1) + lat_lon_match.group(2), 2)
                                longitude = convert_aprs_coords(lat_lon_match.group(3) + lat_lon_match.group(4), 3)
                                print(f"Latitude: {latitude}, Longitude: {longitude}")  # Print coordinates

                            # Decode the sensor data
                            encoded_sensor_data = message.split(': ')[1]  # Assuming the sensor data is the last part of the message
                            sensor_data = decode_sensor_data(encoded_sensor_data)

                            # Print or process the decoded sensor data
                            print("Decoded Sensor Data:")
                            for key, value in sensor_data.items():
                                print(f"{key}: {value}")
                        
                        buffer.clear()
                else:
                    buffer += byte
                    
    except serial.SerialException as e:
        print(f"Error reading from serial port: {e}")

# Replace 'COM3' with your serial port for the ground Pico APRS
read_kiss_frames('COM3')
