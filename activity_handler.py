import dbus
from discord_ipc import ACTIVITY_TYPE, DiscordActivity, DiscordActivityAssets, DiscordActivityButton, DiscordActivityImage, DiscordJSONEncoder
import json

def build_activity_from_format(type: ACTIVITY_TYPE, format: dict[str, str|int], data: dict[str, object]) -> DiscordActivity:
    activity = DiscordActivity(format["name"].format(**data), type)
    if (format["details"]):
        activity.details = format["details"].format(**data)
    if (format["details_url"]):
        activity.details_url = format["details_url"].format(**data)
    if (format["state"]):
        activity.state = format["state"].format(**data)
    if (format["state_url"]):
        activity.state_url = format["state_url"].format(**data)
    activity.status_display_type = format["status_display_type"]
    if (format["large_image"].format(**data) or format["small_image"].format(**data)):
        activity.assets = DiscordActivityAssets()
        if (format["large_image"].format(**data)):
            activity.assets.large_image = DiscordActivityImage(
                format["large_image"].format(**data),
                format["large_image_text"].format(**data) if format["large_image_text"] else None,
                format["large_image_url"].format(**data) if format["large_image_url"] else None
            )
        if (format["small_image"].format(**data)):
            activity.assets.small_image = DiscordActivityImage(
                format["small_image"].format(**data),
                format["small_image_text"].format(**data) if format["small_image_text"] else None,
                format["small_image_url"].format(**data) if format["small_image_url"] else None
            )
    if (len(format["buttons"]) > 0):
        for button in format["buttons"]:
            if (button["url"]):
                activity.buttons.append(DiscordActivityButton(
                    button["label"].format(**data),
                    button["url"].format(**data)
                ))
    return activity

class HandlerContext():
    def __init__(self, config, session_bus: dbus.SessionBus):
        self.config = config
        self.session_bus = session_bus

class HandlerResponse():
    def __init__(self, activity: DiscordActivity|None = None, hash: str = None, prefix: str = None, pid: int = None):
        self.activity = activity
        if (hash == None):
            self.hash: str = json.dumps(self.activity, cls=DiscordJSONEncoder)
        else:
            self.hash: str = hash
        self.prefix: str|None = prefix
        self.pid: int|None = pid

    def get_pid(self) -> int|None:
        return self.pid

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