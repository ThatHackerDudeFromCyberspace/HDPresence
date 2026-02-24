import math
import time
import urllib
import urllib.parse
import requests
import dbus

from activity_handler import ActivityHandler, HandlerContext, HandlerResponse, build_activity_from_format
from discord_ipc import ACTIVITY_TYPE, STATUS_DISPLAY_TYPE, DiscordActivity, DiscordActivityAssets, DiscordActivityButton, DiscordActivityImage, DiscordActivityTimestamps

class Player():
    def __init__(self,
                 name: str,
                 title: str|None,
                 artists: list[str],
                 cover_art_url: str|None,
                 length: int,
                 position: int,
                 status: str,
                 pid: int
                ):
        self.name = name
        self.title = title
        self.artists = artists
        self.cover_art_url = cover_art_url
        self.length = length
        self.position = position
        self.status = status
        self.pid = pid

    def get_artist(self):
        if (len(self.artists) == 0):
            return None
        return self.artists[0]
    
    def get_start(self):
        if (self.status != "Playing" or self.position >= self.length):
            return 1
        else:
            return round(time.time()*1000 - self.position, 2)
    
    def get_end(self):
        if (self.status != "Playing" or self.position >= self.length):
            return round(self.length/1000 + 1, 2)
        else:
            start = round(time.time()*1000 - self.position, 2)
            return start + self.length
        
    def get_status(self):
        return self.status
    
    def get_name(self):
        return self.name
    
    def get_title(self):
        return self.title
    
    def get_length(self):
        return self.length
    
    def get_pid(self):
        return self.pid

    def get_response_hash(self):
        # Used to return the activity-specific hash - we divide start by 10000 to avoid weird jitter that happens sometimes when unpausing
        return f"{str(self.get_status())}:{str(self.get_name())}:{self.get_title()}:{math.trunc(self.get_start()/10000)}:{self.get_length()}:{str(self.cover_art_url)}"
    
    def upload_cover(self, upload_endpoint, auth_key):
        if (self.cover_art_url == None):
            return None
        
        cover_art_url = str(self.cover_art_url)
        if (cover_art_url[:len("file://")] != "file://"):
            return cover_art_url
        
        cover_art_path = urllib.parse.unquote_plus(cover_art_url[len("file://"):])
        try:
            response = requests.post(f"{upload_endpoint}", files={"file": open(cover_art_path, 'rb')}, headers={"authorization": f"Bearer {auth_key}"})
            if (response.status_code != 200):
                return None
            return upload_endpoint + '/' + response.json()["path"]
        except Exception as e:
            return None

    

class MPRISHandler(ActivityHandler):
    SERVICE_PREFIX = "org.mpris.MediaPlayer2"

    def __init__(self, context: HandlerContext):
        self.context = context

    def get_response(self) -> HandlerResponse:
        session_bus = self.context.session_bus
        players: list[Player] = []
        for bus_name in session_bus.list_names():
            bus_name = str(bus_name)
            if (bus_name[:len(self.SERVICE_PREFIX)] == self.SERVICE_PREFIX): # See: https://specifications.freedesktop.org/mpris/latest/
                media_object = session_bus.get_object(bus_name, "/org/mpris/MediaPlayer2")
                mediaplayer_properties = dbus.Interface(media_object, dbus_interface="org.freedesktop.DBus.Properties")
                player_name = mediaplayer_properties.Get("org.mpris.MediaPlayer2", "Identity")
                metadata = mediaplayer_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
                if (not "mpris:trackid" in metadata):
                    continue
                name = player_name
                title = metadata.get("xesam:title", None)
                if (title != None):
                    title = str(title)
                artists = metadata.get("xesam:artist", [])
                cover_art_url = metadata.get("mpris:artUrl", None)
                length = metadata.get("mpris:length", 1000000) / 1000 # Measured in microseconds but we want millis
                position = mediaplayer_properties.Get("org.mpris.MediaPlayer2.Player", "Position") / 1000
                status = mediaplayer_properties.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")

                # Get the PID
                dbus_object = session_bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
                dbus_interface = dbus.Interface(dbus_object, dbus_interface="org.freedesktop.DBus")
                pid = dbus_interface.GetConnectionUnixProcessID(bus_name)

                # We store a list of players so we can select the best one!
                players.append(
                    Player(
                        str(name),
                        title,
                        [str(artist) for artist in artists],
                        cover_art_url,
                        int(length),
                        int(position),
                        str(status),
                        int(pid)
                    )
                )

        if (len(players) == 0):
            return HandlerResponse()

        selected_player = players[0]
        for player in players:
            if (player.get_status() == "Playing"):
                selected_player = player
                break
            if (player.get_start() > selected_player.get_start()):
                selected_player = player

        if (selected_player.get_status() != "Playing"):
            if (len(players) > 1):
                return HandlerResponse()

        cover_url = selected_player.upload_cover(self.context.config["general"]["server_url"], self.context.config["general"]["server_auth_key"])
        activity = build_activity_from_format(
            ACTIVITY_TYPE.LISTENING,
            self.context.config["mpris_handler"]["activity_format"],
            {
                "name": selected_player.get_name(),
                "title": selected_player.get_title(),
                "artist": selected_player.get_artist(),
                "status": selected_player.get_status(),
                "url": f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(str(selected_player.get_artist()) + ' "' + str(selected_player.get_title()) + '"')}",
                "cover_url": cover_url if cover_url else ""
            }
        )

        activity.timestamps=DiscordActivityTimestamps(
            start=selected_player.get_start(),
            end=selected_player.get_end()
        )        
        
        return HandlerResponse(
            activity,
            hash=selected_player.get_response_hash(),
            pid=selected_player.get_pid()
        )



ACTIVITY_HANDLER = MPRISHandler