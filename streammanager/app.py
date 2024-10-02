import datetime
import time
import json
import requests
import os
from io import BytesIO
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import influxdb_client


# Initialize FastAPI
app = FastAPI(title="Stream Manager", description="Manage streamoverlay state", version="1.0")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration

api_token = os.getenv('API_TOKEN')

influxdb_token = os.getenv('INFLUXDB_TOKEN')
influxdb_org = os.getenv('INFLUXDB_ORG') or "makerspace"
influxdb_bucket = os.getenv('INFLUXDB_BUCKET') or "balloon"
influxdb_url = os.getenv('INFUXDB_URL') or "https://influx.balloon.nikogenia.de"

storage_url = os.getenv('STORAGE_URL') or "u421785.your-storagebox.de"
storage_user = os.getenv('STORAGE_USER') or "u421785"
storage_password = os.getenv('STORAGE_PASSWORD')
storage_path = os.getenv('STORAGE_PATH') or "System"

if api_token is None or influxdb_token is None or storage_password is None:
    print("Missing configuration via environment variables")
    exit(1)

# Initialize state
STATE_VERSION = "1.4"
STATE_FILE = "/config/state.json"
STATE_FILE = "state.json"
state = {
    "version": STATE_VERSION,
    "phase": 0,
    "countdown": datetime.datetime(2024, 7, 25, 9, 30, 0).timestamp(),
    "streamcountdown": datetime.datetime(2024, 7, 25, 9, 30, 0).timestamp(),
    "title": "",
    "subtitle": "",
    "sensors": False,
    "source": {
        "connection": "wifi",
        "height": "gps"
    }
}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as file:
        file_state = json.load(file)
        if file_state["version"] == STATE_VERSION:
            state = file_state
        else:
            print("State file version mismatch, using new state")
    print("Loaded state from file")
else:
    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=4, separators=(', ', ': '))
    print("Created new state file")

# Image cache
image_cache = {}


# Define data models for requests
class Token(BaseModel):
    token: str


class Countdown(BaseModel):
    token: str
    time: float


class Title(BaseModel):
    token: str
    title: str
    subtitle: str


class Source(BaseModel):
    token: str
    connection: str
    height: str


@app.get("/sensors")
def route_sensors():

    if not state["sensors"]:
        return {}

    result = {}

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=influxdb_url, org=influxdb_org,
                                        token=influxdb_token, timeout=2500) as client:
        for field, measurement in [("temp", "climate"),
                                   ("avg", "thermal"),
                                   ("pressure", "climate"),
                                   ("humidity", "climate"),
                                   ("uv", "adc"),
                                   ("co2", "co2")]:
            query = f'from(bucket: "{influxdb_bucket}") \
                      |> range(start: -1y) \
                      |> filter(fn: (r) => r._measurement == "{state["source"]["connection"]}_{measurement}") \
                      |> filter(fn: (r) => r._field == "{field}") \
                      |> last()'
            tables = client.query_api().query(org=influxdb_org, query=query)
            for value in tables.to_values(columns=["_value"]):
                result[field] = value[0]
        print("Successfully read data from InfluxDB")

    return result


@app.get("/height")
def route_height():

    result = {
        "phase": state["phase"],
    }

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=influxdb_url, org=influxdb_org,
                                        token=influxdb_token, timeout=2500) as client:
        query = f'from(bucket: "{influxdb_bucket}") \
                  |> range(start: -1y) \
                  |> filter(fn: (r) => r._measurement == "{state["source"]["connection"]}_{state["source"]["height"]}") \
                  |> filter(fn: (r) => r._field == "altitude") \
                  |> sort(columns:["_time"], desc: true) \
                  |> limit(n:2)'
        tables = client.query_api().query(org=influxdb_org, query=query)
        values = tables.to_values(columns=["_value", "_time"])
        if len(values) >= 2:
            last_altitude, last_time = values[0]
            second_last_altitude, second_last_time = values[1]
            time_difference = (last_time - second_last_time).total_seconds()
            result["speed"] = (last_altitude - second_last_altitude) / time_difference
        if values:
            result["height"] = values[0][0]
        print("Successfully read data from InfluxDB")

    return result


@app.get("/phase")
def route_phase():
    return {"phase": state["phase"]}


@app.get("/countdown")
def route_countdown_get():
    return {"time": state["countdown"]}


@app.get("/stream/countdown")
def route_stream_countdown_get():
    return {"time": state["streamcountdown"]}


@app.get("/title")
def route_title_get():
    return {"title": state["title"], "subtitle": state["subtitle"]}


@app.get("/status")
def route_status():
    return state


@app.post("/phase/back")
def route_phase_back(data: Token, response: Response):
    if data.token != api_token:
        response.status_code = 403
        return {"status": "invalid token"}
    if state["phase"] <= 0:
        response.status_code = 400
        return {"status": "already at first phase"}
    state["phase"] -= 1
    print(f"Changed phase back to {state['phase']}")
    save_state()
    return {"status": "successfully changed phase"}


@app.post("/phase/next")
def route_phase_next(data: Token, response: Response):
    if data.token != api_token:
        response.status_code = 403
        return {"status": "invalid token"}
    if state["phase"] >= 4:
        response.status_code = 400
        return {"status": "already at last phase"}
    state["phase"] += 1
    print(f"Changed phase next to {state['phase']}")
    save_state()
    return {"status": "successfully changed phase"}


@app.post("/sensors/toggle")
def route_sensors_toggle(data: Token, response: Response):
    if data.token != api_token:
        response.status_code = 403
        return {"status": "invalid token"}
    state["sensors"] = not state["sensors"]
    print(f"Changed sensor display to {state['sensors']}")
    save_state()
    return {"status": "successfully changed sensor display"}


@app.post("/countdown")
def route_countdown_post(data: Countdown, response: Response):
    if data.token != api_token:
        response.status_code = 403
        return {"status": "invalid token"}
    state["countdown"] = data.time
    print(f"Changed countdown to {datetime.datetime.fromtimestamp(data.time)} ({data.time})")
    save_state()
    return {"status": "successfully changed countdown"}


@app.post("/stream/countdown")
def route_stream_countdown_post(data: Countdown, response: Response):
    if data.token != api_token:
        response.status_code = 403
        return {"status": "invalid token"}
    state["streamcountdown"] = data.time
    print(f"Changed stream countdown to {datetime.datetime.fromtimestamp(data.time)} ({data.time})")
    save_state()
    return {"status": "successfully changed stream countdown"}


@app.post("/title")
def route_title_post(data: Title, response: Response):
    if data.token != api_token:
        response.status_code = 403
        return {"status": "invalid token"}
    state["title"] = data.title
    state["subtitle"] = data.subtitle
    print(f"Changed title to {data.title} and subtitle to {data.subtitle}")
    save_state()
    return {"status": "successfully changed title"}


@app.post("/source")
def route_source(data: Source, response: Response):
    if data.token != api_token:
        response.status_code = 403
        return {"status": "invalid token"}
    updated = []
    if data.connection:
        if data.connection not in ["wifi", "aprs"]:
            response.status_code = 400
            return {"status": "connection must be wifi or aprs"}
        state["source"]["connection"] = data.connection
        print(f"Changed connection source to {data.connection}")
        updated.append("connection")
    if data.height:
        if data.height not in ["gps", "climate"]:
            response.status_code = 400
            return {"status": "height must be gps or climate"}
        state["source"]["height"] = data.height
        print(f"Changed height source to {data.height}")
        updated.append("height")
    if not updated:
        response.status_code = 400
        return {"status": "nothing to update"}
    save_state()
    return {"status": f"successfully changed source {', '.join(updated)}"}


@app.get("/image/{streamid}")
def route_image(request: Request, streamid: str):
    base_url = str(request.url).replace(request.url.path, "")
    return templates.TemplateResponse(request, "image.html", {"streamid": streamid, "sm_url": base_url})


@app.get("/img/{streamid}")
def route_img(streamid: str, response: Response):

    if streamid in image_cache and image_cache[streamid]["time"] > time.time() - 10:
        print("Serving image from cache")
        image_stream = BytesIO(image_cache[streamid]["data"])
        return StreamingResponse(image_stream, media_type="image/png")

    path = f"{storage_path}/photo/{streamid}/latest.jpg"
    if streamid == "thermal":
        path = f"{storage_path}/thermal/latest.png"

    url = f"https://{storage_user}:{storage_password}@{storage_url}/{path}"

    try:
        print("Requesting image from storage box")
        rqs = requests.get(url, timeout=3)
        if rqs.status_code != 200:
            response.status_code = 404
            return "Image not found! Please check stream id or verify the image is available."
    except requests.exceptions.RequestException as e:
        response.status_code = 404
        return "Image not found! Please check stream id or verify the image is available."

    image_cache[streamid] = {
        "time": time.time(),
        "data": rqs.content
    }

    image_stream = BytesIO(rqs.content)
    return StreamingResponse(image_stream, media_type="image/png")


def save_state():
    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=4, separators=(', ', ': '))
    print("Successfully saved state")


@app.on_event("startup")
@repeat_every(seconds=10)
def debug():

    print("State:")
    print(json.dumps(state, indent=4, separators=(', ', ': ')))
