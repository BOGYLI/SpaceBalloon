import serial

KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'
KISS_DATA_FRAME = b'\x00'

def kiss_escape(data):
    """Escape special KISS characters in data."""
    data = data.replace(KISS_FEND, KISS_FESC + KISS_TFEND)
    data = data.replace(KISS_FESC, KISS_FESC + KISS_TFESC)
    return data

def construct_kiss_frame(aprs_packet):
    """Construct a KISS frame for an APRS packet."""
    kiss_frame = KISS_DATA_FRAME + aprs_packet
    kiss_frame = kiss_escape(kiss_frame)
    return KISS_FEND + kiss_frame + KISS_FEND

def main():
    # Replace '/dev/ttyUSB0' with the appropriate serial port for your device
    ser = serial.Serial('/dev/ttyUSB0', 115200)

    # Ensure RTS and DTR are set low
    ser.rts = False
    ser.dtr = False

    try:

        # Activate KISS Mode
        ser.write("INTFACE KISS\nRESET".encode('ascii'))

        # Construct an APRS packet
        src = "DN5WA-11"
        dest = "APRS"
        path = "WIDE1-1"
        info = "!4903.50N/07201.75W-Hello World"
        aprs_packet = f"{src}>{dest},{path}:{info}".encode('ascii')

        # Construct a KISS frame
        kiss_frame = construct_kiss_frame(aprs_packet)

        # Send the KISS frame over the serial connection
        ser.write(kiss_frame)

        print(f"Sent APRS packet: {aprs_packet.decode('ascii')}")

    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        ser.close()

if __name__ == "__main__":
    main()
