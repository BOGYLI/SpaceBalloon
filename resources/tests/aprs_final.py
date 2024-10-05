import binascii
import struct
import serial


# KISS protocol constants
KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'
KISS_DATA_FRAME = b'\x00'

# Convert to hex bytes
def to_hex_bytes(data):
    return " ".join(f"0x{data.hex()[i:i+2]}" for i in range(0, len(data.hex()), 2))

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

def encode_ax25_address(call, ssid):
    """Encodes a callsign and SSID into the AX.25 address format."""
    address = []
    
    # Callsign must be 6 characters long, pad with spaces if necessary
    call = call.ljust(6)
    
    # Shift left by 1 bit (as per AX.25 address field encoding)
    for char in call:
        address.append(ord(char) << 1)
    
    # Encode SSID correctly, bits 1-4 contain the SSID, bit 5 is always 1, and bits 6-7 are reserved
    ssid_byte = 0b01100000 | (ssid << 1)  # Bit 5 is set to 1, bits 6 and 7 are 0
    address.append(ssid_byte)
    
    return address

def construct_ax25_frame(source_call, source_ssid, dest_call, dest_ssid, information):
    """Constructs an AX.25 UI frame using the provided parameters."""
    
    # AX.25 control field for UI frame is always 0x03
    control_field = 0x03
    
    # Protocol ID for no layer 3 is 0xF0 (used in APRS, etc.)
    protocol_id = 0xF0
    
    # Encode the source and destination addresses
    dest_address = encode_ax25_address(dest_call, dest_ssid)
    source_address = encode_ax25_address(source_call, source_ssid)
    path1_address = encode_ax25_address("WIDE1", 1)
    path2_address = encode_ax25_address("WIDE2", 2)
    
    # Combine the frame components
    frame = dest_address + source_address + path1_address + path2_address
    
    # Append the control and protocol ID fields
    frame += [control_field, protocol_id]
    
    # Append the information field (message)
    frame += [ord(c) for c in information]
    
    # Convert to byte array
    frame_bytes = bytearray(frame)
    
    # Optionally, compute the CRC (Frame Check Sequence - FCS)
    fcs = binascii.crc_hqx(frame_bytes, 0xFFFF)
    frame_bytes += struct.pack('<H', fcs)  # Append the CRC (2 bytes)
    
    return frame_bytes

# Example APRS message
source_callsign = "DN5WA"
source_ssid = 11
dest_callsign = "APRS"
dest_ssid = 0
aprs_message = ">Space Balloon Test"

# Encode the AX.25 frame
ax25_frame = construct_ax25_frame(source_callsign, source_ssid, dest_callsign, dest_ssid, aprs_message)

# Output the AX.25 frame in hex format
print("AX.25 Frame (Hex):", to_hex_bytes(ax25_frame))

# Construct KISS frame
kiss_frame = construct_kiss_frame(ax25_frame)

# Print the constructed AX.25 frame in hex format
print(f"Constructed KISS Frame: {to_hex_bytes(kiss_frame)}")

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
