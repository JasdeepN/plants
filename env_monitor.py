import bme680
import time
from datetime import datetime
import RPi.GPIO as GPIO
from water import get_soil_status
import adafruit_ccs811
import busio
import board
import db
from common import *

import os
from dotenv import load_dotenv
logger = logging.getLogger(__name__)

load_dotenv()
ENV_POLL = os.getenv('ENV_POLL')
CCS811_GPIO_PIN = int(os.getenv('CCS811_GPIO_PIN'))
CCS811_ADDR = int(os.getenv('CCS811_ADDR'), 16)
BME680_ADDR = bme680.I2C_ADDR_PRIMARY if os.getenv('BME680_ADDR') == 'PRIMARY' else bme680.I2C_ADDR_SECONDARY

def burnIn(_time = 300, save=True):
    logger.info('Starting burn in procedure')
    logger.info('save burn in data %s', save)
    start_time = time.time()
    curr_time = time.time()
    burn_in_time = _time

    burn_in_data = []
     
    if save: f = open("burn_data.txt", "w")
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if bme_680.get_sensor_data() and bme_680.data.heat_stable:
            gas = bme_680.data.gas_resistance
            burn_in_data.append(gas)
            # print('Gas: {0} Ohms'.format(gas))
            if save: f.write('{:.2f}\n'.format(gas))
            time.sleep(1)
    if save: f.close()
    logger.info('Burn in complete')

    return burn_in_data


def runBurnIn():
    logger.info('Full burn in blocking for 5 minutes...')
    burnIn(300, True)

def aqScore(gas, use_saved_value=True):
    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25


    if use_saved_value:
        burn_in_data = []
        try:
            #get from file saved value
            file = open('burn_data.txt', 'r') 
            for y in file.readlines():
                burn_in_data.append(float(y))   
        except Exception as ex:
            raise LoggedException(logger, "Couldn't open burn_data.txt. Maybe permissions?", ex) from None
    else:
        burn_in_data = burnIn(30, True)

    gas_baseline = sum(burn_in_data[-50:]) / 50.0

    gas_offset = gas_baseline - gas
    hum = bme_680.data.humidity
    hum_offset = hum - hum_baseline

    # Calculate hum_score as the distance from the hum_baseline.
    if hum_offset > 0:
        hum_score = (100 - hum_baseline - hum_offset)
        hum_score /= (100 - hum_baseline)
        hum_score *= (hum_weighting * 100)

    else:
        hum_score = (hum_baseline + hum_offset)
        hum_score /= hum_baseline
        hum_score *= (hum_weighting * 100)

    # Calculate gas_score as the distance from the gas_baseline.
    if gas_offset > 0:
        gas_score = (gas / gas_baseline)
        gas_score *= (100 - (hum_weighting * 100))

    else:
        gas_score = 100 - (hum_weighting * 100)

    # Calculate air_quality_score.
    air_quality_score = hum_score + gas_score

    return air_quality_score

def poll_insert():
    global ccs
    ss = snapshot(False)
    if len(ss) < 5:
        burnIn(5, False)
        ss = snapshot(False)
    soil_status = get_soil_status()
    _time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    sensor_aggregate =[*ss, *soil_status]
    db.insert_data(time=_time, *sensor_aggregate)

    time.sleep(ENV_POLL) 


def snapshot(burn=False, attempt=0):
    global bme_680
    global ccs
    global currentEnvironmentVars
    attempt += 1
    
    if bme_680 is None:
        raise LoggedException(logger, "Can't access bme_680. Try restarting app.", None, None) from None

    snap = [];
    if attempt >= 3:
        raise LoggedException(logger, 'Reached max retries for BME680.', None, None) from None


    if not bme_680.data.heat_stable:
        burn = True;

    if burn:
        burnIn(5, False)
        time.sleep(0.25) # give sensor a second to chill out

    if bme_680.get_sensor_data():
        ccs.set_environmental_data(bme_680.data.humidity, bme_680.data.temperature)
        # print(bme_680.data.temperature)
        snap.append(bme_680.data.temperature)
        snap.append(bme_680.data.pressure)
        snap.append(bme_680.data.humidity)

        if bme_680.data.heat_stable:
            snap.append(bme_680.data.gas_resistance)
            snap.append(aqScore(bme_680.data.gas_resistance))
        else:
            burnIn(3, False)
            snapshot(False, attempt)
    else:
        burnIn(3, False)
    if ccs.data_ready:
        snap.append(ccs.eco2)
        snap.append(ccs.tvoc)
    else:
        burnIn(3, False)

    # some of the data from the sensor is missing. try again.
    if len(snap) < 5:
        snapshot(False, attempt)

    # update the global variable holding latest data
    currentEnvironmentVars = snap
    # print('updated current', currentEnvironmentVars)
    return snap

def getLastReading():
    global currentEnvironmentVars
    return currentEnvironmentVars

def toggle_reset(PIN):
    GPIO.output(PIN, GPIO.LOW)
    time.sleep(.2)
    GPIO.output(PIN, GPIO.HIGH)
    time.sleep(0.5)

def init():
    global bme_680
    global ccs

    if bme_680 is None and ccs is None:
        #CCS811 Power up
        logger.info('Powering up CCS811')
        GPIO.setup(CCS811_GPIO_PIN, GPIO.OUT)
        GPIO.output(CCS811_GPIO_PIN, GPIO.HIGH)
        i2c = busio.I2C(board.SCL, board.SDA)   # uses board.SCL and board.SDA

        logger.info('Reset CCS811 and wait before initalizing.')
        toggle_reset(CCS811_GPIO_PIN) # do this early so any start up stuff can happen
        logger.info('Reset complete continue..')
        try:
            bme_680 = bme680.BME680(BME680_ADDR)
            bme_680.set_humidity_oversample(bme680.OS_2X)
            bme_680.set_pressure_oversample(bme680.OS_4X)
            bme_680.set_temperature_oversample(bme680.OS_8X)
            bme_680.set_filter(bme680.FILTER_SIZE_3)
            bme_680.set_gas_status(bme680.ENABLE_GAS_MEAS)

            for name in dir(bme_680.data):
                value = getattr(bme_680.data, name)

                if not name.startswith('_'):
                    logger.info('{}: {}'.format(name, value))  

            bme_680.set_gas_heater_temperature(320)
            bme_680.set_gas_heater_duration(150)
            bme_680.select_gas_heater_profile(0)
        except Exception as ex:
            raise LoggedException(logger, "Couldn't initialize BME680.", ex) from None

    
        logger.info('Done BME680 startup. Back to CCS811 initalization.') 
        try:
            ccs =  adafruit_ccs811.CCS811(i2c, CCS811_ADDR)
        except Exception as ex:
            raise LoggedException(logger, "Couldn't initialize CCS811.", ex) from None

    
def env_record(startup=False):
    if startup:
        init()
        print(burnIn(5, False))

    while True:
        poll_insert();  


# These calibration data can safely be commented
# out, if desired.

# print('Calibration data:')
# for name in dir(bme_680.calibration_data):

#     if not name.startswith('_'):
#         value = getattr(bme_680.calibration_data, name)

#         if isinstance(value, int):
#             print('{}: {}'.format(name, value))

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.


# Up to 10 heater profiles can be configured, each
# with their own temperature and duration.
# bme_680.set_gas_heater_profile(200, 150, nb_profile=1)
# bme_680.select_gas_heater_profile(1)

'''
this only runs when program is called from the CLI

'''
def poll():
    ss = snapshot(False)
    # logger.info("got sensor snapshot of current env", *ss)
    if len(ss) < 5:
        burnIn(5, False)
        ss = snapshot(False)
    soil_status = get_soil_status()
    
    sensor_aggregate =[*ss, *soil_status]

    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M:%S")
    print(timeString, sensor_aggregate)
    time.sleep(5) 


if __name__ == "__main__":
    print('This file isnt meant to be called directly unless testing')
    init()
    print('Initalized successfully. Begin burn in.')
    burnIn(5, True)
    print('Sensor burn in complete')
    try:
       print('Start polling')
       logger.info("Start logging from CLI. Press CTRL + C to quit.")
       while 1:
            try:
                poll()
            except Exception as e:
                raise e      # standard error to console
    except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
        pass
