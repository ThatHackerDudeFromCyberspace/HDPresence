import dbus
from discord_ipc import DiscordActivity

class ActivityContext():
    def __init__(self, config, session_bus: dbus.SessionBus):
        self.config = config
        self.session_bus = session_bus

class ActivityHandler():
    def __init__(self, context: ActivityContext):
        pass

    def get_activity(self) -> DiscordActivity:
        pass