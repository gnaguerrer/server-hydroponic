DATE_KEY = 'DATE'
SECONDS_KEY = "SECONDS"
TEMPERATURE_TANK_KEY = 'TEM_TANK'
TEMPERATURE_MAIN_TANK_KEY = 'TEMP_MAIN_TANK'
TEMPERATURE_DOME_KEY = 'TEMP_DOME'
TEMPERATURE_PLANTS_KEY = 'TEMP_PLANTS'
TEMPERATURE_ATM_KEY = 'TEMP_ATM'
HUMEDITY_1_KEY = 'HUM_1'
HUMEDITY_2_KEY = 'HUM_2'

DATE_DAY_KEY = "DATE"
DAY_OF_THE_YEAR_KEY = "DATE_OF_THE_YEAR"
MEAN_TEMPERATURE_KEY = "MEAN_TEMPERATURE"


# Keys from values from rabbit/telegraf
Temperatura_medio_ambiente = 'Temperatura_medio_ambiente'
Temperatura_Domo = 'Temperatura_Domo'
Temperatura_Tanque_Principal = 'Temperatura_Tanque_Principal'
Temperatura_Tanque_de_reserva = 'Temperatura_Tanque_de_reserva'
Temperatura_Plantas = 'Temperatura_Plantas'
Humedad_Planta_1 = 'Humedad_Planta_1'
Humedad_Planta_2 = 'Humedad_Planta_2'

# Thresholds for selected vars
THRESHOLD_TEMPERATURE_BACKUP_TANK = {
    'max': 27,
    'min': 18
}

THRESHOLD_TEMPERATURE_MAIN_TANK = {
    'max': 27,
    'min': 18
}

THRESHOLD_HUMIDITY_1 = {
    'max': 70,
    'min': 50
}

THRESHOLD_HUMIDITY_2 = {
    'max': 70,
    'min': 50
}

THRESHOLD_TEMPERATURE_DOME_DAY = {
    'max': 25,
    'min': 20
}

THRESHOLD_TEMPERATURE_DOME_NIGHT = {
    'max': 20,
    'min': 15
}


# Hours
DOME_DAY_HOURS = {
    'min': 5,
    'max': 18
}

DOME_NIGHT_HOURS = {
    'min': 18,
    'max': 5
}


# Vars to count in a range
VARS_COUNT = {
    TEMPERATURE_MAIN_TANK_KEY: THRESHOLD_TEMPERATURE_MAIN_TANK,
    TEMPERATURE_TANK_KEY: THRESHOLD_TEMPERATURE_BACKUP_TANK,
    HUMEDITY_1_KEY: THRESHOLD_HUMIDITY_1,
    HUMEDITY_2_KEY: THRESHOLD_HUMIDITY_2,
}

# Vars to get max & min values
VARS_MAX_MIN = [
    TEMPERATURE_MAIN_TANK_KEY,
    TEMPERATURE_TANK_KEY,
    HUMEDITY_1_KEY,
    HUMEDITY_2_KEY,
    TEMPERATURE_DOME_KEY,
    TEMPERATURE_PLANTS_KEY,
    TEMPERATURE_ATM_KEY
]

VARS_DOME = {
    'day': THRESHOLD_TEMPERATURE_DOME_DAY,
    'night': THRESHOLD_TEMPERATURE_DOME_NIGHT
}


TIME_ZONE = "America/Bogota"
