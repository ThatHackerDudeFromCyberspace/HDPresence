import math
import os
import time
import urllib
import psutil
import requests
import json
import dbus

from activity_handler import ActivityHandler, HandlerContext, HandlerResponse
from discord_ipc import ACTIVITY_TYPE, DiscordActivity, DiscordActivityAssets, DiscordActivityButton, DiscordActivityImage, DiscordActivityTimestamps

class MPRISHandler(ActivityHandler):
    SERVICE_PREFIX = "org.mpris.MediaPlayer2"

    def __init__(self, context: HandlerContext):
        self.session_bus = context.session_bus

    def get_activity(self) -> DiscordActivity:
        for bus_name in self.session_bus.list_names():
            bus_name = str(bus_name)
            if (bus_name[:len(self.SERVICE_PREFIX)] == self.SERVICE_PREFIX):
                media_object = self.session_bus.get_object(bus_name, "/org/mpris/MediaPlayer2")
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
                artist = None
                if (len(artists) > 0):
                    artist = str(artists[0])
                cover_art = metadata.get("mpris:artUrl", None)
                length = metadata.get("mpris:length", 0) / 1000
                position = mediaplayer_properties.Get("org.mpris.MediaPlayer2.Player", "Position") / 1000
                status = mediaplayer_properties.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")

                if (str(status) != "Playing" or position >= length):
                    start = 1
                    end = length/1000 + 1
                else:
                    start = time.time()*1000 - position
                    end = start + length

                return HandlerResponse(
                    DiscordActivity(
                        str(name),
                        type = ACTIVITY_TYPE.LISTENING,
                        details=title,
                        details_url=f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(str(artist) + ' "' + str(title) + '"')}",
                        state=f"{artist} | {str(status)}",
                        timestamps=DiscordActivityTimestamps(
                            start=start,
                            end=end
                        )
                    ),
                    hash=f"{str(status)}:{str(name)}:{title}:{math.trunc(start/10000)}:{length}"
                )
        return HandlerResponse()



ACTIVITY_HANDLER = MPRISHandler