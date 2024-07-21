import requests
import influxdb_client
import os
import time


CALLSIGN = os.getenv('CALLSIGN') or "DN5WA-11"
API_TOKEN = os.getenv('API_TOKEN')
APRS_URL = f"https://api.aprs.fi/api/get?name={CALLSIGN}&what=loc&apikey={API_TOKEN}&format=json"

INFLUX_URL = os.getenv('INFLUX_URL') or f"https://influx.balloon.nikogenia.de"
ORG = os.getenv('INFLUX_ORG') or "makerspace"
BUCKET = os.getenv('INFLUX_BUCKET') or "balloon"
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')

INTERVAL = os.getenv('INTERVAL') or 10


def write_to_influx(data):

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=INFLUX_URL, org=ORG, token=INFLUX_TOKEN) as client:

        points = [
            influxdb_client.Point("aprs_gps").time(int(data["time"]), "s").field("latitude", float(data["lat"])).field("longitude", float(data["lng"])).field("altitude", data["altitude"]),
            influxdb_client.Point("aprs_data").time(int(data["time"]), "s").field("heading", data["course"]).field("speed", data["speed"])
        ]

        write_api = client.write_api()
        for point in points:
            write_api.write(bucket=BUCKET, record=point)
        write_api.close()

        print("Successfully sent data to InfluxDB")


def main():

    while True:

        print("Fetching data from APRS")
        response = requests.get(APRS_URL)

        if response.status_code == 200:
            data = response.json()
            if data["result"] == "ok":
                print("Received data from APRS")
                for loc in data["entries"]:
                    print(f"Data: {loc}")
                    write_to_influx(loc)
            else:
                print("Error fetching data from APRS")
                print(data)
        else:
            print("Error fetching data from APRS")
            print(f"{response.status_code}: {response.text}")

        time.sleep(INTERVAL)


if __name__ == "__main__":

    main()
