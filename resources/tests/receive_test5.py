import serial
import time
import re
import struct
import base64

# Your callsign to filter for
CALLSIGN = "DN5WA-2"


# KISS protocol
KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'
KISS_DATA_FRAME = b'\x00'


def to_hex_bytes(data):
    """Converts data to hex bytes for display purposes."""

    return " ".join(f"0x{data.hex()[i:i+2]}" for i in range(0, len(data.hex()), 2))


def kiss_escape(data):
    """Escape special KISS characters in data."""

    data = data.replace(KISS_FEND, KISS_FESC + KISS_TFEND)
    data = data.replace(KISS_FESC, KISS_FESC + KISS_TFESC)
    return data


def kiss_unescape(data):
    """Unescape KISS special characters in data."""
    data = data.replace(KISS_FESC + KISS_TFEND, KISS_FEND)
    data = data.replace(KISS_FESC + KISS_TFESC, KISS_FESC)
    return data


def construct_kiss_frame(aprs_packet):
    """Construct a KISS frame for an APRS packet."""

    kiss_frame = KISS_DATA_FRAME + aprs_packet
    kiss_frame = kiss_escape(kiss_frame)
    return KISS_FEND + kiss_frame + KISS_FEND


def encode_gps_aprs(lat, lon):
    """Converts latitude and longitude to APRS format."""

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


def decode_gps_aprs(coord_str, degrees_pos=2):
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


def encode_ax25_address(call, ssid, is_last=False):
    """Encodes a callsign and SSID into the AX.25 address format."""

    address = []
    
    # Callsign must be 6 characters long, pad with spaces if necessary
    call = call.ljust(6)
    
    # Shift left by 1 bit (as per AX.25 address field encoding)
    for char in call:
        address.append(ord(char) << 1)
    
    # Encode SSID correctly, bits 1-4 contain the SSID, bit 5 is always 1, and bits 6-7 are reserved
    ssid_byte = 0b01100000 | (ssid << 1)  # Bit 5 is set to 1, bits 6 and 7 are 0

    if is_last:
        ssid_byte |= 0b00000001  # Set the last bit to 1 for the last address field

    address.append(ssid_byte)
    
    return address


def encode_ax25_frame(source_call, source_ssid, dest_call, dest_ssid, information):
    """Constructs an AX.25 UI frame using the provided parameters."""
    
    # AX.25 control field for UI frame is always 0x03
    control_field = 0x03
    
    # Protocol ID for no layer 3 is 0xF0 (used in APRS, etc.)
    protocol_id = 0xF0
    
    # Encode the source and destination addresses
    dest_address = encode_ax25_address(dest_call, dest_ssid)
    source_address = encode_ax25_address(source_call, source_ssid)
    path1_address = encode_ax25_address("WIDE1", 1)
    path2_address = encode_ax25_address("WIDE2", 2, True)
    
    # Combine the frame components
    frame = dest_address + source_address + path1_address + path2_address
    
    # Append the control and protocol ID fields
    frame += [control_field, protocol_id]
    
    # Append the information field (message)
    frame += [ord(c) for c in information]
    
    # Convert to byte array
    frame_bytes = bytearray(frame)
    
    return frame_bytes


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


def main():

    last_sent = 0

    while True:

        try:

            # Open serial connection
            print("Open serial connection")
            ser = serial.Serial('COM3', 115200, timeout=2)

            # Ensure RTS and DTR are set low
            ser.rts = False
            ser.dtr = False

            # Receive buffer
            buffer = bytearray()

            while True:

                # Check if it is time to send an APRS packet
                if time.time() - last_sent > 10:

                    last_sent = time.time()

                    # Construct an APRS packet
                    try:
                        aprs_src = "DN5WA"
                        aprs_src_ssid = 1
                        aprs_dest = "DN5WA"
                        aprs_dest_ssid = 2
                    except (IndexError, ValueError):
                        print("Invalid APRS source or destination")
                    aprs_lat, aprs_lon = encode_gps_aprs(20, 20)
                    aprs_comment = f">Space Balloon Test {int(time.time())}"
                    print(f"APRS packet data: {aprs_src}-{aprs_src_ssid} > {aprs_dest}-{aprs_dest_ssid} | {aprs_comment}")

                    # Construct a AX.25 frame
                    ax25_frame = encode_ax25_frame(aprs_src, aprs_src_ssid, aprs_dest, aprs_dest_ssid, aprs_comment)
                    print(f"AX.25 Frame: {to_hex_bytes(ax25_frame)}")

                    # Construct a KISS frame
                    kiss_frame = construct_kiss_frame(ax25_frame)
                    print(f"KISS Frame: {to_hex_bytes(kiss_frame)}")

                    # Send the KISS frame over the serial connection
                    print("Write data to APRS")
                    ser.write(kiss_frame)

                # Read data from the serial connection
                byte = ser.read(1)
                print(f"Read byte: {byte.hex()}")

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

                        if source_call and CALLSIGN in source_call and False:

                            # Extract and convert coordinates
                            lat_lon_pattern = r'!(\d{2}\d{2}\.\d+)([NS])\/(\d{3}\d{2}\.\d+)([EW])'
                            lat_lon_match = re.search(lat_lon_pattern, message)

                            if lat_lon_match:
                                latitude = decode_gps_aprs(lat_lon_match.group(1) + lat_lon_match.group(2), 2)
                                longitude = decode_gps_aprs(lat_lon_match.group(3) + lat_lon_match.group(4), 3)
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
                

        except Exception as e:
            print(f"An unexpected error occurred in the APRS thread: {e}")
            print("Retrying in 20 seconds")

        time.sleep(20)
            
main()
