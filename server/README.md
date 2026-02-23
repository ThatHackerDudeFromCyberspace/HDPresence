# Server
This server acts as a proxy needed for uploading cover art so Discord can retrieve it from a public-facing URL

## Config.json
There should be a config.json file accessible at `/opt/hd_presence/config.json` in the container, the contents should be as follows:

```json
{
    "client_auth_key": "[authentication key]"
}
```

It should match the authenticatoin key in the client's `config.json` - This will be used to ensure only the clients you want can connect and upload images

## Other Paths
Images will be uploaded, cached and served from `/opt/hd_presence/cache`