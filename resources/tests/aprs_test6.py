import binascii
import struct
import serial


# KISS protocol constants
KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'
KISS_DATA_FRAME = b'\x00'

# Escape special KISS characters in data
def kiss_escape(data):
    """Escape special KISS characters in data."""
    data = data.replace(KISS_FEND, KISS_FESC + KISS_TFEND)
    data = data.replace(KISS_FESC, KISS_FESC + KISS_TFESC)
    return data

# Construct a KISS frame for the AX.25 packet
def construct_kiss_frame(ax25_packet):
    """Construct a KISS frame for an AX.25 packet."""
    kiss_frame = KISS_DATA_FRAME + kiss_escape(ax25_packet)
    return KISS_FEND + kiss_frame + KISS_FEND

# Helper to encode callsign
def encode_callsign(callsign, ssid):
    """Encodes a callsign and SSID into AX.25 format (6-bit ASCII, 7 bytes total)."""
    callsign = callsign.ljust(6)  # Pad callsign to 6 characters
    encoded = ''.join([chr(ord(char) << 1) for char in callsign])  # Shift ASCII characters by 1 bit
    ssid_byte = (ssid & 0x0F) << 1 | 0x60  # Add SSID with bit-shifting
    return encoded + chr(ssid_byte)

# Example to encode an APRS message into AX.25
def encode_ax25_frame(source, source_ssid, dest, dest_ssid, aprs_payload):
    """Encodes an APRS string into an AX.25 frame."""
    
    # Encode source and destination callsigns
    source_encoded = encode_callsign(source, source_ssid)
    dest_encoded = encode_callsign(dest, dest_ssid)
    
    # Path (no digipeaters used here for simplicity)
    control_field = b'\x03'  # Control field for UI frames
    protocol_id = b'\xF0'    # No layer 3 protocol
    
    # Frame information
    information_field = aprs_payload.encode('ascii')
    
    # Frame without FCS
    ax25_frame = dest_encoded.encode('latin1') + source_encoded.encode('latin1') + control_field + protocol_id + information_field
    
    # Calculate CRC-16 for AX.25
    fcs = binascii.crc_hqx(ax25_frame, 0xFFFF)
    
    # Append FCS to the frame in little-endian order
    ax25_frame += struct.pack('<H', fcs)
    
    # Add start and end flags
    ax25_frame = b'\x7E' + ax25_frame + b'\x7E'
    
    return ax25_frame

# Example APRS message
source_callsign = "DN5WA"
source_ssid = 11
dest_callsign = "APRS"
dest_ssid = 0
aprs_message = ">Space Balloon Test"

# Encode the AX.25 frame
ax25_frame = encode_ax25_frame(source_callsign, source_ssid, dest_callsign, dest_ssid, aprs_message)

# Output the AX.25 frame in hex format
print("AX.25 Frame (Hex):", ax25_frame.hex())

# Construct KISS frame
kiss_frame = construct_kiss_frame(ax25_frame)

# Print the constructed AX.25 frame in hex format
print(f"Constructed KISS Frame: {kiss_frame.hex()}")

# Send the KISS frame over the serial connection
try:
    # Replace '/dev/ttyUSB0' with the appropriate serial port for your device
    with serial.Serial('/dev/ttyUSB0', 115200) as ser:
        ser.rts = False  # Ensure RTS and DTR are set low
        ser.dtr = False

        # Send the KISS frame
        ser.write(kiss_frame)
        print("KISS frame sent successfully!")

except serial.SerialException as e:
    print(f"Error sending KISS frame: {e}")
