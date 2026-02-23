from flask import Flask, request, send_file
from PIL import Image
import hashlib
import uuid
import json
import os

print("Reading config file...")
config = {}
try:
    with open("./config.json", 'r') as file:
        config = json.loads(file.read())
    assert("auth_key" in config)
except:
    print("Could not read config file! - Generating new one")
    config["auth_key"] = str(uuid.uuid4())
    with open("./config.json", "w") as file:
        file.write(json.dumps(config))
    print(f"GENERATED AUTH KEY: {config['auth_key']}")

def hashImage(image: Image.Image):
    m = hashlib.sha256()
    m.update(image.tobytes())
    return m.hexdigest()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

os.makedirs("cache/images", exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if (request.headers.get("authorization", "").split(" ")[-1] != config["auth_key"]):
        return "UNAUTHORIZED", 403
    
    if (request.method == "POST"):
        # check if the post request has the file part
        if 'file' not in request.files:
            return "Invalid Upload Request", 400
        file = request.files['file']
        image = Image.open(file.stream)
        image_id = hashImage(image)
        path = f"./cache/images/{image_id}.png"
        new = False
        if (not os.path.exists(path)):
            image.save(path)
            new = True
        return {
            "path": f"/{image_id}.png",
            "new": new
        }
    return "<a href=\"https://github.com/ThatHackerDudeFromCyberspace/HDPresence\">HDPresence Server</a>"

@app.route("/<image_filename>", methods=["GET", "DELETE"])
def image_handler(image_filename):
    for forbidden in ["\\", "'", '"', '/', '..']:
        if (forbidden in image_filename):
            return "", 400
    
    image_path = os.path.join("./cache/images/", image_filename)
    if (not os.path.exists(image_path)):
        return "", 404

    if (request.method == "DELETE"):
        if (request.headers.get("authorization", "").split(" ")[-1] != config["auth_key"]):
            return "UNAUTHORIZED", 403
        try:
            os.remove(image_path)
            return "", 200
        except:
            return "", 500
    return send_file(image_path, "image/png", False)

if (__name__ == "__main__"):
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)