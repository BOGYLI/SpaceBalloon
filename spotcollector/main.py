import requests
import xml.etree.ElementTree as ET
import os
import time
from influxdb_client import InfluxDBClient, Point, WriteOptions


# Configuration
feed_url = os.getenv('FEED_URL') or "https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/1kkyoG79tTlJqnS3lrCl6G9dT5x4QL2YP/message.xml"
feed_password = os.getenv('FEED_PASSWORD')
influxdb_token = os.getenv('INFLUX_TOKEN')
influxdb_org = os.getenv('INFLUX_ORG') or "makerspace"
influxdb_bucket = os.getenv('INFLUX_BUCKET') or "balloon"
influxdb_url = os.getenv('INFLUX_URL') or "https://influx.balloon.nikogenia.de"
if feed_password is None or influxdb_token is None:
    print("Missing configuration via environment variables")
    exit(1)

INTERVAL = int(os.getenv('INTERVAL')) or 60


while True:

    # request data from feed
    print("Fetching data from SPOT feed")
    response = requests.get(f"{feed_url}?feedPassword={feed_password}")
    response.raise_for_status()  # Fehlermeldung bei Anfragenfehler

    # parse XML data
    root = ET.fromstring(response.content)
    messages = root.findall('.//message')

    if messages:

        print(f"Found {len(messages)} messages in feed")

        # create InfluxDB client
        print("Opening InfluxDB connection")
        client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
        write_api = client.write_api(write_options=WriteOptions(batch_size=1))

        # parse XML data and write to InfluxDB
        for message in messages:

            measuretime = message.find('dateTime').text
            latitude = message.find('latitude').text
            longitude = message.find('longitude').text
            altitude = message.find('altitude').text

            point = Point("spot_gps") \
                .field("latitude", float(latitude)) \
                .field("longitude", float(longitude)) \
                .field("altitude", float(altitude)) \
                .time(measuretime)

            try:
                print(f"Writing data {latitude}, {longitude}, {altitude} from {measuretime} to InfluxDB")
                write_api.write(bucket=influxdb_bucket, org=influxdb_org, record=point)
            except Exception as e:
                print("Error writing data to InfluxDB: ", e)
                continue

        write_api.close()
        client.close()

    else:
        print("No messages found in feed")

    print(f"Cycle done, waiting {INTERVAL} seconds until next cycle")
    
    time.sleep(INTERVAL)
