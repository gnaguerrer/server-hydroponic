import os
import time
from datetime import datetime, timedelta
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import AdaBoostRegressor
from datetime import datetime
import pika
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import numpy as np
import pytz
import const
import utils
import alert_sms

columns = [
    const.DATE_KEY,
    const.SECONDS_KEY,
    const.TEMPERATURE_TANK_KEY,
    const.TEMPERATURE_MAIN_TANK_KEY,
    const.TEMPERATURE_DOME_KEY,
    const.TEMPERATURE_PLANTS_KEY,
    const.TEMPERATURE_ATM_KEY,
    const.HUMEDITY_1_KEY,
    const.HUMEDITY_2_KEY,
]

columns_days = [
    const.DATE_DAY_KEY,
    const.DAY_OF_THE_YEAR_KEY,
    const.MEAN_TEMPERATURE_KEY,
]


class Analytics():
    influx_bucket = 'rabbit'
    influx_token = 'token-secret'
    influx_url = 'http://influxDB:8086'
    influx_org = 'org'
    current_date = None
    alert = 0
    dataframe = pd.DataFrame(columns=columns)
    dataframe_prediction = pd.DataFrame(columns=columns_days)
    random_forest_regressor = AdaBoostRegressor(
        DecisionTreeRegressor(max_depth=5), n_estimators=10)
    counts = {
        'COUNT_MIN_{}'.format(const.TEMPERATURE_MAIN_TANK_KEY): 0,
        'COUNT_MIN_{}'.format(const.TEMPERATURE_TANK_KEY): 0,
        'COUNT_MIN_{}'.format(const.HUMEDITY_1_KEY): 0,
        'COUNT_MIN_{}'.format(const.HUMEDITY_2_KEY): 0,
        'COUNT_MAX_{}'.format(const.TEMPERATURE_MAIN_TANK_KEY): 0,
        'COUNT_MAX_{}'.format(const.TEMPERATURE_TANK_KEY): 0,
        'COUNT_MAX_{}'.format(const.HUMEDITY_1_KEY): 0,
        'COUNT_MAX_{}'.format(const.HUMEDITY_2_KEY): 0,
    }

    def write_db(self, tag, key, value, timestamp, tag_value='value'):
        client = InfluxDBClient(url=self.influx_url,
                                token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analytics').tag(tag, tag_value).field(
            key, value).time(timestamp, write_precision='ns')
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

    def get_counts_dataframe(self):
        if len(self.dataframe) > 0:
            for key, value in const.VARS_COUNT.items():
                count_max = (self.dataframe[key] > value['max']).sum()
                count_min = (self.dataframe[key] <= value['min']).sum()
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
                    dataframe_day_min = self.dataframe.apply(lambda x: utils.get_count_dome_day_min(
                        x, value['min'], const.DOME_DAY_HOURS['min'], const.DOME_DAY_HOURS['max']), axis=1)
                    count_day_min = len(
                        dataframe_day_min[dataframe_day_min == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_min',
                        key='COUNT_MIN_{}_{}'.format(
                            key.upper(), const.TEMPERATURE_DOME_KEY),
                        value=count_day_min,
                        timestamp=utils.get_time_to_influx()
                    )
                    # Count max from day
                    dataframe_day_max = self.dataframe.apply(lambda x: utils.get_count_dome_day_min(
                        x, value['max'], const.DOME_DAY_HOURS['min'], const.DOME_DAY_HOURS['max']), axis=1)
                    count_day_max = len(
                        dataframe_day_max[dataframe_day_max == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_max',
                        key='COUNT_MAX_{}_{}'.format(
                            key.upper(), const.TEMPERATURE_DOME_KEY),
                        value=count_day_max,
                        timestamp=utils.get_time_to_influx()
                    )
                else:
                    # Count min from night
                    dataframe_night_min = self.dataframe.apply(lambda x: utils.get_count_dome_night_min(
                        x, value['min'], const.DOME_NIGHT_HOURS['min'], const.DOME_NIGHT_HOURS['max']), axis=1)
                    count_night_min = len(
                        dataframe_night_min[dataframe_night_min == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_min',
                        key='COUNT_MIN_{}_{}'.format(
                            key.upper(), const.TEMPERATURE_DOME_KEY),
                        value=count_night_min,
                        timestamp=utils.get_time_to_influx()
                    )
                    # Count max from night
                    dataframe_night_max = self.dataframe.apply(lambda x: utils.get_count_dome_night_max(
                        x, value['max'], const.DOME_NIGHT_HOURS['min'], const.DOME_NIGHT_HOURS['max']), axis=1)
                    count_night_max = len(
                        dataframe_night_max[dataframe_night_max == True].index)
                    self.write_db(
                        tag='counts',
                        tag_value='counts_max',
                        key='COUNT_MAX_{}_{}'.format(
                            key.upper(), const.TEMPERATURE_DOME_KEY),
                        value=count_night_max,
                        timestamp=utils.get_time_to_influx()
                    )

    def add_to_dataframe_prediction(self):
        timezone = pytz.timezone("America/Bogota")
        last_timestamp = float(
            self.dataframe.iloc[-1][const.DATE_KEY])/1000000000
        last_day = datetime.fromtimestamp(last_timestamp, timezone).date()
        last_day_of_the_year = int((last_day).strftime('%j'))

        if len(self.dataframe_prediction) == 0:
            data_to_append = pd.DataFrame([[last_day, last_day_of_the_year, self.dataframe[const.TEMPERATURE_ATM_KEY].mean(
            )]], columns=self.dataframe_prediction.columns)
            self.dataframe_prediction = pd.concat(
                [self.dataframe_prediction, data_to_append], ignore_index=True)
        else:
            if last_day_of_the_year == self.dataframe_prediction.iloc[-1][const.DAY_OF_THE_YEAR_KEY]:
                self.dataframe_prediction = self.dataframe_prediction.drop(
                    len(self.dataframe_prediction) - 1)
                data_to_append = pd.DataFrame([[last_day, last_day_of_the_year, self.dataframe[const.TEMPERATURE_ATM_KEY].mean(
                )]], columns=self.dataframe_prediction.columns)
                self.dataframe_prediction = pd.concat(
                    [self.dataframe_prediction, data_to_append], ignore_index=True)
            else:
                data_to_append = pd.DataFrame([[last_day, last_day_of_the_year, self.dataframe[const.TEMPERATURE_ATM_KEY].mean(
                )]], columns=self.dataframe_prediction.columns)
                self.dataframe_prediction = pd.concat(
                    [self.dataframe_prediction, data_to_append], ignore_index=True)

        print("Dataframe prediction ", self.dataframe_prediction, flush=True)

    def get_prediction_next_day(self, actual_time):
        if len(self.dataframe_prediction) > 0:
            X = self.dataframe_prediction[const.DAY_OF_THE_YEAR_KEY].to_numpy(
            ).reshape(-1, 1)
            Y = self.dataframe_prediction[const.MEAN_TEMPERATURE_KEY].to_numpy(
            )
            self.random_forest_regressor.fit(X, Y)
            timezone = pytz.timezone(const.TIME_ZONE)
            actual_time = float(actual_time)/1000000000
            next_day = datetime.fromtimestamp(actual_time, timezone).date() + timedelta(
                days=1)
            value_to_predict = np.array(
                int(next_day.strftime('%j'))).reshape(-1, 1)
            value_predicted = self.random_forest_regressor.predict(
                value_to_predict)
            print("Predicted temperature for {} is {} ".format(
                next_day, value_predicted[0]), flush=True)
            self.write_db(
                tag='predictions',
                tag_value='next_day',
                key='MEAN_{}'.format(const.TEMPERATURE_ATM_KEY),
                value=value_predicted[0],
                timestamp=time.time_ns()
            )
        else:
            print(
                "No se puede realizar una prediccion en get_prediction_next_day()", flush=True)

    def get_prediction_seconds(self, actual_time):
        if len(self.dataframe_prediction) > 0:
            timezone = pytz.timezone(const.TIME_ZONE)
            max_seconds = 86400
            forward_seconds = 10
            dataframe = self.dataframe.copy()
            X = dataframe[const.SECONDS_KEY].to_numpy().reshape(-1, 1)
            Y = dataframe[const.TEMPERATURE_ATM_KEY].to_numpy()
            regressor = AdaBoostRegressor(
                DecisionTreeRegressor(max_depth=5), n_estimators=10)
            regressor.fit(X, Y)
            actual_time = float(actual_time)/1000000000
            value_to_predict = actual_time + forward_seconds
            if value_to_predict > max_seconds:
                value_to_predict = np.array(value_to_predict - max_seconds)
            else:
                value_to_predict = np.array(value_to_predict)
            value_predicted = regressor.predict(
                value_to_predict.reshape(-1, 1))
            prediction_time = datetime.fromtimestamp(
                float(actual_time), timezone).strftime("%Y-%m-%dT%H:%M:%S")
            print("Predicted temperature for {} is {} ".format(
                prediction_time, value_predicted[0]), flush=True)
            self.write_db(
                tag='predictions',
                tag_value='few_seconds',
                key='VALUE_OF_{}'.format(const.TEMPERATURE_ATM_KEY),
                value=value_predicted[0],
                timestamp=time.time_ns()
            )
        else:
            print(
                "No se puede realizar una prediccion en get_prediction_seconds()", flush=True)

    def check_counts(self):
        for key, value in self.counts.items():
            if value > 3:
                self.counts[key] = 0
                if int(self.alert):
                    print('Sending messages', flush=True)
                    alert_sms.send_alert_sms(const.ALERT_MESSAGES[key])
        print(self.counts, flush=True)

    def get_counts_alert(self, current_measurements):
        for key, value in const.VARS_COUNT.items():
            print('---> key: {}, value: {}'.format(key, value), flush=True)
            if current_measurements[key] > value['max']:
                self.counts['COUNT_MAX_{}'.format(key)] += 1
            if current_measurements[key] <= value['min']:
                self.counts['COUNT_MIN_{}'.format(key)] += 1
        self.check_counts()

    def take_measurement(self, _message):
        measurements = {}
        # Payload
        payload = _message.split(" ")[1]
        #print(payload, flush=True)
        # Datetime in ns
        timestamp = _message.split(" ")[2]
        # print(timestamp, flush=True)
        measurements_string = payload.split(",")

        timezone = pytz.timezone(const.TIME_ZONE)
        timestamp_in_sec = float(timestamp)/1000000000
        incoming_datetime_str = datetime.fromtimestamp(
            float(timestamp_in_sec), timezone).strftime("%Y-%m-%dT%H:%M:%S")
        # print(incoming_datetime_str, flush=True)
        incoming_datetime_str = incoming_datetime_str.split('T')[0]
        hour = datetime.fromtimestamp(
            float(timestamp_in_sec), timezone).strftime("%H")
        minutes = datetime.fromtimestamp(
            float(timestamp_in_sec), timezone).strftime("%M")
        seconds = datetime.fromtimestamp(
            float(timestamp_in_sec), timezone).strftime("%S")
        time_second = (int(hour)*60 + int(minutes))*60 + int(seconds)

        if self.current_date is None:
            self.current_date = incoming_datetime_str
        else:
            if incoming_datetime_str > self.current_date:
                self.current_date = incoming_datetime_str
                self.dataframe = pd.DataFrame(columns=columns)

        # print('current_date {}'.format(self.current_date), flush=True)
        for measurement in measurements_string:
            measurement_key_value = measurement.split("=")
            #print(measurement_key_value, flush=True)
            measurements[measurement_key_value[0]] = float(
                measurement_key_value[1])
        new_measurement = [
            float(timestamp),
            int(time_second),
            measurements[const.Temperatura_Tanque_de_reserva],
            measurements[const.Temperatura_Tanque_Principal],
            measurements[const.Temperatura_Domo],
            measurements[const.Temperatura_Plantas],
            measurements[const.Temperatura_medio_ambiente],
            measurements[const.Humedad_Planta_1],
            measurements[const.Humedad_Planta_2]
        ]
        data_to_append = pd.DataFrame(
            [new_measurement], columns=self.dataframe.columns)
        self.dataframe = pd.concat(
            [self.dataframe, data_to_append], ignore_index=True)
        print("Normal Dataframe ", self.dataframe, flush=True)
        self.add_to_dataframe_prediction()
        self.get_counts_alert(new_measurement)
        self.get_max_values()
        self.get_min_values()
        self.get_counts_dataframe()

    def get_prediction(self, _message):
        print('get_prediction - message {}'.format(_message), flush=True)

    def toggle_alerts(self, _message):
        print('toggle_alerts - value {}'.format(_message), flush=True)
        payload = _message.split(" ")[1]
        value = payload.split('=')[1]
        self.alert = value


if __name__ == '__main__':

    analytics = Analytics()

    def callback(ch, method, properties, body):
        global analytics
        message = body.decode("utf-8")
        current_topic = method.routing_key
        if current_topic == 'data':
            analytics.take_measurement(message)
        elif current_topic == 'prediction':
            timestamp = message.split(" ")[2]
            analytics.get_prediction_next_day(timestamp)
            analytics.get_prediction_seconds(timestamp)
        elif current_topic == 'alert':
            analytics.toggle_alerts(message)

    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)

    channel = connection.channel()
    channel.queue_declare(queue='messages')
    channel.queue_bind(exchange='amq.topic', queue='messages', routing_key='#')
    channel.basic_consume(
        queue='messages', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
