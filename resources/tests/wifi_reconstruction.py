from pathlib import Path
import datetime


last_input = 0
silent_zones = [(datetime.datetime(2025, 3, 20, 10, 43, 6, 0).timestamp(), 314), (datetime.datetime(2025, 3, 20, 10, 56, 54, 0).timestamp(), 172),
                (datetime.datetime(2025, 3, 20, 11, 23, 0, 0).timestamp(), 97)]
startline = datetime.datetime(2025, 3, 20, 10, 38, 2, 0).timestamp()
deadline = datetime.datetime(2025, 3, 20, 11, 26, 21, 0).timestamp()
points = [datetime.datetime(2025, 3, 20, 11, 27, 2, 0).timestamp(), datetime.datetime(2025, 3, 20, 11, 29, 21, 0).timestamp(),
          datetime.datetime(2025, 3, 20, 11, 34, 19, 0).timestamp(), datetime.datetime(2025, 3, 20, 11, 39, 46, 0).timestamp()]


def keep_or_not(timestamp):

    global last_input

    if timestamp - last_input < 5:
        return False

    for silent_zone in silent_zones:
        if silent_zone[0] < timestamp < silent_zone[0] + silent_zone[1]:
            return False
    
    if startline < timestamp < deadline:
        last_input = timestamp
        return True
    
    for point in points:
        if abs(timestamp - point) < 18 and timestamp - last_input > 40:
            last_input = timestamp
            return True

    return False


if __name__ == '__main__':

    print("Enter the path to the file:")
    path = Path(input("> "))
    with open(path, 'r') as file:
        with open(path.with_name("wifi_" + path.name), 'w') as out_file:

            for line in file:
                columns = line.split(',')
                if len(columns) < 2:
                    print("Invalid line:", line)
                    continue
                keep = True
                try:
                    timestamp = float(columns[0])
                    keep = keep_or_not(timestamp)
                except ValueError:
                    print("Could not parse timestamp, ignoring line:", line)
                if keep:
                    out_file.write(','.join(columns))

