import paramiko
import numpy as np
import PIL
import datetime
import matplotlib.pyplot as plt
import influxdb_client
import os
import time
import subprocess


# Configuration
STORAGE_URL = os.getenv('STORAGE_URL') or "u421785.your-storagebox.de"
STORAGE_USER = os.getenv('STORAGE_USER') or "u421785"
STORAGE_PASSWORD = os.getenv('STORAGE_PASSWORD')
STORAGE_PATH = os.getenv('STORAGE_PATH') or "System/thermal"

INFLUX_URL = os.getenv('INFLUX_URL') or f"https://influx.balloon.nikogenia.de"
ORG = os.getenv('INFLUX_ORG') or "makerspace"
BUCKET = os.getenv('INFLUX_BUCKET') or "balloon"
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')

INTERVAL = os.getenv('INTERVAL') or 5

TEMP_MIN = os.getenv('TEMP_MIN') or 5
TEMP_MAX = os.getenv('TEMP_MAX') or 85

if STORAGE_PASSWORD is None or INFLUX_TOKEN is None:
    print("Missing configuration via environment variables")
    exit(1)


def list_files(sftp):

    print("Listing files")
    files = sftp.listdir()
    result = []

    for file in files:
        if not file.endswith(".png"):
            continue
        try:
            year, month, day, hour, minute, second = [int(x) for x in file.split(".")[0].split("-")]
            result.append(datetime.datetime(year, month, day, hour, minute, second))
        except ValueError:
            print(f"Failed to parse filename: {file}")
    print(f"Found {len(result)} already rendered files")

    return result


def convert_color(temp):

    # Normalize temperature
    norm = (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)

    # Convert to RGB
    colormap = plt.get_cmap("jet")
    color = colormap(norm)

    # Convert RGBA to RGB and scale to 0-255
    return tuple((np.array(color[:3]) * 255).astype(int))


def parse_image(point):

    # Parse the data
    pixels = point.get_value()
    pixels = pixels.split(",")
    pixels = [int(x) for x in pixels]

    # Create the image
    image = PIL.Image.new("RGB", (32, 24))

    # Convert the pixels
    for i in range(32):
        for j in range(24):
            temp = pixels[i + j * 32]
            image.putpixel((i, j), convert_color(temp))

    return image


def upload_image(sftp, image, timestamp):

    # Save a local image
    image.save("latest.png")

    # Upload the image
    sftp.put("latest.png", "latest.png")
    sftp.put("latest.png", f"{timestamp.strftime('%Y-%m-%d-%H-%M-%S')}.png")


def init_sftp():

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

    return ssh_client, sftp


def main():

    ignore = []
    ignore_update = 0

    newest_point = None
    cached_points = 0
    
    ssh_client = None
    sftp = None

    # Main loop
    while True:

        # List files
        if time.time() - ignore_update > 60:
            ssh_client, sftp = init_sftp()
            ignore = list_files(sftp)
            ignore_update = time.time()

        # Connect to InfluxDB
        print("Connecting to InfluxDB")
        influx = influxdb_client.InfluxDBClient(url=INFLUX_URL, org=ORG, token=INFLUX_TOKEN)
        query_api = influx.query_api()

        # Query data
        print("Querying data from InfluxDB")
        points = query_api.query_stream(f'''from(bucket: "{BUCKET}")
            |> range(start: {'-1y' if newest_point is None else newest_point.strftime('%Y-%m-%dT%H:%M:%SZ')})
            |> filter(fn: (r) => r._measurement == "wifi_thermal")
            |> filter(fn: (r) => r._field == "pixels")
            ''')

        # Process points
        print("Processing points")
        total_points = 0
        skipped_points = 0
        for point in points:
            total_points += 1
            timestamp = point.get_time()
            if newest_point is None or timestamp > newest_point:
                newest_point = timestamp + datetime.timedelta(seconds=1)
            for ignore_time in ignore:
                if ignore_time.year == timestamp.year and ignore_time.month == timestamp.month \
                    and ignore_time.day == timestamp.day and ignore_time.hour == timestamp.hour \
                    and ignore_time.minute == timestamp.minute and ignore_time.second == timestamp.second:
                    skipped_points += 1
                    break
            else:
                img = parse_image(point)
                if ssh_client is None or sftp is None:
                    ssh_client, sftp = init_sftp()
                upload_image(sftp, img, timestamp)
                print(f"Rendered image and saved as {timestamp.strftime('%Y-%m-%d-%H-%M-%S')}.png")
        print(f"Found a total of {total_points} (cached {cached_points}) points")
        print(f"Skipped {skipped_points} and renderered {total_points - skipped_points}")
        cached_points += total_points

        # Close connection
        print("Closing connections")
        if sftp is not None:
            sftp.close()
            sftp = None
        if ssh_client is not None:
            ssh_client.close()
            ssh_client = None
        influx.close()

        # Wait for the next interval
        print(f"Waiting for {INTERVAL} seconds")
        time.sleep(INTERVAL)


if __name__ == "__main__":

    main()
