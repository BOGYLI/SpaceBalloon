from pathlib import Path


def fix_longitude(lon):

    lon = lon + 6
    minutes = (lon - 1) * 60
    coords = f'01{minutes}'
    degrees = int(coords[:3])
    minutes = float(coords[3:])
    degrees_dec = degrees + minutes / 60
    return degrees_dec


if __name__ == '__main__':

    print("Enter the path to the file:")
    path = Path(input("> "))
    with open(path, 'r') as file:
        with open(path.with_name("fixed_" + path.name), 'w') as out_file:

            for line in file:
                columns = line.split(',')
                if len(columns) < 4:
                    print("Invalid line:", line)
                    continue
                try:
                    longitude = float(columns[2])
                    if longitude < 0:
                        columns[2] = str(fix_longitude(longitude))
                except ValueError:
                    print("Could not parse longitude, ignoring line:", line)
                out_file.write(','.join(columns))

