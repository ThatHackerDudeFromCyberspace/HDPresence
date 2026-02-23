import dbus
from discord_ipc import DiscordActivity, DiscordJSONEncoder
import json

class HandlerContext():
    def __init__(self, config, session_bus: dbus.SessionBus):
        self.config = config
        self.session_bus = session_bus

class HandlerResponse():
    def __init__(self, activity: DiscordActivity|None = None, hash: object = None):
        self.activity = activity
        if (hash == None):
            self.hash = json.dumps(self.activity, cls=DiscordJSONEncoder)
        else:
            self.hash = hash

    def get_hash(self) -> str:
        return self.hash
    
    def get_activity(self) -> DiscordActivity|None:
        return self.activity

class ActivityHandler():
    def __init__(self, context: HandlerContext):
        pass

    def get_response(self) -> HandlerResponse:
        pass