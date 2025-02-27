# Use in AutoKey
# Setup Keyboard Shortcut in Ubuntu Settings
# Run with autokey-run as command

# THIS TRASH IMPLEMENTATION WAS DONE IN HELL


import threading
import time
import subprocess


if 'workspace_cycle_active' not in store:
    store['workspace_cycle_active'] = False
if 'running_cycle' not in store:
    store['running_cycle'] = False


def left_mon():

    for i in range(40):
        subprocess.call(["sudo", "ydotool", "mousemove", "--", "-100", "0"])


def right_mon():

    for i in range(40):
        subprocess.call(["sudo", "ydotool", "mousemove", "--", "100", "0"])


def mouse_pos_left(xpos, ypos):

    subprocess.call(["sudo", "ydotool", "mousemove", "-a", "--", str(xpos), "0"])
    subprocess.call(["sudo", "ydotool", "mousemove", "--", "0", str(ypos)])


def mouse_pos_right(xpos, ypos):

    subprocess.call(["sudo", "ydotool", "mousemove", "-a", "--", "0", "100"])
    subprocess.call(["sudo", "ydotool", "mousemove", "--", str(xpos), "0"])
    subprocess.call(["sudo", "ydotool", "mousemove", "--", "0", str(ypos-100)])


def mouse_click():

    subprocess.call(["sudo", "ydotool", "click", "C0"])


def smart_sleep(seconds):

    for i in range(seconds):
        time.sleep(1)
        if not store.get('workspace_cycle_active', False):
            return True


def cycle_workspaces():

    store['running_cycle'] = True

    while store.get('workspace_cycle_active', False):
        try:
            output = subprocess.check_output(["wmctrl", "-d"]).decode("utf-8")
            desktops = output.splitlines()
            num_desktops = len(desktops)
            current_workspace = None
            for line in desktops:
                if '*' in line:
                    current_workspace = int(line.split()[0])
                    break
            if current_workspace is None:
                current_workspace = 0
            next_workspace = (current_workspace + 1) % (num_desktops - 3)
            subprocess.call(["wmctrl", "-s", str(next_workspace)])
            if next_workspace == 0:
                video = subprocess.Popen(["mpv", "--fs", "/home/maker/SpaceBalloonEventTrailerJufo.mp4"])
                while video.poll() is None:
                    if not store.get('workspace_cycle_active', False):
                        break
                    time.sleep(1)
                video.terminate()
            elif next_workspace == 1:
                if smart_sleep(1): continue
                left_mon()
                mouse_pos_left(250, 1180)
                mouse_click()
                if smart_sleep(1): continue
                right_mon()
                mouse_pos_right(1820, 20)
                mouse_click()
                if smart_sleep(10): continue
                right_mon()
                mouse_pos_right(1820, 20)
                mouse_click()
                if smart_sleep(10): continue
                right_mon()
                mouse_pos_right(1820, 20)
                mouse_click()
                if smart_sleep(10): continue
                left_mon()
                mouse_pos_left(50, 1180)
                mouse_click()
                if smart_sleep(1): continue
            elif next_workspace == 2:
                if smart_sleep(1): continue
                left_mon()
                mouse_pos_left(1820, 20)
                mouse_click()
                if smart_sleep(1): continue
                right_mon()
                mouse_pos_right(1820, 20)
                mouse_click()
                if smart_sleep(10): continue
                left_mon()
                mouse_pos_left(1820, 20)
                mouse_click()
                if smart_sleep(1): continue
                right_mon()
                mouse_pos_right(1820, 20)
                mouse_click()
                if smart_sleep(10): continue
                left_mon()
                mouse_pos_left(1820, 20)
                mouse_click()
                if smart_sleep(1): continue
                right_mon()
                mouse_pos_right(1820, 20)
                mouse_click()
                if smart_sleep(10): continue
            elif next_workspace == 3:
                if smart_sleep(1): continue
                left_mon()
                mouse_pos_left(1820, 20)
                mouse_click()
                if smart_sleep(1): continue
                right_mon()
                mouse_pos_right(870, 150)
                mouse_click()
                if smart_sleep(10): continue
                left_mon()
                mouse_pos_left(1820, 20)
                mouse_click()
                if smart_sleep(1): continue
                right_mon()
                mouse_pos_right(870, 150)
                mouse_click()
                if smart_sleep(10): continue
                left_mon()
                mouse_pos_left(1820, 20)
                mouse_click()
                if smart_sleep(1): continue
                right_mon()
                mouse_pos_right(870, 150)
                mouse_click()
                if smart_sleep(10): continue
            else:
                time.sleep(4)
        except Exception as e:
            time.sleep(30)

    store['running_cycle'] = False


if not store['workspace_cycle_active']:
    store['workspace_cycle_active'] = True
    if not store.get('running_cycle', False):
        t = threading.Thread(target=cycle_workspaces, daemon=True)
        t.start()
    #dialog.info_dialog("Space Balloon Jufo", "Workspace cycling ENABLED")
else:
    store['workspace_cycle_active'] = False
    dialog.info_dialog("Space Balloon Jufo", "Workspace cycling DISABLED")
