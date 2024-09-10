import paramiko
import PIL
import datetime
import influxdb_client
import os
import time


# Configuration
STORAGE_URL = os.getenv('STORAGE_URL') or "u421785.your-storagebox.de"
STORAGE_USER = os.getenv('STORAGE_USER') or "u421785"
STORAGE_PASSWORD = os.getenv('STORAGE_PASSWORD')
STORAGE_PATH = os.getenv('STORAGE_PATH') or "/System/thermal"

INFLUX_URL = os.getenv('INFLUX_URL') or f"https://influx.balloon.nikogenia.de"
ORG = os.getenv('INFLUX_ORG') or "makerspace"
BUCKET = os.getenv('INFLUX_BUCKET') or "balloon"
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')

INTERVAL = os.getenv('INTERVAL') or 10

if STORAGE_PASSWORD is None or INFLUX_TOKEN is None:
    print("Missing configuration via environment variables")
    exit(1)


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

    # Create SSH client
    print("Preparing SSH client")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Connect to Hetzner Storage Box
    print("Opening connection to Hetzner Storage Box")
    ssh_client.connect(hostname=STORAGE_URL, username=STORAGE_USER, password=STORAGE_PASSWORD)
    sftp = ssh_client.open_sftp()

    # Change directory while creating it if it does not exist
    try:
        sftp.chdir(STORAGE_PATH)
    except IOError:
        print("Creating storage directory")
        sftp.mkdir(STORAGE_PATH)
        sftp.chdir(STORAGE_PATH)

    # List files
    print("Listing files")
    files = sftp.listdir()
    ignore = []
    for file in files:
        if not file.endswith(".png"):
            continue

            ignore.append(file)

    # Close connection
    print("Closing connection")
    sftp.close()
    ssh_client.close()

    return

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
