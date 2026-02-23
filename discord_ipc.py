###
# This file handles Discord IPC shennanigans
# Thanks to https://stackoverflow.com/questions/67339313/discord-interprocess-communication-read-messages
###

from abc import ABC, abstractmethod
import socket
import json
import os

class OPCODES():
    Handshake = 0
    Frame = 1
    Close = 2
    Ping = 3
    Pong = 4

class ACTIVITY_TYPE():
    PLAYING = 0
    STREAMING = 1 # Invalid for this!
    LISTENING = 2
    WATCHING = 3
    CUSTOM = 4 # Invalid for this!
    COMPETING = 5

    def to_string(activity_type: ACTIVITY_TYPE):
        if (activity_type == ACTIVITY_TYPE.PLAYING):
            return "playing"
        if (activity_type == ACTIVITY_TYPE.STREAMING):
            return "streaming"
        if (activity_type == ACTIVITY_TYPE.LISTENING):
            return "listening to"
        if (activity_type == ACTIVITY_TYPE.WATCHING):
            return "watching"
        if (activity_type == ACTIVITY_TYPE.COMPETING):
            return "competing in"

class ACTIVITY_FLAGS():
    INSTANCE	= 1 << 0
    JOIN	= 1 << 1
    SPECTATE	= 1 << 2
    JOIN_REQUEST	= 1 << 3
    SYNC	= 1 << 4
    PLAY	= 1 << 5
    PARTY_PRIVACY_FRIENDS	= 1 << 6
    PARTY_PRIVACY_VOICE_CHANNEL	= 1 << 7
    EMBEDDED	= 1 << 8

class STATUS_DISPLAY_TYPE():
    NAME = 0 # "Listening to Spotify"
    STATE = 1 # "Listening to Rick Astley"
    DETAILS = 2 # "Listening to Never Gonna Give You Up"

class DiscordJSONObject():
    @abstractmethod
    def to_json_object(self):
        pass

class DiscordJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, DiscordJSONObject)):
            return obj.to_json_object()
        return super().default(obj)

class DiscordActivityTimestamps(DiscordJSONObject):
    def __init__(self, start: int = None, end: int = None):
        self.start: int = start
        self.end: int = end
        
    def to_json_object(self):
        data = {}
        if (self.start != None):
            data["start"] = self.start
        if (self.end != None):
            data["end"] = self.end
        return data
    
class DiscordEmoji(DiscordJSONObject):
    def __init__(self, name: str, id: str = None, animated: bool = None):
        self.name: str = name
        self.id: str = id
        self.animated = animated

    def to_json_object(self):
        data = {
            "name": self.name,
        }
        if (self.id):
            data["id"] = self.id
        if (self.animated != None):
            data["animated"] = self.animated
        return data

class DiscordActivityParty(DiscordJSONObject):
    def __init__(self, current_size: int, max_size: int, id: str = None):
        self.current_size = current_size
        self.max_size = max_size
        self.id = id

    def to_json_object(self):
        data = {
            "size": [self.current_size, self.max_size]
        }
        if (self.id):
            data["id"] = self.id
        return data
    
class DiscordActivityImage():
    def __init__(self, image: str = None, text: str = None, url: str = None):
        self.image: str = image
        self.text: str = text
        self.url: str = url
    
class DiscordActivityAssets(DiscordJSONObject):
    def __init__(self, large_image: DiscordActivityImage = None, small_image: DiscordActivityImage = None, invite_cover_image: str = None):
        self.large_image: DiscordActivityImage = large_image
        self.small_image: DiscordActivityImage = small_image
        self.invite_cover_image: str = invite_cover_image
    
    def to_json_object(self):
        data = {}
        if (self.large_image != None):
            if (self.large_image.image != None):
                data["large_image"] = self.large_image.image
            if (self.large_image.text != None):
                data["large_text"] = self.large_image.text
            if (self.large_image.url != None):
                data["large_url"] = self.large_image.url
        if (self.small_image != None):
            if (self.small_image.image != None):
                data["small_image"] = self.small_image.image
            if (self.small_image.text != None):
                data["small_text"] = self.small_image.text
            if (self.small_image.url != None):
                data["small_url"] = self.small_image.url
        if (self.invite_cover_image != None):
            data["invite_cover_image"] = self.invite_cover_image
        return data

class DiscordActivitySecrets(DiscordJSONObject):
    def __init__(self, join: str = None, spectate: str = None, match: str = None):
        self.join: str = join
        self.spectate: str = spectate
        self.match: str = match

    def to_json_object(self):
        data = {}
        if (self.join != None):
            data["join"] = self.join
        if (self.spectate != None):
            data["spectate"] = self.spectate
        if (self.match != None):
            data["match"] = self.match

class DiscordActivityButton(DiscordJSONObject):
    def __init__(self, label: str, url: str):
        self.label: str = label
        self.url: str = url

    def to_json_object(self):
        return {
            "label": self.label,
            "url": self.url
        }

class DiscordActivity(DiscordJSONObject):
    def __init__(self,
                 name: str,
                 type: int = ACTIVITY_TYPE.PLAYING,
                 timestamps: DiscordActivityTimestamps = None,
                 application_id: str = None, # @TODO: Are snowflakes a string?
                 status_display_type: STATUS_DISPLAY_TYPE = STATUS_DISPLAY_TYPE.NAME,
                 details: str = None,
                 details_url: str = None,
                 state: str = None,
                 state_url: str =  None,
                 emoji: DiscordEmoji = None,
                 party: DiscordActivityParty = None,
                 assets: DiscordActivityAssets = None,
                 secrets: DiscordActivitySecrets = None,
                 instance: bool = None,
                 flags: int = None,
                 buttons: list[DiscordActivityButton] = None
                ):
        self.name = name
        self.type = type
        self.timestamps = timestamps
        self.application_id = application_id
        self.status_display_type = status_display_type
        self.details = details
        self.details_url = details_url
        self.state = state
        self.state_url = state_url
        self.emoji = emoji
        self.party = party
        self.assets = assets
        self.secrets = secrets
        self.instance = instance
        self.flags = flags
        self.buttons = buttons
        if (self.buttons == None):
            self.buttons = []

    def to_json_object(self):
        data = {
            "name": self.name,
            "type": self.type,
        }

        if (self.timestamps != None):
            data["timestamps"] = self.timestamps.to_json_object()

        if (self.application_id != None):
            data["application_id"] = self.application_id

        if (self.status_display_type != None):
            data["status_display_type"] = self.status_display_type

        if (self.details != None):
            data["details"] = self.details

        if (self.details_url != None):
            data["details_url"] = self.details_url

        if (self.state != None):
            data["state"] = self.state

        if (self.state_url != None):
            data["state_url"] = self.state_url

        if (self.emoji != None):
            data["emoji"] = self.emoji.to_json_object()

        if (self.party != None):
            data["party"] = self.party.to_json_object()

        if (self.assets != None):
            data["assets"] = self.assets.to_json_object()

        if (self.secrets != None):
            data["secrets"] = self.secrets.to_json_object()

        if (self.instance != None):
            data["instance"] = self.instance

        if (self.flags != None):
            data["flags"] = self.flags

        if (len(self.buttons) > 0):
            data["buttons"] = []
            for button in self.buttons:
                data["buttons"].append(button.to_json_object())

        return data


class DiscordIPC():
    def _create_packet(opcode: int, payload):
        data = []
        payload_bytes = json.dumps(payload, cls=DiscordJSONEncoder).encode('utf-8')
        data.extend(opcode.to_bytes(4, 'little', signed=False))
        data.extend(len(payload_bytes).to_bytes(4, 'little', signed=False))
        return bytes(data) + payload_bytes
    
    def __init__(self, client_id):
        self.client_id = client_id

        discord_socket_path = None
        for file in os.listdir(runtime_dir):
            if ("discord-ipc" in file):
                discord_socket_path = os.path.join(runtime_dir, file)
                break
        if (discord_socket_path == None):
            raise Exception("Could not find Discord socket path!")

        self.discord_socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.discord_socket.connect(discord_socket_path)
        self._handshake()

    def send(self, opcode, payload):
        self.discord_socket.send(DiscordIPC._create_packet(opcode, payload))

    def wait_valid_response(self):
        received = None
        buffer = b''
        while (received == None or len(received) != 0):
            received = self.discord_socket.recv(1)
            buffer += received
            try:
                fixed_buffer = buffer[buffer.index(b'{'):].split(b'\x00')[-1]
                data = json.loads(fixed_buffer)
                return data
            except Exception as e:
                pass

    def _handshake(self):
        self.send(0, {
            "v": 1,
            "client_id": self.client_id
        })

        print("Waiting for Discord to respond")
        self.wait_valid_response()

runtime_dir = os.environ["XDG_RUNTIME_DIR"]