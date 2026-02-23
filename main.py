import json
from activity_handler import ActivityContext, ActivityHandler
from discord_ipc import DiscordIPC, DiscordJSONEncoder
import importlib
import uuid
import time
import dbus
import os

os.makedirs("cache", exist_ok=True)
PID = os.getpid()
config = {}
with open("./config.json", 'r') as file:
    config = json.loads(file.read())

discord = DiscordIPC(config["client_id"])

print("Connecting to dbus...")
session_bus = dbus.SessionBus()

activity_context = ActivityContext(config, session_bus)

print("Loading activity handlers...")
handlers: list[ActivityHandler] = []
for file in os.listdir("activity_handlers"):
    if (not ".py" == file[-3:]):
        continue

    handler_name = file[:-3]
    print(f"- {handler_name}")
    handler_lib = importlib.import_module(f"activity_handlers.{handler_name}")
    handler = getattr(handler_lib, "ACTIVITY_HANDLER", None)
    if (handler == None):
        print(f"ERROR: Could not load handler {handler_name} - Missing ACTIVITY_HANDLER")
        continue
    handlers.append(handler(activity_context))

print("\nDone.\n")
last_activity = None
last_activity_ping = 0
while True:
    should_send_activity = time.time() - last_activity_ping > config["activity_refresh_time"]
    sent_activity = False
    for handler in handlers:
        activity = handler.get_activity()
        if (activity == None):
            continue
        if (not should_send_activity and json.dumps(activity, cls=DiscordJSONEncoder) == last_activity):
            sent_activity = True # don't spam discord
            break
        
        print("Sending new activity!")
        discord.send(1, {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": PID,
                "activity": activity
            },
            "nonce": str(uuid.uuid4())
        })
        response = discord.wait_valid_response()
        last_activity = json.dumps(activity, cls=DiscordJSONEncoder)
        last_activity_ping = time.time()
        if (response["evt"] != "ERROR"):
            sent_activity = True
            break
        else:
            print(f"ERROR: {response}")

    if (not sent_activity and (last_activity != None or should_send_activity)):
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
        last_activity = None
        last_activity_ping = time.time()