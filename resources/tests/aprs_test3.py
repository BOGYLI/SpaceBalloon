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

def create_kiss_frame(data):
    FEND = b'\xC0'  # Frame End
    FESC = b'\xDB'  # Frame Escape
    TFEND = b'\xDC'  # Transposed Frame End
    TFESC = b'\xDD'  # Transposed Frame Escape

    frame = FEND
    frame += b'\x00'  # KISS-Kommando (0x00 für Daten senden)
    for byte in data:
        if byte == FEND[0]:
            frame += FESC + TFEND
        elif byte == FESC[0]:
            frame += FESC + TFESC
        else:
            frame += bytes([byte])
    frame += FEND
    return frame

def create_aprs_packet(source, destination, path, info):
    def encode_address(addr):
        return bytes([ord(char) << 1 for char in addr]) + b'\x60'  # Shift ASCII and set SSID to 0

    packet = encode_address(destination)
    packet += encode_address(source)

    for p in path:
        packet += encode_address(p)

    packet += b'\x03\xf0'  # Control and PID for APRS
    packet += info.encode('ascii')
    return packet

def send_aprs_packet(serial_port, baudrate, source, destination, path, info):
    ser = open_serial_connection(serial_port, baudrate)
    packet = create_aprs_packet(source, destination, path, info)
    kiss_frame = create_kiss_frame(packet)
    ser.write(kiss_frame)
    ser.close()

def format_aprs_info(gps_coords, temperature, humidity):
    lat, lon = gps_coords
    # APRS Positionsformat: !DDMM.mmN/DDDMM.mmE#
    aprs_position = f"!{lat:.2f}N/{lon:.2f}E#"
    # Zusätzliche Informationen wie Temperatur und Luftfeuchtigkeit
    aprs_info = f"{aprs_position}T:{temperature:.1f}C H:{humidity:.1f}%"
    return aprs_info

if __name__ == "__main__":
    # Beispielhafte Sensordaten
    gps_coords = (52.52, 13.405)  # GPS-Koordinaten (Breitengrad, Längengrad)
    temperature = 22.5  # Temperatur in Grad Celsius
    humidity = 60.0  # Luftfeuchtigkeit in Prozent

    source = 'DN5WA-11'
    destination = 'APRS'
    path = ['WIDE1-1', 'WIDE2-2']
    info = format_aprs_info(gps_coords, temperature, humidity)

    serial_port = '/dev/ttyUSB0'  # Passe diesen Port entsprechend deinem Setup an
    baudrate = 9600

    send_aprs_packet(serial_port, baudrate, source, destination, path, info)
    print("APRS Paket gesendet")
