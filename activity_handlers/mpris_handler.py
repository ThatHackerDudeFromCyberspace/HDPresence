import os
import time
import psutil
import requests
import json
import dbus

from activity_handler import ActivityContext, ActivityHandler
from discord_ipc import ACTIVITY_TYPE, DiscordActivity, DiscordActivityAssets, DiscordActivityButton, DiscordActivityImage, DiscordActivityTimestamps

class MPRISHandler(ActivityHandler):
    SERVICE_PREFIX = "org.mpris.MediaPlayer2"

    def __init__(self, context: ActivityContext):
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
                artists = metadata.get("xesam:artist", [])
                artist = None
                if (len(artists) > 0):
                    artist = str(artists[0])
                cover_art = metadata.get("mpris:artUrl", None)
                length = metadata.get("mpris:length", 0) / 1000
                position = mediaplayer_properties.Get("org.mpris.MediaPlayer2.Player", "Position") / 1000
                status = mediaplayer_properties.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")

                if (str(status) != "Playing"):
                    start = 1
                    end = length/1000 + 1
                else:
                    start = (time.time()*1000 - position) // 1000 * 1000
                    end = (start + length) // 1000 * 1000

                return DiscordActivity(
                    str(name),
                    type = ACTIVITY_TYPE.LISTENING,
                    details=title,
                    state=f"{artist} | {str(status)}",
                    timestamps=DiscordActivityTimestamps(
                        start=start,
                        end=end
                    )
                )



ACTIVITY_HANDLER = MPRISHandler