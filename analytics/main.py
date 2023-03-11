import os
import time
from datetime import datetime
import pika
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import pytz
import const
import utils

columns = [
    const.DATE_KEY,
    const.TEMPERATURE_TANK_KEY,
    const.TEMPERATURE_MAIN_TANK_KEY,
    const.TEMPERATURE_DOME_KEY,
    const.TEMPERATURE_PLANTS_KEY,
    const.TEMPERATURE_ATM_KEY,
    const.HUMEDITY_1_KEY,
    const.HUMEDITY_2_KEY,
]


class Analytics():
    influx_bucket = 'rabbit'
    influx_token = 'token-secret'
    influx_url = 'http://influxDB:8086'
    influx_org = 'org'
    current_date = None
    dataframe = pd.DataFrame(columns=columns)

    def write_db(self, tag, key, value, timestamp, tag_value='value'):
        client = InfluxDBClient(url=self.influx_url,
                                token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analytics').tag(tag, tag_value).field(key, value).time(timestamp, write_precision='ns')
        write_api.write(bucket=self.influx_bucket, record=point)

    # Get max values from every var and post to InfluxDB
    def get_max_values(self):
        if len(self.dataframe) > 0:
            for item in const.VARS_MAX_MIN:
                max_temperature = self.dataframe[item].max()
                max_temperature_idx = self.dataframe[item].idxmax()
                max_temperature_row = self.dataframe.iloc[max_temperature_idx]
                max_temperature_time = max_temperature_row[const.DATE_KEY]
                self.write_db(
                    tag='max_values', 
                    key='MAX_{}'.format(item), 
                    value=max_temperature, 
                    timestamp=utils.get_time_to_influx(max_temperature_time)
                )

    # Get min values from every var and post to InfluxDB
    def get_min_values(self):
        if len(self.dataframe) > 0:
            for item in const.VARS_MAX_MIN:
                min_temperature = self.dataframe[item].min()
                min_temperature_idx = self.dataframe[item].idxmin()
                min_temperature_row = self.dataframe.iloc[min_temperature_idx]
                min_temperature_time = min_temperature_row[const.DATE_KEY]
                self.write_db(
                    tag='min_values', 
                    key='MIN_{}'.format(item), 
                    value=min_temperature, 
                    timestamp=utils.get_time_to_influx(min_temperature_time)
                )
  

    def get_counts(self):
        if len(self.dataframe) > 0:
            for key, value in const.VARS_COUNT.items():
                count_max = (self.dataframe[key] > value['max']).sum()
                count_min = (self.dataframe[key] <=  value['min']).sum()
                self.write_db(
                    tag='counts', 
                    tag_value='counts_max',
                    key='COUNT_MAX_{}'.format(key), 
                    value=count_max, 
                    timestamp=utils.get_time_to_influx()
                )
                self.write_db(
                    tag='counts', 
                    tag_value='counts_min',
                    key='COUNT_MIN_{}'.format(key), 
                    value=count_min, 
                    timestamp=utils.get_time_to_influx()
                )

            for key, value in const.VARS_DOME.items():
                if key == 'day':
                    # Count min from day
                    dataframe_day_min = self.dataframe.apply(lambda x : utils.get_count_dome_day_min(x, value['min'], const.DOME_DAY_HOURS['min'], const.DOME_DAY_HOURS['max']), axis = 1)
                    count_day_min = len(dataframe_day_min[dataframe_day_min == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_min',
                        key='COUNT_MIN_{}_{}'.format(key.upper(), const.TEMPERATURE_DOME_KEY), 
                        value=count_day_min, 
                        timestamp=utils.get_time_to_influx()
                    )
                    # Count max from day
                    dataframe_day_max = self.dataframe.apply(lambda x : utils.get_count_dome_day_min(x, value['max'], const.DOME_DAY_HOURS['min'], const.DOME_DAY_HOURS['max']), axis = 1)
                    count_day_max = len(dataframe_day_max[dataframe_day_max == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_max',
                        key='COUNT_MAX_{}_{}'.format(key.upper(), const.TEMPERATURE_DOME_KEY), 
                        value=count_day_max, 
                        timestamp=utils.get_time_to_influx()
                    )
                else:
                    # Count min from night
                    dataframe_night_min = self.dataframe.apply(lambda x : utils.get_count_dome_night_min(x, value['min'],const.DOME_NIGHT_HOURS['min'], const.DOME_NIGHT_HOURS['max']), axis = 1)
                    count_night_min = len(dataframe_night_min[dataframe_night_min == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_min',
                        key='COUNT_MIN_{}_{}'.format(key.upper(), const.TEMPERATURE_DOME_KEY), 
                        value=count_night_min, 
                        timestamp=utils.get_time_to_influx()
                    )
                     # Count max from night
                    dataframe_night_max = self.dataframe.apply(lambda x : utils.get_count_dome_night_max(x, value['max'], const.DOME_NIGHT_HOURS['min'], const.DOME_NIGHT_HOURS['max']), axis = 1)
                    count_night_max = len(dataframe_night_max[dataframe_night_max == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_max',
                        key='COUNT_MAX_{}_{}'.format(key.upper(), const.TEMPERATURE_DOME_KEY), 
                        value=count_night_max, 
                        timestamp=utils.get_time_to_influx()
                    )



    def take_measurement(self, _message):
        measurements = {}
        # Payload
        payload=_message.split(" ")[1]
        #print(payload, flush=True)
        # Datetime in ns
        timestamp=_message.split(" ")[2]
        # print(timestamp, flush=True)
        measurements_string = payload.split(",")
        
        timezone = pytz.timezone("America/Bogota")
        timestamp_in_sec=float(timestamp)/1000000000
        incoming_datetime_str=datetime.fromtimestamp(float(timestamp_in_sec), timezone).strftime("%Y-%m-%dT%H:%M:%S")
        # print(incoming_datetime_str, flush=True)
        incoming_datetime_str=incoming_datetime_str.split('T')[0]
        

        if self.current_date is None:
            self.current_date=incoming_datetime_str
        else:
            if incoming_datetime_str > self.current_date:
                self.current_date=incoming_datetime_str
                self.dataframe = pd.DataFrame(columns=columns)
        
        # print('current_date {}'.format(self.current_date), flush=True)
        for measurement in measurements_string:
            measurement_key_value=measurement.split("=")
            #print(measurement_key_value, flush=True)
            measurements[measurement_key_value[0]]=float(measurement_key_value[1])
        self.dataframe = self.dataframe.append({
            const.DATE_KEY:int(timestamp), 
            const.TEMPERATURE_TANK_KEY:measurements[const.Temperatura_Tanque_de_reserva],
            const.TEMPERATURE_MAIN_TANK_KEY:measurements[const.Temperatura_Tanque_Principal],
            const.TEMPERATURE_DOME_KEY:measurements[const.Temperatura_Domo],
            const.TEMPERATURE_PLANTS_KEY:measurements[const.Temperatura_Plantas],
            const.TEMPERATURE_ATM_KEY:measurements[const.Temperatura_medio_ambiente],
            const.HUMEDITY_1_KEY:measurements[const.Humedad_Planta_1],
            const.HUMEDITY_2_KEY:measurements[const.Humedad_Planta_2],
            }, 
            ignore_index=True
            )
        #print(self.dataframe)
        self.get_max_values()
        self.get_min_values()
        self.get_counts()



if __name__ == '__main__':

    analytics = Analytics()

    def callback(ch, method, properties, body):
        global analytics
        message = body.decode("utf-8")
        analytics.take_measurement(message)

    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)

    channel = connection.channel()
    channel.queue_declare(queue='messages')
    channel.queue_bind(exchange='amq.topic', queue='messages', routing_key='#')
    channel.basic_consume(
        queue='messages', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
