import time
import datetime
import json
import os
from fastapi import FastAPI, Response
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
import influxdb_client


# Initialize FastAPI
app = FastAPI(title="Stream Manager", description="Manage streamoverlay state", version="1.0")

# Configuration
api_token = os.getenv('API_TOKEN')
influxdb_token = os.getenv('INFLUXDB_TOKEN')
influxdb_org = os.getenv('INFLUXDB_ORG') or "makerspace"
influxdb_bucket = os.getenv('INFLUXDB_BUCKET') or "balloon"
influxdb_url = os.getenv('INFUXDB_URL') or "https://influx.balloon.nikogenia.de"
value_timeout = os.getenv('VALUE_TIMEOUT') or "90d"
if api_token is None or influxdb_token is None:
    print("Missing configuration via environment variables")
    exit(1)

# Initialize state
STATE_VERSION = "1.0"
STATE_FILE = "/config/state.json"
state = {
    "version": STATE_VERSION,
    "phase": 0,
    "countdown": datetime.datetime(2024, 7, 25, 9, 30, 0).timestamp(),
    "title": "",
    "subtitle": "",
    "sensors": False,
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


@app.get("/sensors")
def route_sensors():

    if not state["sensors"]:
        return {}

    result = {}

    print("Connecting to InfluxDB")
    with influxdb_client.InfluxDBClient(url=influxdb_url, org=influxdb_org,
                                        token=influxdb_token, timeout=2500) as client:
        for field, measurement in [("temp", "climate"),
                                   ("pressure", "climate"),
                                   ("humidity", "climate"),
                                   ("uv", "adc"),
                                   ("co2", "co2")]:
            query = f'from(bucket: "{influxdb_bucket}") \
                      |> range(start: -{value_timeout}) \
                      |> filter(fn: (r) => r._measurement == "wifi_{measurement}") \
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
                  |> range(start: -{value_timeout}) \
                  |> filter(fn: (r) => r._measurement == "wifi_gps") \
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


@app.get("/title")
def route_title_get():
    return {"title": state["title"], "subtitle": state["subtitle"]}


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


def save_state():
    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=4, separators=(', ', ': '))
    print("Successfully saved state")


@app.on_event("startup")
@repeat_every(seconds=10)
def debug():

    print("State:")
    print(json.dumps(state, indent=4, separators=(', ', ': ')))
