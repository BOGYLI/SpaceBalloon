import serial

# KISS protocol constants
KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'

# Your callsign to filter for
CALLSIGN = "DN5WA-2"

# Unescape KISS special characters
def kiss_unescape(data):
    """Unescape KISS special characters in data."""
    data = data.replace(KISS_FESC + KISS_TFEND, KISS_FEND)
    data = data.replace(KISS_FESC + KISS_TFESC, KISS_FESC)
    return data

# Decode the AX.25 frame to extract the source, destination, and path
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

        # Extract digipeater path (each address is 7 bytes, check if it's the last one with the 0x01 bit)
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
                        
                        # Decode AX.25 frame
                        source_call, dest_call, path, message = decode_ax25_frame(ax25_frame)
                        
                        if source_call and CALLSIGN in source_call:
                            print(f"Received message from {source_call}: {message}")
                            print(f"Destination: {dest_call}, Path: {path}")
                        
                        buffer.clear()
                else:
                    buffer += byte
                    
    except serial.SerialException as e:
        print(f"Error reading from serial port: {e}")

# Replace '/dev/ttyUSB0' with your serial port for the ground Pico APRS
read_kiss_frames('COM3')