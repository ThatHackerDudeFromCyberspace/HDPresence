# HD Presence

## Example Config
```json
{
    "client_id": "Discord Application Client ID",
    "steam_api_key": "Optional Steam API Key (https://steamcommunity.com/dev/apikey)",
    "activity_refresh_time": 600,
    "activity_cooldown_time": 5
}
```

- `activity_refresh_time` is how often in seconds the activity will be sent to the Discord client if it hasn't changed (useful if another app is open that sends the activity multiple times)
- `activity_cooldown_time` is how long to wait between sending activity statuses (Discord seems to struggle if they are sent too frequently, ie, when quickly playing then immediately pausing media)