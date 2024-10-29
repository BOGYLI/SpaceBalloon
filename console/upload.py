import os
import influxdb_client
from getpass import getpass


influx_url = "https://influx.balloon.nikogenia.de"
influx_org = "makerspace"
influx_bucket = "balloon"
influx_token = ""


def format_size(size):

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024


def write_to_influx(name, data):

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=influx_url, org=influx_org, token=influx_token) as client:

        points = []

        for timestamp, fields in data.items():
            point = influxdb_client.Point(name).time(timestamp, "s")
            pixels = ""
            for field, value in fields.items():
                if name == "file_thermal" and field.isdigit():
                    pixels += f",{int(value)}" if pixels else f"{int(value)}"
                    continue
                point.field(field, value)
            if name == "file_thermal" and pixels:
                point.field("pixels", pixels)
            points.append(point)

        write_api = client.write_api()
        for point in points:
            write_api.write(bucket=influx_bucket, record=point)
        write_api.close()

        print("Successfully sent data to InfluxDB")


def upload():

    global influx_url, influx_org, influx_bucket, influx_token

    print("Upload")
    print("------")
    print("")

    influx_url = input("Influx URL (empty for default): ").strip() or influx_url
    influx_org = input("Influx Organisation (empty for default): ").strip() or influx_org
    influx_bucket = input("Influx Bucket (empty for default): ").strip() or influx_bucket
    influx_token = getpass("Influx Token: ").strip()
    if not influx_token:
        print("Empty token detected, exiting")
        return
    print("")

    print("Configuration:")
    print(f"Influx URL: {influx_url} (organisation: {influx_org}, bucket: {influx_bucket}, token: {'*' * len(influx_token)})")
    print("")

    running = True

    while running:

        print("Enter file to upload (q to exit):")
        file = input("> ").strip()
        print("")

        if file == "q":
            running = False
            continue

        if not os.path.exists(file):
            print(f"File not found: {file}")
            print("")
            continue

        path = os.path.abspath(file)

        if not os.path.isfile(path):
            print(f"Not a file: {path}")
            print("")
            continue

        print(f"Loading file {path}")
        try:
            with open(path, "r") as f:
                head = f.readline()
        except OSError as e:
            print(f"Failed to open file: {e}")
            print("")
            continue
        print("")

        columns = head.strip().split(",")
        width = len(columns)
        size = os.path.getsize(path)

        if not columns:
            print("No columns found in file")
            print("")
            continue

        if columns[0] != "timestamp":
            print("First column must be 'timestamp'")
            print("")
            continue

        print(f"Path: {path}")
        print(f"Size: {format_size(size)}")
        print(f"Columns: {', '.join(columns)}")
        print(f"Field count: {width - 1}")
        print("")

        print("Parse data? (y/n)")
        confirm = input("> ").strip().lower()
        print("")
        if confirm != "y":
            continue

        data = {}
        with open(path, "r") as f:
            for i, line in enumerate(f):
                try:
                    if i == 0:
                        continue
                    values = line.strip().split(",")
                    if len(values) != width:
                        print(f"Invalid line width {i + 1}: {line.strip()}")
                    for j, value in enumerate(values):
                        if j == 0:
                            timestamp = int(float(value))
                            data[timestamp] = {}
                        else:
                            data[timestamp][columns[j]] = float(value)
                except ValueError as e:
                    print(f"Failed to parse line {i + 1} because of value error ({e}): {line.strip()}")
                except Exception as e:
                    print(f"Failed to parse line {i + 1} because of unknown error ({e}): {line.strip()}")

        name = "file_" + os.path.basename(path).removesuffix(".csv")
        print(f"Measurement name is {name}")
        print("Is this correct? (enter to confirm, else type new name)")
        confirm = input("> ").strip()
        if confirm:
            name = confirm
        print("")

        print(f"Measurement name: {name}")
        print(f"Fields: {', '.join(columns[1:])}")
        print(f"Data points: {len(data)}")
        print("")

        print("Upload data to InfluxDB? (y/n)")
        confirm = input("> ").strip().lower()
        print("")
        if confirm != "y":
            continue

        write_to_influx(name, data)                

    print("Exiting")


if __name__ == "__main__":

    print("Space Balloon Mission Control Console")
    print("=====================================")
    print("")

    upload()
