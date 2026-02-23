# HD Presence

## Example Config
```json
{
    "client_id": "Discord Application Client ID",
    "steam_api_key": "Optional Steam API Key (https://steamcommunity.com/dev/apikey)",
    "activity_refresh_time": 600,
    "activity_cooldown_time": 10,
    "server_url": "https://example.com",
    "server_auth_key": "[auth key here]",
    "enabled_handlers": [
        "mpris_handler",
        "steam_handler"
    ]
}
```

- `activity_refresh_time` is how often in seconds the activity will be sent to the Discord client if it hasn't changed (useful if another app is open that sends the activity multiple times)
- `activity_cooldown_time` is how long to wait between sending activity statuses (Discord seems to struggle if they are sent too frequently, ie, when quickly playing then immediately pausing media)
- `server_url` is the URL to the presence server (see the `server` folder)
- `server_auth_key` should match the `auth_key` configured for the server
- `enabled_handlers` - the list of enabled handlers in order of highest priority to least (it is recommended that media/"listening to" handlers are above "playing" handlers)