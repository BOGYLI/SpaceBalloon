import smbus2

# Define the I2C bus and address for the SAM-M8Q module
I2C_BUS = 1
GPS_ADDRESS = 0x42

# Create an I2C bus instance
bus = smbus2.SMBus(I2C_BUS)

def convert_to_degrees(raw_value):
    """Convert NMEA raw latitude/longitude format to decimal degrees."""
    degrees = int(raw_value[:2])
    minutes = float(raw_value[2:])
    return degrees + minutes / 60

def read_gps_data():
    try:
        # Read 32 bytes of data from the GPS module
        data = bus.read_i2c_block_data(GPS_ADDRESS, 0xFF, 32)  # 0xFF is the register address to read data
        
        # Filter out initialization bytes (255)
        filtered_data = [byte for byte in data if byte != 255]
        
        return filtered_data
    except Exception as e:
        print(f"Error reading GPS data: {e}")
        return None

def parse_nmea_sentence(data):
    try:
        # Convert data to ASCII characters
        nmea_sentence = ''.join(chr(byte) for byte in data)
        return nmea_sentence
    except Exception as e:
        print(f"Error parsing NMEA sentence: {e}")
        return None

def extract_lat_lon_alt(nmea_sentence):
    latitude = None
    longitude = None
    altitude = None

    if nmea_sentence.startswith("$GNRMC") or nmea_sentence.startswith("$GPRMC"):
        parts = nmea_sentence.split(',')
        if len(parts) > 6 and parts[3] and parts[5]:
            # Extract latitude and longitude
            latitude = convert_to_degrees(parts[3])
            if parts[4] == 'S':
                latitude = -latitude

            longitude = convert_to_degrees(parts[5])
            if parts[6] == 'W':
                longitude = -longitude

    elif nmea_sentence.startswith("$GNGGA") or nmea_sentence.startswith("$GPGGA"):
        parts = nmea_sentence.split(',')
        if len(parts) > 9 and parts[2] and parts[4] and parts[9]:
            # Extract latitude and longitude
            latitude = convert_to_degrees(parts[2])
            if parts[3] == 'S':
                latitude = -latitude

            longitude = convert_to_degrees(parts[4])
            if parts[5] == 'W':
                longitude = -longitude

            # Extract altitude
            altitude = float(parts[9])

    # Adjusting longitude by a certain amount
    if longitude is not None:
        longitude -= 6.0  # Adjust longitude by -6.0 degrees

    return latitude, longitude, altitude

def main():
    buffer = ""
    try:
        while True:
            # Read GPS data
            raw_data = read_gps_data()
            if raw_data:
                # Append new data to buffer
                nmea_sentence_part = parse_nmea_sentence(raw_data)
                if nmea_sentence_part:
                    buffer += nmea_sentence_part

                    # Split buffer into complete sentences
                    sentences = buffer.split('\n')
                    buffer = sentences[-1]  # Keep incomplete sentence in buffer

                    for sentence in sentences[:-1]:
                        # Extract and print latitude, longitude, and altitude
                        lat, lon, alt = extract_lat_lon_alt(sentence)
                        if lat is not None and lon is not None and alt is not None:
                            print(f"Adjusted Latitude: {lat}, Adjusted Longitude: {lon}, Altitude: {alt} meters")


    except KeyboardInterrupt:
        print("\nExiting the GPS script.")
        pass

if __name__ == "__main__":
    main()
