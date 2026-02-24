import os
import time
import psutil
import requests
import json
import configparser

from activity_handler import ActivityHandler, HandlerContext, HandlerResponse, build_activity_from_format
from discord_ipc import ACTIVITY_TYPE, DiscordActivity, DiscordActivityAssets, DiscordActivityButton, DiscordActivityImage, DiscordActivityTimestamps

DESKTOP_FOLDER_PATHS = [
    "/usr/share/applications",
    "~/.local/share/applications/"
]

ICON_FOLDER_PATHS = [
    "/usr/share/icons",
    "~/.local/share/icons"
]

class DesktopFile():
    def __init__(self, filename: str, type: str, name: str, generic_name: str|None = None, exec: str|None = None, logo: str|None = None):
        self.filename = filename
        self.type = type
        self.name = name
        self.generic_name = generic_name
        self.exec = exec
        self.logo = logo

class DesktopFileHandler():
    def __init__(self, folder_paths: list[str]):
        self.folder_paths = folder_paths
        self.desktop_files: dict[str, DesktopFile] = {}

        for path in self.folder_paths:
            for root, dirs, files in os.walk(path):
                for filename in files:                
                    filepath = os.path.join(root, filename)
                    desktop_file = configparser.ConfigParser(interpolation=None)
                    desktop_file.read(filepath)
                    self.desktop_files[filename] = DesktopFile(
                        filename,
                        desktop_file["Desktop Entry"].get("type", "Application"),
                        desktop_file["Desktop Entry"].get("name", filename[:-len(".desktop")]),
                        desktop_file["Desktop Entry"].get("generic_name", None),
                        desktop_file["Desktop Entry"].get("exec", None),
                        desktop_file["Desktop Entry"].get("logo", None)
                    )

class WindowHandler():
    def __init__(self, context: HandlerContext):
        self.context = context

    def getPIDInfo(self):
        # list windows
        # return (is_window, is_active)
        pass

class ProcessHandler(ActivityHandler):    
    def __init__(self, context: HandlerContext):
        self.context = context

    def get_responses(self) -> list[HandlerResponse]:
        processes: dict[str, list[dict]] = {}
        whitelist = self.context.config["process_handler"]["whitelist"]
        blacklist = self.context.config["process_handler"]["blacklist"]

        for proc in psutil.process_iter(['name', 'cmdline', 'create_time', 'pid', 'status']):
            if (proc.info["cmdline"] == None or len(proc.info["cmdline"]) == 0):
                continue
            if (proc.info["status"] in [psutil.STATUS_DISK_SLEEP,
                                        psutil.STATUS_STOPPED,
                                        psutil.STATUS_TRACING_STOP,
                                        psutil.STATUS_ZOMBIE,
                                        psutil.STATUS_DEAD,
                                        psutil.STATUS_PARKED]):
                print(proc.info["status"])
                continue

            name = proc.info["name"].lower()
            executable = proc.info["cmdline"][0]
            if (executable in blacklist or name in blacklist):
                continue
            if (whitelist != None and not (executable in whitelist or name in whitelist)):
                continue

            if (not name in processes):
                processes[name] = []
            processes[name].append(proc.info)

        name_overrides: dict[str, str] = {}
        prefix_overrides: dict[str, str] = {}
        icon_overrides: dict[str, str] = {}
        for name_override in self.context.config["process_handler"]["name_overrides"]:
            name_overrides[name_override[0]] = name_override[1]
        for prefix_override in self.context.config["process_handler"]["prefix_overrides"]:
            prefix_overrides[prefix_override[0]] = prefix_override[1]
        for icon_override in self.context.config["process_handler"]["icon_overrides"]:
            icon_overrides[icon_override[0]] = icon_override[1]

        sorted_processes = [process_name for process_name in processes]
        sorted_processes.sort(key=lambda process_name: processes[process_name][0]["create_time"])
        sorted_processes = sorted_processes[-1::-1]

        
        responses = []
        for process_name in sorted_processes:
            icon_url = ""
            process = processes[process_name][0]

            icon_path = ""
            if (self.context.config["process_handler"]["upload_icons"]):
                icon_path = icon_overrides.get(process_name, icon_path)
                try:
                    response = requests.post(f"{self.context.config["general"]["server_url"]}", files={"file": open(icon_path, 'rb')}, headers={"authorization": f"Bearer {self.context.config["general"]["server_auth_key"]}"})
                    if (response.status_code != 200):
                        return None
                    icon_url = self.context.config["general"]["server_url"] + '/' + response.json()["path"]
                except Exception as e:
                    pass


            activity = build_activity_from_format(
                ACTIVITY_TYPE.PLAYING,
                self.context.config["process_handler"]["activity_format"],
                {
                    "name": name_overrides.get(process_name, process_name),
                    "window_title": name_overrides.get(process_name, process_name),
                    "icon_url": icon_url
                }
            )

            activity.timestamps = DiscordActivityTimestamps(
                start=process["create_time"]*1000
            )

            responses.append(HandlerResponse(
                activity,
                prefix=prefix_overrides.get(process_name, "playing"),
                pid=process["pid"]
            ))

        return responses
        
ACTIVITY_HANDLER = ProcessHandler