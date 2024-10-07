import serial
import time


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


counter = 0

while True:

    # Data
    data = f"Space Balloon PicoAPRS Transmission Test #{counter}".encode('ascii')

    # Construct KISS frame
    kiss_frame = construct_kiss_frame(data)

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

    time.sleep(10)
