import dbus
from discord_ipc import ACTIVITY_TYPE, DiscordActivity, DiscordJSONEncoder
import json

class HandlerContext():
    def __init__(self, config, session_bus: dbus.SessionBus):
        self.config = config
        self.session_bus = session_bus

class HandlerResponse():
    def __init__(self, activity: DiscordActivity|None = None, hash: str = None, prefix: str = None):
        self.activity = activity
        if (hash == None):
            self.hash: str = json.dumps(self.activity, cls=DiscordJSONEncoder)
        else:
            self.hash: str = hash
        self.prefix: str|None = prefix

    def get_prefix(self) -> str:
        if (self.prefix != None):
            return self.prefix
        if (self.activity != None):
            return ACTIVITY_TYPE.to_string(self.activity.type)
        return "using"

    def get_hash(self) -> str:
        return self.hash
    
    def get_activity(self) -> DiscordActivity|None:
        return self.activity

class ActivityHandler():
    def __init__(self, context: HandlerContext):
        pass

    def get_response(self) -> HandlerResponse:
        pass