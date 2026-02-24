import os
import time
import psutil
import requests
import json

from activity_handler import ActivityHandler, HandlerContext, HandlerResponse, build_activity_from_format
from discord_ipc import ACTIVITY_TYPE, DiscordActivity, DiscordActivityAssets, DiscordActivityButton, DiscordActivityImage, DiscordActivityTimestamps

class SteamHandler(ActivityHandler):
    cache_path = "./cache/steam_handler/cache.json"
    
    def __init__(self, context: HandlerContext):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        self.api_key: str = context.config["steam_handler"]["api_key"]
        self.context = context
        self.cache = {}
        if (os.path.exists(self.cache_path)):
            with open(self.cache_path, "r") as file:
                self.cache = json.loads(file.read())
        else:
            with open("cache/steam_handler/cache.json", 'w') as file:
                file.write(json.dumps(self.cache))

    def get_app_infos(self, appids):
        to_request = []
        obtained = {}
        for appid in appids:
            appid = str(appid)
            if (appid in self.cache):
                obtained[appid] = self.cache[appid]
            else:
                to_request.append(appid)

        if (len(to_request) > 0):
            request_url = f"https://api.steampowered.com/ICommunityService/GetApps/v1/?key={self.api_key}"
            i = 0
            for i in range(len(to_request)):
                request_url += f"&appids%5B{i}%5D={to_request[i]}"
            response = requests.get(request_url)
            if (response.status_code != 200):
                print("ERROR: Could not obtain Steam app artwork")
                print(response.text)
                return {} # TODO
            data = response.json()["response"]
            for app in data["apps"]:
                obtained[str(app["appid"])] = app
                self.cache[str(app["appid"])] = app
            with open(self.cache_path, 'w') as file:
                file.write(json.dumps(self.cache))

        return obtained

    def get_responses(self) -> list[HandlerResponse]:
        running_games = []
        for proc in psutil.process_iter(['name', 'cmdline', 'create_time', 'pid']):
            if (proc.info["name"] == "reaper"):
                if (proc.info["cmdline"] == None):
                    continue
                for arg in proc.info["cmdline"]:
                    if ("AppId" in arg):
                        running_games.append((
                            arg.split('=')[-1],
                            proc.info["create_time"],
                            proc.info["cmdline"],
                            proc.info["pid"]
                        ))
        running_games.sort(key=lambda game: game[1]) # Sort by creation time
        running_games = running_games[-1::-1] # Flip
        
        app_infos = self.get_app_infos([game[0] for game in running_games])
        responses = []
        for game in running_games:
            appid = game[0]
            create_time = game[1]
            app_info = app_infos[appid]

            icon_url = ""
            header_image_url = ""
            store_url = ""
            if ("icon" in app_info.keys() and "name" in app_info.keys()):
                icon_url = f"https://shared.fastly.steamstatic.com/community_assets/images/apps/{appid}/{app_info['icon']}.jpg"
                header_image_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg" #f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg"
                store_url = f"https://store.steampowered.com/app/{appid}"
            else:
                app_info["name"] = os.path.basename(game[2][-1]).strip()
                if (app_info["name"][-4:] == ".exe"):
                    app_info["name"] = app_info["name"][:-4]

            activity = build_activity_from_format(
                ACTIVITY_TYPE.PLAYING,
                self.context.config["steam_handler"]["activity_format"],
                {
                    "name": app_info["name"],
                    "header_url": header_image_url,
                    "icon_url": icon_url,
                    "store_url": store_url
                }
            )
            activity.timestamps = DiscordActivityTimestamps(start=create_time*1000)
            responses.append(HandlerResponse(activity, pid=game[3]))
        return responses

ACTIVITY_HANDLER = SteamHandler