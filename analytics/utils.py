import time
from datetime import datetime
import pytz
import const


def get_time_to_influx(prev_time=None) -> str:
    """
    Return current time or provided time to InfluxDB format

    Parameters:
    prev_time (int): value's time

    """
    if prev_time:
        timestamp_in_sec=float(prev_time)/1000000000
        incoming_datetime_str=datetime.fromtimestamp(float(timestamp_in_sec)).strftime("%Y-%m-%dT%H:%M:%S")
    else :
        actual_time = time.time_ns()
        timestamp_in_sec=float(actual_time)/1000000000
        incoming_datetime_str=datetime.fromtimestamp(float(timestamp_in_sec)).strftime("%Y-%m-%dT%H:%M:%S")
    return incoming_datetime_str

def get_hour_int(timestamp) -> int:
    """
    Return hours from timestamp in ns

    Parameters:
    timestamp (int): time in ns

    """
    timezone = pytz.timezone(const.TIME_ZONE)
    time_str=datetime.fromtimestamp(float(timestamp)/1000000000, timezone).strftime("%H")
    return int(time_str)


def get_count_dome_day_max(item, max_value, time_min, time_max) -> bool:
    time_int=get_hour_int(item[const.DATE_KEY])
    return bool(item[const.TEMPERATURE_DOME_KEY] > max_value and (time_int > time_min or time_int < time_max))

def get_count_dome_day_min(item, min_value, time_min, time_max) -> bool:
    time_int=get_hour_int(item[const.DATE_KEY])
    return bool(item[const.TEMPERATURE_DOME_KEY] <= min_value and (time_int > time_min or time_int < time_max))

def get_count_dome_night_max(item, max_value, time_min, time_max) -> bool:
    time_int=get_hour_int(item[const.DATE_KEY])
    return bool(item[const.TEMPERATURE_DOME_KEY] > max_value and (time_int >= time_min or time_int <= time_max))

def get_count_dome_night_min(item, min_value, time_min, time_max) -> bool:
    time_int=get_hour_int(item[const.DATE_KEY])
    return bool(item[const.TEMPERATURE_DOME_KEY] <= min_value and (time_int >= time_min or time_int <= time_max))
