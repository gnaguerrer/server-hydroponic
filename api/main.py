from typing import Union
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import paho.mqtt.client as mqtt
from pydantic import BaseModel
from typing import Dict
import time

servidor = 'rabbit'

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
]

app = FastAPI(title="TestApi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
influx_bucket = 'rabbit'
influx_token = 'token-secret'
influx_url = 'http://influxDB:8086'
influx_org = 'org'
client = InfluxDBClient(url=influx_url,token=influx_token, org=influx_org)
query_api = client.query_api()

current_alert_value = False

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("$SYS/#")


def on_message(client, userdata, msg):
    print(msg.topic + str(msg.payload))


@app.get("/")
def read_root():
    return {"status": 200}

# @app.get("/temperature")
# def get_temperature():
#     query = 'from(bucket: "rabbit")\
#                 |> range(start: -24h)\
#                 |> filter(fn: (r) => r["_measurement"] == "measurements")\
#                 |> filter(fn: (r) => r["_field"] == "Temperatura_Domo" or r["_field"] == "Temperatura_Tanque_de_reserva" or r["_field"] == "Temperatura_Tanque_Principal" or r["_field"] == "Temperatura_Plantas" or r["_field"] == "Temperatura_medio_ambiente")\
#                 |> yield(name: "last")'
#     result = query_api.query(org=influx_org, query=query)
#     print('result')
#     print(result, flush=True)
#     results = []
#     table_items = {
#         'Temperatura_Domo' : [],
#         'Temperatura_Plantas' : [],
#         'Temperatura_Tanque_Principal' : [],
#         'Temperatura_Tanque_de_reserva' : [],
#         'Temperatura_medio_ambiente' : [],
#     }
#     for table in result:
#         print('Table')
#         print(table, flush=True)
#         for record in table.records:
#             table_items[record.get_field()].append(record.get_value())
#             print('record')
#             print(record, flush=True)
    
#     for index in range(len(table_items['Temperatura_Domo'])):
#         item_new = dict()
#         print(table_items['Temperatura_medio_ambiente'][index], flush=True)
#         for key, value in table_items.items():
#           item_new[key] = value[index]
#         print(item_new, flush=True)
#         results.append(item_new)
#     print(results, flush=True)
#     print('table_items, flush=True')
#     print(table_items, flush=True)
            
#     return {
#        "status": 200,
#        "message": "Get temperatures",
#        "data": results 
#     }

@app.get("/toogle_alerts")
def toggle_alert():
    global current_alert_value
    current_alert_value = not current_alert_value
    value = 1 if current_alert_value else 0
    print('current_alert_value---{}'.format(current_alert_value), flush=True)
    client = mqtt.Client()
    client.username_pw_set("guest", password='guest')
    client.connect(servidor, 1883, 60)
    client.loop_start()
    client.publish("alert", 'alert alert_value={}'.format(value))

@app.get("/get_prediction")
def get_prediction():
    actual_time = time.time_ns()
    print('get_prediction---{}'.format(actual_time), flush=True)
    client = mqtt.Client()
    client.username_pw_set("guest", password='guest')
    client.connect(servidor, 1883, 60)
    client.loop_start()
    client.publish("prediction", 'prediction prediction_time={} {}'.format(actual_time, actual_time))