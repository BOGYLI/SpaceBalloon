"""
Mission control console
"""

import sys
import requests
import datetime
import time
import getpass


PHASES = ["Countdown", "Troposphäre", "Stratosphäre", "Sinkflug", "Rescue"]


url_raspi = "https://raspi.balloon.nikogenia.de"
url_sm = "https://sm.balloon.nikogenia.de"
username_raspi = "root"
password_raspi = ""
token_sm = ""
    

def strip_service_name(name):
    return name.removeprefix("balloon-").removesuffix(".service")


def strip_service_names(names):
    return [strip_service_name(name) for name in names]


def convert_camera_name(number):
    if number == -1:
        return "off"
    return f"cam{number}"


def status_message(response):
    try:
        print(f'Status Message | "{response.json()["status"]}"')
    except (requests.JSONDecodeError, KeyError):
        pass


def status():

    aprs_fallback = False

    print("Status")
    print("------")
    print("")

    try:
        response = requests.get(url_raspi + "/status", timeout=3, auth=(username_raspi, password_raspi))
        if response.status_code == 200:
            status = response.json()
            print(f"Live camera: {convert_camera_name(status['live']['webcam'])}")
            print(f"Video cameras: {convert_camera_name(status['video']['webcam0'])}, " +
                    f"{convert_camera_name(status['video']['webcam1'])}, " +
                    f"{convert_camera_name(status['video']['webcam2'])}")
            print("Services:")
            print(f"  Active: {', '.join(strip_service_names(status['services']['active'])) or '-'}")
            print(f"  Activating: {', '.join(strip_service_names(status['services']['activating'])) or '-'}")
            print(f"  Failed: {', '.join(strip_service_names(status['services']['failed'])) or '-'}")
            print(f"  Inactive: {', '.join(strip_service_names(status['services']['inactive'])) or '-'}")
        else:
            print(f"Raspi status request failed: {response.status_code}")
            aprs_fallback = True
    except requests.exceptions.RequestException as e:
        print(f"Raspi status request failed: {e}")
        aprs_fallback = True
    print("")

    try:
        response = requests.get(url_sm + "/status", timeout=3)
        if response.status_code == 200:
            status = response.json()
            print(f"Phase: {PHASES[status["phase"]]} ({status['phase']})")
            print(f"Title: {'off' if not status['title'] else status['title']}")
            print(f"Subtitle: {'off' if not status['subtitle'] else status['subtitle']}")
            print(f"Sensor display: {'on' if status['sensors'] else 'off'}")
            print(f"Source connection: {status['source']['connection']}")
            print(f"Source height: {status['source']['height']}")
            print(f"Countdown: {status['countdown'] - time.time():.0f} seconds")
            print(f"           {datetime.datetime.fromtimestamp(status['countdown']).strftime('%m/%d %H:%M:%S')}")
        else:
            print(f"Stream Manager status request failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Stream Manager status request failed: {e}")
    print("")


def help():

    print("")
    print("Help")
    print("----")
    print("")
    print("h                       show help")
    print("q                       quit")
    print("l[x]                    livestream camera x")
    print("l                       stop camera livestream")
    print("v[xyz]                  camera x, y, z to save video file")
    print("v                       stop saving video file")
    print("pb                      go back a phase")
    print("pn                      go to next phase")
    print("s                       toggle sensor data display")
    print("sc aprs                 change connection source to APRS")
    print("sc wifi                 change connection source to WiFi")
    print("sh gps                  change height source to GPS altitude")
    print("sh climate              change height source to climate pressure")
    print("ts                      select title and subtitle popup from configuration list")
    print("tc [title];[subtitle]   set title and subtitle popup to custom text")
    print("th                      hide title and subtitle popup")
    print("r reboot system         reboot full raspberry pi system")
    print("r restart [service]     restart a systemd service")
    print("r start [service]       start a systemd service")
    print("r stop [service]        stop a systemd service")
    print("c[seconds]              set countdown to seconds")
    print("c [month];[day];[hour];[minute];[second]   set countdown to date and time")
    print("")
    print("Full console documentation is available in the GitHub wiki:")
    print("https://github.com/BOGYLI/SpaceBalloon/wiki/Mission-Control-Console")
    print("")


def main():

    global url_raspi, url_sm, username_raspi, password_raspi, token_sm

    print("Space Balloon Mission Control Console")
    print("=====================================")
    print("")

    print("Login")
    print("-----")
    print("")
    if "-c" in sys.argv or "--custom" in sys.argv:
        url_raspi = input("Raspi URL (empty for default, 'offline' for offline operation): ").strip() or url_raspi
        if url_raspi.lower() == "offline":
            url_raspi = "http://192.168.25.4"
        url_sm = input("Stream manager URL (empty for default): ").strip() or url_sm
        username_raspi = input("Raspi username (empty for default): ").strip() or username_raspi
        password_raspi = getpass.getpass("Raspi password: ").strip()
        token_sm = getpass.getpass("Stream manager token (empty to use the raspi password): ").strip() or password_raspi
    else:
        password_raspi = token_sm = getpass.getpass("Password: ").strip()
    if not password_raspi or not token_sm:
        print("Empty password or token detected, exiting")
        return
    print("")

    print("Configuration:")
    print(f"Raspi URL: {url_raspi} (username: {username_raspi}, password: {'*' * len(password_raspi)})")
    print(f"Stream manager URL: {url_sm} (token: {'*' * len(token_sm)})")
    print("")

    running = True

    while running:

        status()

        print("Enter command (h for help):")
        command = input("> ").strip()

        if command == "h":
            help()

        elif command == "q":
            running = False

        elif command == "l":
            try:
                response = requests.post(url_raspi + "/live", json={"webcam": -1}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print(f"Stopped livestream camera")
                else:
                    print(f"Failed to stop livestream camera: {response.status_code}")
                status_message(response)
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
                response = requests.post(url_raspi + "/live", json={"webcam": camera}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print(f"Changed to livestream camera {camera}")
                else:
                    print(f"Failed to change livestream camera: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to change livestream camera: {e}")
            print("")

        elif command == "v":
            try:
                response = requests.post(url_raspi + "/video", json={"webcam0": -1, "webcam1": -1, "webcam2": -1}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print(f"Stopped saving video file")
                else:
                    print(f"Failed to stop saving video file: {response.status_code}")
                status_message(response)
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
                response = requests.post(url_raspi + "/video", json={"webcam0": camera0, "webcam1": camera1, "webcam2": camera2}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print(f"Changed to video cameras {camera0}, {camera1}, {camera2}")
                else:
                    print(f"Failed to change video cameras: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to change video cameras: {e}")
            print("")

        elif command == "pb":
            try:
                response = requests.post(url_sm + "/phase/back", json={"token": token_sm}, timeout=2)
                if response.status_code == 200:
                    print(f"Changed to previous phase")
                else:
                    print(f"Failed to change phase: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to change phase: {e}")
            print("")

        elif command == "pn":
            try:
                response = requests.post(url_sm + "/phase/next", json={"token": token_sm}, timeout=2)
                if response.status_code == 200:
                    print(f"Changed to next phase")
                else:
                    print(f"Failed to change phase: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to change phase: {e}")
            print("")

        elif command == "s":
            try:
                response = requests.post(url_sm + "/sensors/toggle", json={"token": token_sm}, timeout=2)
                if response.status_code == 200:
                    print(f"Toggled sensor display")
                else:
                    print(f"Failed to toggle sensor display: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to toggle sensor display: {e}")
            print("")

        elif command.startswith("sc "):
            mode = command[3:]
            try:
                response = requests.post(url_sm + "/source", json={"token": token_sm, "connection": mode, "height": ""}, timeout=2)
                if response.status_code == 200:
                    print(f"Changed source connection to {mode}")
                else:
                    print(f"Failed to change source connection: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to change source connection: {e}")
            print("")

        elif command.startswith("sh "):
            mode = command[3:]
            try:
                response = requests.post(url_sm + "/source", json={"token": token_sm, "connection": "", "height": mode}, timeout=2)
                if response.status_code == 200:
                    print(f"Changed source height to {mode}")
                else:
                    print(f"Failed to change source height: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to change source connection: {e}")
            print("")

        elif command == "th":
            try:
                response = requests.post(url_sm + "/title", json={"token": token_sm, "title": "", "subtitle": ""}, timeout=2)
                if response.status_code == 200:
                    print("Hide title and subtitle popup")
                else:
                    print(f"Failed to hide title and subtitle popup: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to hide title and subtitle popup: {e}")
            print("")

        elif command == "ts":
            print("")
            with open("title.txt", "r") as f:
                lines = f.read().strip().splitlines()
                titles = [line.split(";") for line in lines]
            print("Select title and subtitle popup:")
            for i, (title, subtitle) in enumerate(titles):
                print(f"[{i + 1}]: {title} - {subtitle}")
            print("Enter number or cancel with enter:")
            selection = input("> ").strip()
            if not selection:
                print("")
                continue
            try:
                title, subtitle = titles[int(selection) - 1]
            except (ValueError, IndexError):
                print("Invalid selection")
                print("")
                continue
            try:
                response = requests.post(url_sm + "/title", json={"token": token_sm, "title": title, "subtitle": subtitle}, timeout=2)
                if response.status_code == 200:
                    print(f"Set title to {title} and subtitle to {subtitle}")
                else:
                    print(f"Failed to set title and subtitle popup: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to set title and subtitle popup: {e}")
            print("")

        elif command.startswith("tc "):
            title, subtitle = command[3:].split(";")
            try:
                response = requests.post(url_sm + "/title", json={"token": token_sm, "title": title, "subtitle": subtitle}, timeout=2)
                if response.status_code == 200:
                    print(f"Set title to {title} and subtitle to {subtitle}")
                else:
                    print(f"Failed to set title and subtitle popup: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to set title and subtitle popup: {e}")
            print("")

        elif command == "r reboot system":
            print("")
            print("ATTENTION: THIS ACTION WILL REBOOT THE FULL RASPBERRY PI SYSTEM!")
            print("Only do this under direct command of the flight director.")
            print("Please enter confirmation code or cancel with enter:")
            code = getpass.getpass("> ").strip()
            try:
                response = requests.post(url_raspi + "/restart/system", json={"code": code}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print("Full raspberry pi system rebooting")
                elif response.status_code == 403:
                    print("Wrong confirmation code")
                else:
                    print(f"Failed to reboot system: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to reboot system: {e}")
            print("")

        elif command.startswith("r restart "):
            service = command[11:]
            print("")
            print(f"ATTENTION: THIS ACTION WILL RESTART THE SERVICE {service}!")
            print("Only do this under direct command of the flight director.")
            print("Please enter confirmation code or cancel with enter:")
            code = getpass.getpass("> ").strip()
            try:
                response = requests.post(url_raspi + "/restart/service", json={"service": service, "code": code}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print(f"Service {service} restarted")
                elif response.status_code == 403:
                    print("Wrong confirmation code")
                else:
                    print(f"Failed to restart service {service}: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to restart service {service}: {e}")
            print("")

        elif command.startswith("r start "):
            service = command[9:]
            print("")
            print(f"ATTENTION: THIS ACTION WILL START THE SERVICE {service}!")
            print("Only do this under direct command of the flight director.")
            print("Please enter confirmation code or cancel with enter:")
            code = getpass.getpass("> ").strip()
            try:
                response = requests.post(url_raspi + "/start/service", json={"service": service, "code": code}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print(f"Service {service} started")
                elif response.status_code == 403:
                    print("Wrong confirmation code")
                else:
                    print(f"Failed to start service {service}: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to start service {service}: {e}")
            print("")

        elif command.startswith("r stop "):
            service = command[8:]
            print("")
            print(f"ATTENTION: THIS ACTION WILL STOP THE SERVICE {service}!")
            print("Only do this under direct command of the flight director.")
            print("Please enter confirmation code or cancel with enter:")
            code = getpass.getpass("> ").strip()
            try:
                response = requests.post(url_raspi + "/stop/service", json={"service": service, "code": code}, auth=(username_raspi, password_raspi), timeout=5)
                if response.status_code == 200:
                    print(f"Service {service} stopped")
                elif response.status_code == 403:
                    print("Wrong confirmation code")
                else:
                    print(f"Failed to stop service {service}: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to stop service {service}: {e}")
            print("")

        elif command.startswith("c "):
            try:
                month, day, hour, minute, second = [int(n) for n in command[2:].split(";")]
                countdown = datetime.datetime(2024, month, day, hour, minute, second).timestamp()
            except ValueError:
                print("Invalid date and time")
                print("")
                continue
            try:
                response = requests.post(url_sm + "/countdown", json={"token": token_sm, "time": countdown}, timeout=2)
                if response.status_code == 200:
                    print(f"Set countdown to {month:02d}/{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
                else:
                    print(f"Failed to set countdown: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to set countdown: {e}")
            print("")

        elif command.startswith("c"):
            try:
                countdown = float(time.time() + int(command[1:]))
                month = datetime.datetime.fromtimestamp(countdown).month
                day = datetime.datetime.fromtimestamp(countdown).day
                hour = datetime.datetime.fromtimestamp(countdown).hour
                minute = datetime.datetime.fromtimestamp(countdown).minute
                second = datetime.datetime.fromtimestamp(countdown).second
            except ValueError:
                print("Invalid second count")
                print("")
                continue
            try:
                response = requests.post(url_sm + "/countdown", json={"token": token_sm, "time": countdown}, timeout=2)
                if response.status_code == 200:
                    print(f"Set countdown to {month:02d}/{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
                else:
                    print(f"Failed to set countdown: {response.status_code}")
                status_message(response)
            except requests.exceptions.RequestException as e:
                print(f"Failed to set countdown: {e}")
            print("")

        else:
            print("Unknown command: " + command)
            print("Type 'h' for help")
            print("")


if __name__ == "__main__":

    main()