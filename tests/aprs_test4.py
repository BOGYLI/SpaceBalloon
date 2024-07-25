import serial
import time

def open_serial_connection(port, baudrate):
    ser = serial.Serial(
        port=port,
        baudrate=baudrate,
        timeout=1,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    return ser

def send_kiss_command(serial_port, baudrate, command):
    ser = open_serial_connection(serial_port, baudrate)
    FEND = b'\xC0'  # Frame End
    ser.write(FEND + command + FEND)
    ser.close()

def main():
    serial_port = '/dev/ttyUSB0'  # Passe diesen Port entsprechend deinem Setup an
    baudrate = 9600

    # Beispiel für ein KISS-Kommando zum Aktivieren des KISS-Modus
    KISS_ON = b'\xFF\x01'
    
    send_kiss_command(serial_port, baudrate, KISS_ON)
    print("KISS-Modus aktiviert")

if __name__ == "__main__":
    main()
