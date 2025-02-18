import datetime
import threading as th
import time
import tkinter as tk
from tkinter import ttk

run_command = lambda: print(f"WARNING: Command backend not available")
status_update = lambda: print(f"WARNING: Status backend not available")

live_cams_active = [False, False, False, False, False]
video_cams_active = [False, False, False, False, False]
phase_active = ""
title_active = ""
subtitle_active = ""
sensor_display = False
source_connection = ""
source_height = ""
countdown = 0
stream_countdown = 0
realtime = True
autoupdate = True
last_refresh = 0
request_ui_update = False

live_camera_buttons = []
video_camera_buttons = []
connection_buttons = {}
height_buttons = {}
flight_phase_buttons = {}


with open("title.txt", "r", encoding="utf-8") as f:
    lines = f.read().strip().splitlines()
    TITLES = ["  +++  ".join(line.split(";")) for line in lines]
    

def toggle_live_camera(cam):

    if live_cams_active[cam]:
        run_command("l")
    else:
        run_command(f"l{cam}")
    
    refresh_status()


def toggle_video_camera(cam):

    cams = []
    for i, active in enumerate(video_cams_active):
        if active:
            cams.append(i)

    if video_cams_active[cam]:
        cams.remove(cam)
    else:
        if len(cams) >= 2:
            cams.pop(0)
        cams.append(cam)

    run_command("v" + ''.join([str(c) for c in cams]))
    
    refresh_status()


def send_title():

    titel_text = titel_entry.get().strip()
    untertitel_text = untertitel_entry.get().strip()
    run_command(f"tc {titel_text};{untertitel_text}")

    refresh_status()


def apply_preset():

    preset = preset_var.get()
    if not preset:
        return
    run_command(f"tc {';'.join(preset.split('  +++  '))}")

    refresh_status()


def send_countdown():

    monat = countdown_monat_entry.get().strip()
    tag = countdown_tag_entry.get().strip()
    stunde = countdown_stunde_entry.get().strip()
    minute = countdown_minute_entry.get().strip()
    sekunde = countdown_sekunde_entry.get().strip()
    
    run_command(f"c {monat};{tag};{stunde};{minute};{sekunde}")

    refresh_status()


def send_stream_countdown():

    monat = stream_monat_entry.get().strip()
    tag = stream_tag_entry.get().strip()
    stunde = stream_stunde_entry.get().strip()
    minute = stream_minute_entry.get().strip()
    sekunde = stream_sekunde_entry.get().strip()
    
    run_command(f"c {monat};{tag};{stunde};{minute};{sekunde}")

    refresh_status()


def toggle_sensors():

    run_command("s")

    refresh_status()


def toggle_realtime():

    run_command("rt")

    refresh_status()
    

def toggle_autoupdate():

    global autoupdate
    autoupdate = not autoupdate
    

def select_connection_source(source):
    
    run_command(f"sc {source}")

    refresh_status()


def select_height_source(source):
    
    run_command(f"sh {source}")

    refresh_status()


def update_live_camera_buttons():

    for i, active in enumerate(live_cams_active):
        if active:
            live_camera_buttons[i].configure(bg="green")
        else:
            live_camera_buttons[i].configure(bg="white")


def update_video_camera_buttons():

    for i, active in enumerate(video_cams_active):
        if active:
            video_camera_buttons[i].configure(bg="green")
        else:
            video_camera_buttons[i].configure(bg="white")


def update_sensor_button():

    if sensor_toggle_button is not None:
        sensor_toggle_button.configure(bg="green" if sensor_display else "white")


def update_title():

    titel_entry.delete(0, tk.END)
    untertitel_entry.delete(0, tk.END)
    titel_entry.insert(0, title_active)
    untertitel_entry.insert(0, subtitle_active)


def update_countdown_inputs():

    c = datetime.datetime.fromtimestamp(countdown)

    countdown_monat_entry.delete(0, tk.END)
    countdown_tag_entry.delete(0, tk.END)
    countdown_stunde_entry.delete(0, tk.END)
    countdown_minute_entry.delete(0, tk.END)
    countdown_sekunde_entry.delete(0, tk.END)

    countdown_monat_entry.insert(0, str(c.month))
    countdown_tag_entry.insert(0, str(c.day))
    countdown_stunde_entry.insert(0, str(c.hour))
    countdown_minute_entry.insert(0, str(c.minute))
    countdown_sekunde_entry.insert(0, str(c.second))


def update_stream_countdown_inputs():

    c = datetime.datetime.fromtimestamp(stream_countdown)

    stream_monat_entry.delete(0, tk.END)
    stream_tag_entry.delete(0, tk.END)
    stream_stunde_entry.delete(0, tk.END)
    stream_minute_entry.delete(0, tk.END)
    stream_sekunde_entry.delete(0, tk.END)

    stream_monat_entry.insert(0, str(c.month))
    stream_tag_entry.insert(0, str(c.day))
    stream_stunde_entry.insert(0, str(c.hour))
    stream_minute_entry.insert(0, str(c.minute))
    stream_sekunde_entry.insert(0, str(c.second))


def update_connection_buttons():

    if "wifi" in connection_buttons:
        connection_buttons["wifi"].configure(bg="green" if source_connection == "wifi" else "white")
    if "aprs" in connection_buttons:
        connection_buttons["aprs"].configure(bg="green" if source_connection == "aprs" else "white")


def update_height_buttons():

    if "gps" in height_buttons:
        height_buttons["gps"].configure(bg="green" if source_height=="gps" else "white")
    if "climate" in height_buttons:
        height_buttons["climate"].configure(bg="green" if source_height == "climate" else "white")


def update_steuerung_buttons():

    realtime_button.configure(bg="green" if realtime else "white")
    autoupdate_button.configure(bg="green" if autoupdate else "white")


def update_ui():

    update_live_camera_buttons()
    update_video_camera_buttons()
    update_sensor_button()
    update_title()
    update_connection_buttons()
    update_height_buttons()
    update_countdown_inputs()
    update_stream_countdown_inputs()
    update_steuerung_buttons()


def refresh_status():

    global last_refresh

    last_refresh = time.time()

    def thread():

        global live_cams_active, video_cams_active, phase_active, title_active, \
            subtitle_active, sensor_display, source_connection, source_height, \
            countdown, stream_countdown, realtime, request_ui_update
        
        live_cams_active, video_cams_active, phase_active, title_active, \
            subtitle_active, sensor_display, source_connection, source_height, \
            countdown, stream_countdown, realtime = status_update()

        request_ui_update = True

    th.Thread(target=thread).start()
    

def periodic_refresh():

    global request_ui_update
    
    if time.time() - last_refresh > 20 and autoupdate:
        refresh_status()

    if request_ui_update:
        request_ui_update = False
        update_ui()

    root.after(100, periodic_refresh)


root = tk.Tk()
root.geometry("800x800")
root.title("Space Balloon Mission Control Console")


# ------------------------------------------------------------
# Bereich Steuerung
# ------------------------------------------------------------
steuerung_frame = ttk.LabelFrame(root, text="Steuerung")
steuerung_frame.pack(fill="x", padx=10, pady=5)
steuerung_frame.columnconfigure(0, weight=1)
steuerung_frame.columnconfigure(1, weight=1)
steuerung_frame.columnconfigure(2, weight=1)

realtime_button = tk.Button(steuerung_frame, text="Realtime Modus", width=20, bg="white", relief="solid", bd=1, command=toggle_realtime)
realtime_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

autoupdate_button = tk.Button(steuerung_frame, text="Auto Update 20s", width=20, bg="white", relief="solid", bd=1, command=toggle_autoupdate)
autoupdate_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

refresh_button = tk.Button(steuerung_frame, text="Jetzt aktualisieren", width=20, bg="white", relief="solid", bd=1, command=refresh_status)
refresh_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

# ------------------------------------------------------------
# Bereich Titel & Untertitel
# ------------------------------------------------------------
titel_frame = ttk.LabelFrame(root, text="Titel & Untertitel")
titel_frame.pack(fill="x", padx=10, pady=5)
titel_frame.columnconfigure(1, weight=1)

ttk.Label(titel_frame, text="Titel:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
titel_entry = ttk.Entry(titel_frame, width=40)
titel_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
ttk.Label(titel_frame, text="Untertitel:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
untertitel_entry = ttk.Entry(titel_frame, width=40)
untertitel_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
update_title_button = ttk.Button(titel_frame, text="Titel aktualisieren", command=send_title)
update_title_button.grid(row=0, column=2, rowspan=2, padx=5, pady=5)

# ------------------------------------------------------------
# Bereich Voreingestellte Titel (title.txt)
# ------------------------------------------------------------
preset_frame = ttk.LabelFrame(root, text="Voreingestellte Titel")
preset_frame.pack(fill="x", padx=10, pady=5)
preset_frame.columnconfigure(0, weight=1)
preset_var = tk.StringVar()
preset_dropdown = ttk.Combobox(preset_frame, textvariable=preset_var, values=TITLES, state="readonly", width=50)
preset_dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
apply_preset_button = ttk.Button(preset_frame, text="Preset anwenden", command=apply_preset)
apply_preset_button.grid(row=0, column=1, padx=5, pady=5)

# ------------------------------------------------------------
# Neuer Bereich Countdown (Eingaben: Monat, Tag, Stunde, Minute, Sekunde)
# ------------------------------------------------------------
countdown_frame = ttk.LabelFrame(root, text="Countdown")
countdown_frame.pack(fill="x", padx=10, pady=5)
for col in range(11):
    countdown_frame.columnconfigure(col, weight=1)
ttk.Label(countdown_frame, text="Monat:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
countdown_monat_entry = ttk.Entry(countdown_frame, width=5)
countdown_monat_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
ttk.Label(countdown_frame, text="Tag:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
countdown_tag_entry = ttk.Entry(countdown_frame, width=5)
countdown_tag_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
ttk.Label(countdown_frame, text="Stunde:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
countdown_stunde_entry = ttk.Entry(countdown_frame, width=5)
countdown_stunde_entry.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
ttk.Label(countdown_frame, text="Minute:").grid(row=0, column=6, padx=5, pady=5, sticky="e")
countdown_minute_entry = ttk.Entry(countdown_frame, width=5)
countdown_minute_entry.grid(row=0, column=7, padx=5, pady=5, sticky="ew")
ttk.Label(countdown_frame, text="Sekunde:").grid(row=0, column=8, padx=5, pady=5, sticky="e")
countdown_sekunde_entry = ttk.Entry(countdown_frame, width=5)
countdown_sekunde_entry.grid(row=0, column=9, padx=5, pady=5, sticky="ew")

# Standardwerte: aktueller Monat, Tag; Stunde = eine Stunde nach aktuell, Minute und Sekunde = 00
now = datetime.datetime.now()
countdown_monat_entry.insert(0, now.strftime("%m"))
countdown_tag_entry.insert(0, now.strftime("%d"))
hour = (now.hour + 1) % 24
countdown_stunde_entry.insert(0, str(hour).zfill(2))
countdown_minute_entry.insert(0, "00")
countdown_sekunde_entry.insert(0, "00")

update_countdown_button = ttk.Button(countdown_frame, text="Countdown aktualisieren", command=send_countdown)
update_countdown_button.grid(row=0, column=10, padx=5, pady=5)
cd_label = ttk.Label(countdown_frame, text="Verbleibend: 0 min 0 sec")
cd_label.grid(row=1, column=0, columnspan=11, padx=5, pady=5, sticky="ew")

# ------------------------------------------------------------
# Bereich Stream Countdown
# ------------------------------------------------------------
stream_countdown_frame = ttk.LabelFrame(root, text="Stream Countdown")
stream_countdown_frame.pack(fill="x", padx=10, pady=5)
for col in range(12):
    stream_countdown_frame.columnconfigure(col, weight=1)
now = datetime.datetime.now()
default_monat = now.strftime("%m")
default_tag = now.strftime("%d")
default_stunde = str((now.hour + 1) % 24).zfill(2)
default_minute = "00"
default_sekunde = "00"
ttk.Label(stream_countdown_frame, text="Monat:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
stream_monat_entry = ttk.Entry(stream_countdown_frame, width=5)
stream_monat_entry.insert(0, default_monat)
stream_monat_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
ttk.Label(stream_countdown_frame, text="Tag:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
stream_tag_entry = ttk.Entry(stream_countdown_frame, width=5)
stream_tag_entry.insert(0, default_tag)
stream_tag_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
ttk.Label(stream_countdown_frame, text="Stunde:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
stream_stunde_entry = ttk.Entry(stream_countdown_frame, width=5)
stream_stunde_entry.insert(0, default_stunde)
stream_stunde_entry.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
ttk.Label(stream_countdown_frame, text="Minute:").grid(row=0, column=6, padx=5, pady=5, sticky="e")
stream_minute_entry = ttk.Entry(stream_countdown_frame, width=5)
stream_minute_entry.insert(0, default_minute)
stream_minute_entry.grid(row=0, column=7, padx=5, pady=5, sticky="ew")
ttk.Label(stream_countdown_frame, text="Sekunde:").grid(row=0, column=8, padx=5, pady=5, sticky="e")
stream_sekunde_entry = ttk.Entry(stream_countdown_frame, width=5)
stream_sekunde_entry.insert(0, default_sekunde)
stream_sekunde_entry.grid(row=0, column=9, padx=5, pady=5, sticky="ew")
update_stream_countdown_button = ttk.Button(stream_countdown_frame, text="Stream Countdown aktualisieren", command=send_stream_countdown)
update_stream_countdown_button.grid(row=0, column=10, padx=5, pady=5)
stream_cd_label = ttk.Label(stream_countdown_frame, text="Verbleibend: 0 min 0 sec")
stream_cd_label.grid(row=0, column=11, padx=5, pady=5, sticky="ew")

# ------------------------------------------------------------
# Bereich Live-Kamera Auswahl (Mehrfachauswahl möglich)
# ------------------------------------------------------------
live_camera_frame = ttk.LabelFrame(root, text="Live-Kamera Auswahl")
live_camera_frame.pack(fill="x", padx=10, pady=5)
for col in range(5):
    live_camera_frame.columnconfigure(col, weight=1)
for i in range(5):  # Kameras 0 bis 4
    btn = tk.Button(live_camera_frame,
                    text=f"Kamera {i}",
                    width=15,
                    bg="white",
                    relief="solid",
                    bd=1,
                    command=lambda idx=i: toggle_live_camera(idx))
    btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
    live_camera_buttons.append(btn)

# ------------------------------------------------------------
# Bereich Videoaufzeichnung (bis zu 2 Kameras aktiv, Mehrfachauswahl möglich)
# ------------------------------------------------------------
video_camera_frame = ttk.LabelFrame(root, text="Videoaufzeichnung")
video_camera_frame.pack(fill="x", padx=10, pady=5)
for col in range(5):
    video_camera_frame.columnconfigure(col, weight=1)
for i in range(5):  # Kameras 0 bis 4
    btn = tk.Button(video_camera_frame,
                    text=f"Kamera {i}",
                    width=15,
                    bg="white",
                    relief="solid",
                    bd=1,
                    command=lambda idx=i: toggle_video_camera(idx))
    btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
    video_camera_buttons.append(btn)

# ------------------------------------------------------------
# Bereich Sensor Umschaltung
# ------------------------------------------------------------
sensor_frame = ttk.LabelFrame(root, text="Sensor Umschaltung")
sensor_frame.pack(fill="x", padx=10, pady=5)
sensor_frame.columnconfigure(0, weight=1)
sensor_toggle_button = tk.Button(sensor_frame,
                                 text="Sensoren umschalten",
                                 width=15,
                                 bg="white",
                                 relief="solid",
                                 bd=1,
                                 command=toggle_sensors)
sensor_toggle_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
update_sensor_button()

# ------------------------------------------------------------
# Bereich Quellen: Verbindungs- & Höhenquelle nebeneinander
# ------------------------------------------------------------
quellen_frame = ttk.Frame(root)
quellen_frame.pack(fill="x", padx=10, pady=5)
quellen_frame.columnconfigure(0, weight=1)
quellen_frame.columnconfigure(1, weight=1)

connection_frame = ttk.LabelFrame(quellen_frame, text="Verbindungsquelle (Exklusiv)")
connection_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
for col in range(2):
    connection_frame.columnconfigure(col, weight=1)
btn_wifi = tk.Button(connection_frame,
                      text="sc wifi",
                      width=15,
                      bg="green",
                      relief="solid",
                      bd=1,
                      command=lambda: select_connection_source("wifi"))
btn_wifi.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
connection_buttons["wifi"] = btn_wifi
btn_aprs = tk.Button(connection_frame,
                      text="sc aprs",
                      width=15,
                      bg="white",
                      relief="solid",
                      bd=1,
                      command=lambda: select_connection_source("aprs"))
btn_aprs.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
connection_buttons["aprs"] = btn_aprs

height_frame = ttk.LabelFrame(quellen_frame, text="Höhenquelle (Exklusiv)")
height_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
height_frame.columnconfigure(0, weight=1)
height_frame.columnconfigure(2, weight=1)
btn_gps = tk.Button(height_frame,
                    text="sh gps",
                    width=15,
                    bg="green",
                    relief="solid",
                    bd=1,
                    command=lambda: select_height_source("gps"))
btn_gps.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
height_buttons["gps"] = btn_gps
separator = ttk.Separator(height_frame, orient="vertical")
separator.grid(row=0, column=1, sticky="ns", padx=5)
btn_climate = tk.Button(height_frame,
                        text="sh climate",
                        width=15,
                        bg="white",
                        relief="solid",
                        bd=1,
                        command=lambda: select_height_source("climate"))
btn_climate.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
height_buttons["climate"] = btn_climate

# ------------------------------------------------------------
# Periodischer Refresh starten (alle 5 Sekunden)
# ------------------------------------------------------------

def start():

    root.after(100, periodic_refresh)

    root.mainloop()
