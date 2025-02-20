from flask import Flask
from flask_cors import CORS 
from pathlib import Path
import base64

app = Flask(__name__)

CORS(app)

@app.route("/rain", methods=["GET"])
def get_rain():
    rain = []

    for image_path in Path("./outputs").iterdir():
        blob = image_path.read_bytes()
        image_base64 = base64.b64encode(blob).decode('utf-8')
        rain.append({"name": str(image_path), "blob": image_base64})
    return rain
