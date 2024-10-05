import serial


def read_raw_serial_data(port):
    """Reads and prints all raw data from the serial port."""
    try:
        with serial.Serial(port, 115200, timeout=1) as ser:

            # Deactivate RTS and DTR
            ser.rts = False
            ser.dtr = False

            while True:
                # Read raw bytes from the serial port
                data = ser.read(ser.in_waiting or 1)

                if data:
                    # Print the raw data in both hex and string format
                    print(f"Raw data (hex): {data.hex()}")
                    print(f"Raw data (ascii): {data}")

    except serial.SerialException as e:
        print(f"Error reading from serial port: {e}")

read_raw_serial_data('COM3')
