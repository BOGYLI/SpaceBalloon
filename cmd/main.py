"""
Mission control console
"""

import requests
import getpass


def main():
    
    print("Space Balloon Mission Control Console")
    print("=====================================")
    print("")

    print("Login")
    print("-----")
    print("")
    url = input("URL (empty for default): ").strip() or "https://raspi.balloon.nikogenia.de"
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ").strip()
    print("")

    running = True

    while running:

        print("Status")
        print("------")
        print("")

        try:
            response = requests.get(url + "/status", timeout=3, auth=(username, password))
            if response.status_code == 200:
                status = response.json()
                print(f"Live camera: {status["live"]["webcam"]}")
                print(f"Video cameras: {status["video"]["webcam0"]}, {status["video"]["webcam1"]}, {status["video"]["webcam2"]}")
                print("Services:")
                print(f"  Active: {', '.join(status["services"]["active"])}")
                print(f"  Activating: {', '.join(status["services"]["activating"])}")
                print(f"  Failed: {', '.join(status["services"]["failed"])}")
                print(f"  Inactive: {', '.join(status["services"]["inactive"])}")
            else:
                print(f"Status request failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Status request failed: {e}")
        print("")

        print("Enter command (h for help):")
        command = input("> ").strip()

        if command == "h":
            print("")
            print("Help")
            print("----")
            print("")
            print("h: show help")
            print("q: quit")
            print("l[x]: livestream camera x")
            print("l: stop camera livestream")
            print("v[xyz]: camera x, y, z to save video file")
            print("v: stop saving video file")
            print("pb: go back a phase")
            print("pn: go to next phase")
            print("c[seconds]: set countdown to seconds")
            print("t [title];[subtitle]: set title and subtitle popup")
            print("t: hide title and subtitle popup")
            print("r system: reboot full raspberry pi system")
            print("r [service]: restart a systemd service")
            print("")

        elif command == "q":
            running = False

        elif command == "l":
            try:
                response = requests.post(url + "/live", json={"webcam": -1}, auth=(username, password), timeout=5)
                if response.status_code == 200:
                    print(f"Stopped livestream camera")
                else:
                    print(f"Failed to stop livestream camera: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to stop livestream camera: {e}")
            print("")

        elif command.startswith("l"):
            try:
                camera = int(command[1:])
            except ValueError:
                print("Invalid camera number")
                print("")
                continue
            try:
                response = requests.post(url + "/live", json={"webcam": camera}, auth=(username, password), timeout=5)
                if response.status_code == 200:
                    print(f"Changed to livestream camera {camera}")
                else:
                    print(f"Failed to change livestream camera: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to change livestream camera: {e}")
            print("")

        elif command == "v":
            try:
                response = requests.post(url + "/video", json={"webcam0": -1, "webcam1": -1, "webcam2": -1}, auth=(username, password), timeout=5)
                if response.status_code == 200:
                    print(f"Stopped saving video file")
                else:
                    print(f"Failed to stop saving video file: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to stop saving video file: {e}")
            print("")

        elif command.startswith("v"):
            try:
                cameras = [int(n) for n in command[1:]]
                camera0 = cameras[0] if len(cameras) > 0 else -1
                camera1 = cameras[1] if len(cameras) > 1 else -1
                camera2 = cameras[2] if len(cameras) > 2 else -1
            except ValueError:
                print("Invalid camera selection")
                print("")
                continue
            if camera0 == camera1 != -1 or camera0 == camera2 != -1 or camera1 == camera2 != -1:
                print("Duplicate camera selection")
                print("")
                continue
            try:
                response = requests.post(url + "/video", json={"webcam0": camera0, "webcam1": camera1, "webcam2": camera2}, auth=(username, password), timeout=5)
                if response.status_code == 200:
                    print(f"Changed to video cameras {camera0}, {camera1}, {camera2}")
                else:
                    print(f"Failed to change video cameras: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to change video cameras: {e}")
            print("")

        elif command == "pb":
            print("Go back a phase")
            print("")

        elif command == "pn":
            print("Go to next phase")
            print("")

        elif command.startswith("c"):
            countdown = command[1:]
            print("Set countdown to " + countdown + " seconds")
            print("")

        elif command == "t":
            print("Hide title and subtitle popup")
            print("")

        elif command.startswith("t "):
            title, subtitle = command[2:].split(";")
            print("Set title to " + title + " and subtitle to " + subtitle)
            print("")

        elif command == "r system":
            print("")
            print("ATTENTION: THIS ACTION WILL REBOOT THE FULL RASPBERRY PI SYSTEM!")
            print("Only do this under direct command of the flight director.")
            print("Please enter confirmation code or cancel with enter:")
            code = input("> ").strip()
            try:
                response = requests.post(url + "/restart/system", json={"code": code}, auth=(username, password), timeout=5)
                if response.status_code == 200:
                    print("Full raspberry pi system rebooting")
                elif response.status_code == 403:
                    print("Wrong confirmation code")
                else:
                    print(f"Failed to reboot system: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to reboot system: {e}")
            print("")

        elif command.startswith("r "):
            service = command[2:]
            print("")
            print(f"ATTENTION: THIS ACTION WILL RESTART THE SERVICE {service}!")
            print("Only do this under direct command of the flight director.")
            print("Please enter confirmation code or cancel with enter:")
            code = input("> ").strip()
            try:
                response = requests.post(url + "/restart/service", json={"service": service, "code": code}, auth=(username, password), timeout=5)
                if response.status_code == 200:
                    print(f"Service {service} restarted")
                elif response.status_code == 403:
                    print("Wrong confirmation code")
                else:
                    print(f"Failed to restart service {service}: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to restart service {service}: {e}")
            print("")

        else:
            print("Unknown command: " + command)
            print("Type 'h' for help")
            print("")


if __name__ == "__main__":

    main()
