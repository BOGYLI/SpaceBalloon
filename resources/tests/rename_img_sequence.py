import os
import sys


if __name__ == "__main__":

    print("Enter the path to image folder:")
    path = input("> ").strip()

    if not os.path.exists(path):
        print("Folder not found")
        sys.exit(1)

    counter = 0
    for filename in sorted(os.listdir(path)):
        if (filename.endswith(".jpg") or filename.endswith(".png")) and not filename.startswith("latest"):
            new_filename = os.path.join(path, f"thermal_{counter:05d}.png")
            os.rename(os.path.join(path, filename), new_filename)
            print(f"Renamed {filename} to {new_filename}")
            counter += 1
        else:
            print(f"Skipped {filename}, not an image file")
