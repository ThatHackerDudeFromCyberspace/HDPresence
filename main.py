import json
from activity_handler import HandlerContext, ActivityHandler, HandlerResponse
from discord_ipc import ACTIVITY_TYPE, DiscordActivityAssets, DiscordIPC, DiscordJSONEncoder
import tomllib
import importlib
import uuid
import time
import dbus
import os

os.makedirs("cache", exist_ok=True)
PID = os.getpid()
config = None
with open("./config.toml", 'rb') as file:
    config = tomllib.load(file)

discord = DiscordIPC(config["general"]["client_id"])

print("Connecting to dbus...")
session_bus = dbus.SessionBus()

handler_context = HandlerContext(config, session_bus)

print("Loading activity handlers...")
handlers: dict[str, ActivityHandler] = {}
for file in os.listdir("activity_handlers"):
    if (not ".py" == file[-3:]):
        continue

    handler_name = file[:-3]
    if (not handler_name in config["general"]["enabled_handlers"]):
        continue

    print(f"- {handler_name}")
    handler_lib = importlib.import_module(f"activity_handlers.{handler_name}")
    handler = getattr(handler_lib, "ACTIVITY_HANDLER", None)
    if (handler == None):
        print(f"ERROR: Could not load handler {handler_name} - Missing ACTIVITY_HANDLER")
        continue
    handlers[handler_name] = handler(handler_context)

print("\nDone.\n")
last_activity_hash = None
last_activity_ping = 0
while True:
    should_update_activity = time.time() - last_activity_ping > config["general"]["activity_refresh_time"]
    if (last_activity_hash != None and time.time() - last_activity_ping < config["general"]["activity_cooldown_time"]):
        time.sleep(config["general"]["activity_cooldown_time"] - (time.time() - last_activity_ping)) # Cooldown or Discord won't respect our updates at all!
        continue

    activity = None
    sent_activity = False
    cumulative_hash = ""
    handled_pids = []
    for handler_name in config["general"]["enabled_handlers"]:
        handler = handlers[handler_name]
        handler_response = handler.get_response()
        response_hash = handler_response.get_hash()
        response_pid = handler_response.get_pid()
        response_activity = handler_response.get_activity()
        if (response_activity == None or response_hash == None):
            continue
        if (response_pid in handled_pids): # Don't have one handler accidentally do the same application
            continue

        cumulative_hash += response_hash
        handled_pids.append(response_pid)
        if (activity == None):
            activity = response_activity
            continue

        activity.name += f" whilst {handler_response.get_prefix()} " + response_activity.name
        activity.buttons.extend(response_activity.buttons)
        activity.buttons = activity.buttons[:2] # Max of two items!!!
        if (response_activity.assets != None):
            if (activity.assets == None):
                activity.assets = DiscordActivityAssets()

            image_to_use = response_activity.assets.large_image
            if (response_activity.assets.small_image != None):
                image_to_use = response_activity.assets.small_image

            if (image_to_use.text == None):
                image_to_use.text = response_activity.name

            if (activity.assets.large_image != None):
                activity.assets.small_image = image_to_use
            else:
                activity.assets.large_image = image_to_use
        break # We only allow two at most! @TODO Add support for more?

    if (activity != None and (should_update_activity or cumulative_hash != last_activity_hash)):
        print("Sending new activity!")
        #print(json.dumps(activity_response.get_activity(), cls=DiscordJSONEncoder))
        discord.send(1, {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": PID,
                "activity": activity
            },
            "nonce": str(uuid.uuid4())
        })
        response = discord.wait_valid_response()
        last_activity_hash = cumulative_hash
        last_activity_ping = time.time()
        if (response["evt"] != "ERROR"):
            sent_activity = True
        else:
            print(f"ERROR: {response}")

    if (activity == None and (should_update_activity or last_activity_hash != None)):
        print("Clearing last activity!")
        discord.send(1, {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": PID,
                "activity": None
            },
            "nonce": str(uuid.uuid4())
        })
        response = discord.wait_valid_response()
        last_activity_hash = None
        last_activity_ping = time.time()