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
realtime = False
autoupdate = True
autoupdate_setting = True
last_refresh = 0
countdown_update = 0
request_ui_update = False

live_camera_buttons = []
video_camera_buttons = []
connection_buttons = {}
height_buttons = {}
flight_phase_buttons = {}


COLOR_BG = "#f0f0f0"
COLOR_BUTTON = "#ffffff"
COLOR_TEXT = "#000000"
COLOR_ACCENT = "#e7931a"
COLOR_HIGHLIGHT = "#cccccc"


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
    subtitle_text = subtitle_entry.get().strip()
    run_command(f"tc {titel_text};{subtitle_text}")
    check_autoupdate()
    refresh_status()


def clear_title():
    run_command("th")
    refresh_status()


def apply_preset():
    preset = preset_var.get()
    if not preset:
        return
    run_command(f"tc {';'.join(preset.split('  +++  '))}")
    refresh_status()


def send_countdown():
    month = countdown_month_entry.get().strip()
    day = countdown_day_entry.get().strip()
    hour = countdown_hour_entry.get().strip()
    minute = countdown_minute_entry.get().strip()
    second = countdown_second_entry.get().strip()
    run_command(f"c {month};{day};{hour};{minute};{second}")
    check_autoupdate()
    refresh_status()


def send_stream_countdown():
    month = stream_countdown_month_entry.get().strip()
    day = stream_countdown_day_entry.get().strip()
    hour = stream_countdown_hour_entry.get().strip()
    minute = stream_countdown_minute_entry.get().strip()
    second = stream_countdown_second_entry.get().strip()
    run_command(f"cs {month};{day};{hour};{minute};{second}")
    check_autoupdate()
    refresh_status()


def toggle_sensors():
    run_command("s")
    refresh_status()


def toggle_realtime():
    run_command("rt")
    refresh_status()
    

def toggle_autoupdate():
    global autoupdate, autoupdate_setting
    autoupdate = not autoupdate
    autoupdate_setting = autoupdate
    update_ui()


def disable_autoupdate(e):
    global autoupdate
    autoupdate = False
    update_control_buttons()


def check_autoupdate():
    global autoupdate
    autoupdate = autoupdate_setting
    update_ui()
    

def select_connection_source(source):
    run_command(f"sc {source}")
    refresh_status()


def select_height_source(source):
    run_command(f"sh {source}")
    refresh_status()


def phase_back():
    run_command("pb")
    refresh_status()


def phase_next():
    run_command("pn")
    refresh_status()


def execute_raw_command():
    command = raw_command_entry.get().strip()
    if command:
        run_command(command)
        refresh_status()


def update_live_camera_buttons():
    for i, active in enumerate(live_cams_active):
        if active:
            live_camera_buttons[i].configure(bg=COLOR_ACCENT)
        else:
            live_camera_buttons[i].configure(bg=COLOR_BUTTON)


def update_video_camera_buttons():
    for i, active in enumerate(video_cams_active):
        if active:
            video_camera_buttons[i].configure(bg=COLOR_ACCENT)
        else:
            video_camera_buttons[i].configure(bg=COLOR_BUTTON)


def update_sensor_button():
    if sensor_toggle_button is not None:
        sensor_toggle_button.configure(bg=COLOR_ACCENT if sensor_display else COLOR_BUTTON)


def update_title():
    titel_entry.delete(0, tk.END)
    subtitle_entry.delete(0, tk.END)
    titel_entry.insert(0, title_active)
    subtitle_entry.insert(0, subtitle_active)


def update_countdown_inputs():
    c = datetime.datetime.fromtimestamp(countdown)
    countdown_month_entry.delete(0, tk.END)
    countdown_day_entry.delete(0, tk.END)
    countdown_hour_entry.delete(0, tk.END)
    countdown_minute_entry.delete(0, tk.END)
    countdown_second_entry.delete(0, tk.END)
    countdown_month_entry.insert(0, str(c.month))
    countdown_day_entry.insert(0, str(c.day))
    countdown_hour_entry.insert(0, str(c.hour))
    countdown_minute_entry.insert(0, str(c.minute))
    countdown_second_entry.insert(0, str(c.second))


def update_stream_countdown_inputs():
    c = datetime.datetime.fromtimestamp(stream_countdown)
    stream_countdown_month_entry.delete(0, tk.END)
    stream_countdown_day_entry.delete(0, tk.END)
    stream_countdown_hour_entry.delete(0, tk.END)
    stream_countdown_minute_entry.delete(0, tk.END)
    stream_countdown_second_entry.delete(0, tk.END)
    stream_countdown_month_entry.insert(0, str(c.month))
    stream_countdown_day_entry.insert(0, str(c.day))
    stream_countdown_hour_entry.insert(0, str(c.hour))
    stream_countdown_minute_entry.insert(0, str(c.minute))
    stream_countdown_second_entry.insert(0, str(c.second))


def update_countdown_labels():
    delta = countdown - time.time()
    text = "T-" if delta > 0 else "T+"
    delta = abs(delta)
    hours, remainder = divmod(delta, 3600)
    minutes, seconds = divmod(remainder, 60)
    countdown_label_active.configure(text=f"{text}{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    try:
        month = int(countdown_month_entry.get().strip())
        day = int(countdown_day_entry.get().strip())
        hour = int(countdown_hour_entry.get().strip())
        minute = int(countdown_minute_entry.get().strip())
        second = int(countdown_second_entry.get().strip())
        delta = datetime.datetime(year=2025, month=month, day=day, hour=hour, minute=minute, second=second) - datetime.datetime.now()
        text = "T-" if delta.total_seconds() > 0 else "T+"
        delta = abs(delta.total_seconds())
        hours, remainder = divmod(delta, 3600)
        minutes, seconds = divmod(remainder, 60)
        countdown_label_new.configure(text=f"{text}{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    except ValueError:
        countdown_label_new.configure(text="Ungültige Eingabe")


def update_stream_countdown_labels():
    delta = stream_countdown - time.time()
    if delta > 0:
        delta = abs(delta)
        hours, remainder = divmod(delta, 3600)
        minutes, seconds = divmod(remainder, 60)
        stream_countdown_label_active.configure(text=f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    else:
        stream_countdown_label_active.configure(text="00:00:00")
    try:
        month = int(stream_countdown_month_entry.get().strip())
        day = int(stream_countdown_day_entry.get().strip())
        hour = int(stream_countdown_hour_entry.get().strip())
        minute = int(stream_countdown_minute_entry.get().strip())
        second = int(stream_countdown_second_entry.get().strip())
        delta = datetime.datetime(year=2025, month=month, day=day, hour=hour, minute=minute, second=second) - datetime.datetime.now()
        if delta.total_seconds() > 0:
            delta = abs(delta.total_seconds())
            hours, remainder = divmod(delta, 3600)
            minutes, seconds = divmod(remainder, 60)
            stream_countdown_label_new.configure(text=f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        else:
            stream_countdown_label_new.configure(text="00:00:00")
    except ValueError:
        stream_countdown_label_new.configure(text="Ungültige Eingabe")


def update_connection_buttons():
    if "wifi" in connection_buttons:
        connection_buttons["wifi"].configure(bg=COLOR_ACCENT if source_connection == "wifi" else COLOR_BUTTON)
    if "aprs" in connection_buttons:
        connection_buttons["aprs"].configure(bg=COLOR_ACCENT if source_connection == "aprs" else COLOR_BUTTON)


def update_height_buttons():
    if "gps" in height_buttons:
        height_buttons["gps"].configure(bg=COLOR_ACCENT if source_height=="gps" else COLOR_BUTTON)
    if "climate" in height_buttons:
        height_buttons["climate"].configure(bg=COLOR_ACCENT if source_height == "climate" else COLOR_BUTTON)


def update_control_buttons():
    realtime_button.configure(bg=COLOR_ACCENT if realtime else COLOR_BUTTON)
    autoupdate_button.configure(bg=COLOR_ACCENT if autoupdate else COLOR_BUTTON)


def update_phase_display():
    for lbl in phase_labels:
        if lbl.cget("text") == phase_active:
            lbl.configure(bg=COLOR_HIGHLIGHT)
        else:
            lbl.configure(bg=COLOR_BUTTON)


def update_ui():
    update_live_camera_buttons()
    update_video_camera_buttons()
    update_sensor_button()
    update_title()
    update_connection_buttons()
    update_height_buttons()
    update_countdown_inputs()
    update_stream_countdown_inputs()
    update_control_buttons()
    update_countdown_labels()
    update_stream_countdown_labels()
    update_phase_display()


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

    global request_ui_update, countdown_update

    if time.time() - last_refresh > 20 and autoupdate:
        refresh_status()

    if request_ui_update:
        request_ui_update = False
        update_ui()

    if time.time() - countdown_update > 0.5:
        countdown_update = time.time()
        update_countdown_labels()
        update_stream_countdown_labels()

    root.after(100, periodic_refresh)


root = tk.Tk()
root.geometry("800x800")
root.configure(bg=COLOR_BG)
root.title("Space Balloon Mission Control Console")


# ------------------------------------------------------------
# Bereich Steuerung
# ------------------------------------------------------------
control_frame = ttk.LabelFrame(root, text="Steuerung")
control_frame.pack(fill="x", padx=10, pady=5)
control_frame.columnconfigure(0, weight=1)
control_frame.columnconfigure(1, weight=1)
control_frame.columnconfigure(2, weight=1)

realtime_button = tk.Button(control_frame, text="Realtime Modus (WiFi Verfügbar)", width=20, bg=COLOR_BUTTON, fg=COLOR_TEXT, relief="solid", bd=1, command=toggle_realtime)
realtime_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

autoupdate_button = tk.Button(control_frame, text="Auto Update (alle 20s)", width=20, bg=COLOR_BUTTON, fg=COLOR_TEXT, relief="solid", bd=1, command=toggle_autoupdate)
autoupdate_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

refresh_button = ttk.Button(control_frame, text="Jetzt aktualisieren", width=20, command=refresh_status)
refresh_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

# ------------------------------------------------------------
# Bereich Titel und Untertitel
# ------------------------------------------------------------
title_frame = ttk.LabelFrame(root, text="Titel und Untertitel")
title_frame.pack(fill="x", padx=10, pady=5)
title_frame.columnconfigure(1, weight=1)
ttk.Label(title_frame, text="Titel:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
titel_entry = ttk.Entry(title_frame, width=40)
titel_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
ttk.Label(title_frame, text="Untertitel:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
subtitle_entry = ttk.Entry(title_frame, width=40)
subtitle_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
update_title_button = ttk.Button(title_frame, text="Übernehmen", command=send_title)
update_title_button.grid(row=0, column=2, rowspan=2, padx=5, pady=5)
ttk.Label(title_frame, text="Preset:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
preset_var = tk.StringVar()
preset_dropdown = ttk.Combobox(title_frame, textvariable=preset_var, values=TITLES, state="readonly", width=40)
preset_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
apply_preset_button = ttk.Button(title_frame, text="Preset anwenden", command=apply_preset)
apply_preset_button.grid(row=2, column=2, padx=5, pady=5)
clear_title_button = ttk.Button(title_frame, text="Titel und Untertitel ausblenden", command=clear_title)
clear_title_button.grid(row=3, column=0, columnspan=3, padx=5, pady=5)
titel_entry.bind("<KeyRelease>", disable_autoupdate)
subtitle_entry.bind("<KeyRelease>", disable_autoupdate)

# ------------------------------------------------------------
# Bereich Countdown und Stream Countdown
# ------------------------------------------------------------
combined_countdown_frame = ttk.LabelFrame(root, text="Countdown und Stream Countdown")
combined_countdown_frame.pack(fill="x", padx=10, pady=5)

combined_countdown_frame.columnconfigure(0, weight=1)
for col in range(1, 9):
    combined_countdown_frame.columnconfigure(col, weight=1)

title_labels = ["", "Monat", "Tag", "Stunde", "Minute", "Sekunde", "", "Countdown (aktuell)", "Countdown (neu)"]
for col, text in enumerate(title_labels):
    if text:
        ttk.Label(combined_countdown_frame, text=text).grid(row=0, column=col, padx=5, pady=5)

ttk.Label(combined_countdown_frame, text="Countdown").grid(row=1, column=0, padx=5, pady=5)
countdown_month_entry = ttk.Entry(combined_countdown_frame, width=8)
countdown_month_entry.grid(row=1, column=1, padx=5, pady=5)
countdown_day_entry = ttk.Entry(combined_countdown_frame, width=8)
countdown_day_entry.grid(row=1, column=2, padx=5, pady=5)
countdown_hour_entry = ttk.Entry(combined_countdown_frame, width=8)
countdown_hour_entry.grid(row=1, column=3, padx=5, pady=5)
countdown_minute_entry = ttk.Entry(combined_countdown_frame, width=8)
countdown_minute_entry.grid(row=1, column=4, padx=5, pady=5)
countdown_second_entry = ttk.Entry(combined_countdown_frame, width=8)
countdown_second_entry.grid(row=1, column=5, padx=5, pady=5)
update_countdown_button = ttk.Button(combined_countdown_frame, text="Bestätigen", command=send_countdown)
update_countdown_button.grid(row=1, column=6, padx=5, pady=5)
countdown_label_active = ttk.Label(combined_countdown_frame, text="T-00:00:00")
countdown_label_active.grid(row=1, column=7, padx=5, pady=5)
countdown_label_new = ttk.Label(combined_countdown_frame, text="T-00:00:00")
countdown_label_new.grid(row=1, column=8, padx=5, pady=5)
countdown_month_entry.bind("<KeyRelease>", disable_autoupdate)
countdown_day_entry.bind("<KeyRelease>", disable_autoupdate)
countdown_hour_entry.bind("<KeyRelease>", disable_autoupdate)
countdown_minute_entry.bind("<KeyRelease>", disable_autoupdate)
countdown_second_entry.bind("<KeyRelease>", disable_autoupdate)

ttk.Label(combined_countdown_frame, text="Stream Countdown").grid(row=2, column=0, padx=5, pady=5)
stream_countdown_month_entry = ttk.Entry(combined_countdown_frame, width=8)
stream_countdown_month_entry.grid(row=2, column=1, padx=5, pady=5)
stream_countdown_day_entry = ttk.Entry(combined_countdown_frame, width=8)
stream_countdown_day_entry.grid(row=2, column=2, padx=5, pady=5)
stream_countdown_hour_entry = ttk.Entry(combined_countdown_frame, width=8)
stream_countdown_hour_entry.grid(row=2, column=3, padx=5, pady=5)
stream_countdown_minute_entry = ttk.Entry(combined_countdown_frame, width=8)
stream_countdown_minute_entry.grid(row=2, column=4, padx=5, pady=5)
stream_countdown_second_entry = ttk.Entry(combined_countdown_frame, width=8)
stream_countdown_second_entry.grid(row=2, column=5, padx=5, pady=5)
update_stream_countdown_button = ttk.Button(combined_countdown_frame, text="Bestätigen", command=send_stream_countdown)
update_stream_countdown_button.grid(row=2, column=6, padx=5, pady=5)
stream_countdown_label_active = ttk.Label(combined_countdown_frame, text="T-00:00:00")
stream_countdown_label_active.grid(row=2, column=7, padx=5, pady=5)
stream_countdown_label_new = ttk.Label(combined_countdown_frame, text="T-00:00:00")
stream_countdown_label_new.grid(row=2, column=8, padx=5, pady=5)
stream_countdown_month_entry.bind("<KeyRelease>", disable_autoupdate)
stream_countdown_day_entry.bind("<KeyRelease>", disable_autoupdate)
stream_countdown_hour_entry.bind("<KeyRelease>", disable_autoupdate)
stream_countdown_minute_entry.bind("<KeyRelease>", disable_autoupdate)
stream_countdown_second_entry.bind("<KeyRelease>", disable_autoupdate)

# ------------------------------------------------------------
# Bereich Live-Kamera Auswahl
# ------------------------------------------------------------
live_camera_frame = ttk.LabelFrame(root, text="Livekamera")
live_camera_frame.pack(fill="x", padx=10, pady=5)
for col in range(5):
    live_camera_frame.columnconfigure(col, weight=1)
for i in range(5):  # Kameras 0 bis 4
    btn = tk.Button(live_camera_frame,
                    text=f"Kamera {i}",
                    width=15,
                    bg=COLOR_BUTTON, fg=COLOR_TEXT,
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
                    bg=COLOR_BUTTON, fg=COLOR_TEXT,
                    relief="solid",
                    bd=1,
                    command=lambda idx=i: toggle_video_camera(idx))
    btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
    video_camera_buttons.append(btn)

# ------------------------------------------------------------
# Bereich Sensor Umschaltung
# ------------------------------------------------------------
sensor_frame = ttk.LabelFrame(root, text="Sensoren")
sensor_frame.pack(fill="x", padx=10, pady=5)
sensor_frame.columnconfigure(0, weight=1)
sensor_toggle_button = tk.Button(sensor_frame,
                                 text="Sensoren anzeigen",
                                 width=15,
                                 bg=COLOR_BUTTON, fg=COLOR_TEXT,
                                 relief="solid",
                                 bd=1,
                                 command=toggle_sensors)
sensor_toggle_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
update_sensor_button()

# ------------------------------------------------------------
# Bereich Quellen: Verbindungs- & Höhenquelle nebeneinander
# ------------------------------------------------------------
quellen_frame = ttk.Frame(root)
quellen_frame.pack(fill="x", padx=5, pady=5)
quellen_frame.columnconfigure(0, weight=1)
quellen_frame.columnconfigure(1, weight=1)

connection_frame = ttk.LabelFrame(quellen_frame, text="Verbindungsquelle")
connection_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
for col in range(2):
    connection_frame.columnconfigure(col, weight=1)
btn_wifi = tk.Button(connection_frame,
                      text="WiFi",
                      width=15,
                      bg=COLOR_BUTTON, fg=COLOR_TEXT,
                      relief="solid",
                      bd=1,
                      command=lambda: select_connection_source("wifi"))
btn_wifi.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
connection_buttons["wifi"] = btn_wifi
btn_aprs = tk.Button(connection_frame,
                      text="APRS",
                      width=15,
                      bg=COLOR_BUTTON, fg=COLOR_TEXT,
                      relief="solid",
                      bd=1,
                      command=lambda: select_connection_source("aprs"))
btn_aprs.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
connection_buttons["aprs"] = btn_aprs

height_frame = ttk.LabelFrame(quellen_frame, text="Höhenquelle")
height_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
height_frame.columnconfigure(0, weight=1)
height_frame.columnconfigure(2, weight=1)
btn_gps = tk.Button(height_frame,
                    text="GPS",
                    width=15,
                    bg=COLOR_BUTTON, fg=COLOR_TEXT,
                    relief="solid",
                    bd=1,
                    command=lambda: select_height_source("gps"))
btn_gps.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
height_buttons["gps"] = btn_gps
btn_climate = tk.Button(height_frame,
                        text="Climate",
                        width=15,
                        bg=COLOR_BUTTON, fg=COLOR_TEXT,
                        relief="solid",
                        bd=1,
                        command=lambda: select_height_source("climate"))
btn_climate.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
height_buttons["climate"] = btn_climate

# ------------------------------------------------------------
# Bereich Phase
# ------------------------------------------------------------
phase_frame = ttk.LabelFrame(root, text="Phase")
phase_frame.pack(fill="x", padx=10, pady=5)

phase_nav_frame = ttk.Frame(phase_frame)
phase_nav_frame.pack(fill="x", padx=10, pady=5)

back_button = ttk.Button(phase_nav_frame, text="Zurück", width=10,
                        command=phase_back)
back_button.pack(side="left", padx=5)

phase_display_frame = ttk.Frame(phase_nav_frame)
phase_display_frame.pack(side="left", expand=True, fill="x")

phases = ["Countdown", "Troposphäre", "Stratosphäre", "Sinkflug", "Rescue"]
phase_labels = []
for phase in phases:
    lbl = tk.Label(phase_display_frame, text=phase, relief="solid", bg=COLOR_BUTTON, fg=COLOR_TEXT, bd=1, width=12)
    lbl.pack(side="left", fill="x", expand=True, padx=5)
    phase_labels.append(lbl)

next_button = ttk.Button(phase_nav_frame, text="Weiter", width=10,
                        command=phase_next)
next_button.pack(side="right", padx=5)

# ------------------------------------------------------------
# Bereich Befehl (Rohbefehl ausführen)
# ------------------------------------------------------------
command_frame = ttk.LabelFrame(root, text="Befehl")
command_frame.pack(fill="x", padx=10, pady=5)
command_frame.columnconfigure(1, weight=1)

ttk.Label(command_frame, text="Beliebiger Befehl:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
raw_command_entry = ttk.Entry(command_frame)
raw_command_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
execute_command_button = ttk.Button(command_frame, text="Ausführen", command=execute_raw_command)
execute_command_button.grid(row=0, column=2, padx=5, pady=5)

# ------------------------------------------------------------
# Bereich Fußzeile
# ------------------------------------------------------------
footer_frame = ttk.Frame(root)
footer_frame.pack(side="bottom", fill="x", padx=10, pady=5)

left_footer = tk.Label(footer_frame, text="Space Balloon Mission Control Console (V3)", anchor="w", bg=COLOR_BG, fg=COLOR_TEXT)
left_footer.pack(side="left", fill="x", expand=True)

right_footer = tk.Label(footer_frame, text="Design von Nikolas Beyer und Felix Berg", anchor="e", bg=COLOR_BG, fg=COLOR_TEXT)
right_footer.pack(side="right", fill="x", expand=True)


def start():
    root.after(100, periodic_refresh)
    root.mainloop()
