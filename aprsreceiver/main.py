"""
APRS Receiver
"""


import serial
import requests
import influxdb_client
import os
import time


def write_to_influx(data):

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=INFLUX_URL, org=ORG, token=INFLUX_TOKEN) as client:

        points = [
            influxdb_client.Point("aprs_gps").time(int(data["time"]), "s").field("latitude", float(data["lat"])).field("longitude", float(data["lng"])).field("altitude", int(float(data["altitude"]))),
            influxdb_client.Point("aprs_data").time(int(data["time"]), "s").field("heading", int(data["course"])).field("speed", int(data["speed"]))
        ]

        write_api = client.write_api()
        for point in points:
            write_api.write(bucket=BUCKET, record=point)
        write_api.close()

        print("Successfully sent data to InfluxDB")


def main():
     
    while True:

        # Replace '/dev/ttyUSB0' with the appropriate serial port for your device
        print("Open serial connection")
        ser = serial.Serial('COM3', 115200)

        # Send the KISS frame over the serial connection
        data = ser.readline()
        print(data)
        print(data.decode('ascii'))
        print(data.decode('utf-8'))
    

        ser.close()


if __name__ == "__main__":

    main()
