import RPi.GPIO as GPIO
import time
from datetime import datetime
import subprocess
import glob
import json 
import hashlib
import os
from dotenv import load_dotenv
from functools import reduce


from common import * 
logger = logging.getLogger(__name__)

load_dotenv()
DEBUG = os.getenv('DEBUG')
SENSE_TIME = os.getenv('SENSE_TIME')
PUMP_TIME = os.getenv('PUMP_TIME')

def clear_errors():
    global power_on_count
    power_on_count = [0,0,0,0]

def sensor_state():
    global active_sensors
    return active_sensors

def init():
    logger.info("Start pump pin init")
    global md5_sense
    global active_sensors
    global pump_pin
    global ADS
    GPIO.setwarnings(False)

    try:
        mode = GPIO.getmode()
        if modes[mode] == "BCM" or 11: # Broadcom pin-numbering scheme
            logger.info("Got Broadcom pin-numbering from Pi settings as GPIO mode")
            pump_pin = [4,17,27,22]
        elif modes[mode] == "BOARD" or 10:
            logger.info("Got BOARD from Pi settings as GPIO mode")
            pump_pin = [7,11,13,15]
    except:
        logger.warning('Unable to read Pi settings, try setting your GPIO mode again. Will try using BCM and continue..')
        GPIO.setmode(GPIO.BCM) 
        pump_pin = [4,17,27,22]

    logger.info('setting up pump pins %s...' % pump_pin)

    for pin in pump_pin:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
    
    logger.info('pump pins set successfully')

    startup = [False, False, False, False] #TODO: Update this if adding more soil moisture sensors
    logger.info('setting sensor file defaults all off')
    try:
        with open('.sense.cfg', 'w+', encoding='utf-8') as filehandle:
            json.dump(startup, filehandle)
            md5_sense=hashlib.md5(filehandle.read().encode('utf-8')).hexdigest()
            filehandle.close()
    except Exception as ex:
        raise LoggedException(logger, "Couldn't open [init] .sense.cfg. Maybe permissions?", ex) from None
  
    active_sensors = startup #no need for file read we start will all sensors off
    logger.info('sensor file set')

    logger.info('setup complete using file hash %s', md5_sense)
  
def toggle_sensor(pin=None):
    pin = int(pin)
    global active_sensors
    if pin is None: return
    active_sensors[pin]=not active_sensors[pin]
    try:
        with open('.sense.cfg', 'w') as filehandle:
            json.dump(active_sensors, filehandle)
            filehandle.close()
    except Exception as ex:
            raise LoggedException(logger, "Couldn't open [toggle_sensor] .sense.cfg. Maybe permissions?", ex) from None

def deactivate(pin=None):
    global active_sensors
    active_sensors[pin] = False
    try:
        with open('.sense.cfg', 'w') as filehandle:
            json.dump(active_sensors, filehandle)
            filehandle.close()
        active_sensors = loadSensors() # force reload with sensor disabled
    except Exception as ex:
        raise LoggedException(logger, "Couldn't open [deactivate] .sense.cfg. Maybe permissions?", ex) from None

def loadSensors():
    logger.info('loading sensor config...')
    # file_change = False # turn off read flag
    try:
        with open(".sense.cfg", "r") as f:
            _f= f.read().encode('utf-8')
            f.close()
            logger.info('read from file:', json.loads(_f))
            return json.loads(_f)
    except Exception as ex:
        raise LoggedException(logger, "Couldn't open [load] .sense.cfg. Maybe permissions?", ex) from None
    
def get_soil_status(pin = None):
    global sensorADSPin
    global ADS
    if pin == None:
        out = []
        for pin in sensorADSPin:
            out.append(getSensorState(pin)) 
        return out
    else:
        return getSensorState(pin)

def auto_water():   
    global active_sensors
    global power_on_count

    power_on_count=[0,0,0,0]
    try:
        while 1:
            logger.info('start checking the ADS channels')
            checkFile()# if file_change update list of sensors to use
            for pin in sensorADSPin:
                if active_sensors[pin]:
                    logger.info('pin %s running power count=%s' % (pin, power_on_count))
                    if power_on_count[pin] <= 5:
                        dry = get_soil_status(pin) == "dry"
                        logger.info('status', dry)
                        if dry:
                            pump_on(pin, PUMP_TIME)
                            power_on_count[pin] += 1
                        else:
                            power_on_count[pin] = 0 # reset safety counter 
                    else:    
                        pump_off(pin) # just in case
                        deactivate(pin) #stop from running this pump until manually turned back on
                        print('there might be something wrong with the sensor on pin %d, reached max retries; sensor and pump disabled.' % pin)
                        pass # ? do we need this..probably not but whatever
                        #TODO: send ALERT through email/mqtt/sms/push whatever
                else:
                    logger.info('pin %d is inactive' % pin)
            time.sleep(SENSE_TIME) # check soil every x seconds        
    except Exception as ex:
        raise LoggedException(logger, "Something went wrong with AUTO WATER.", ex) from None

def checkFile():
    global active_sensors
    global md5_sense

    try:
        if md5_sense is None:  
            with open('.sense.cfg', 'r', encoding='utf-8') as filehandle:
                md5_sense=hashlib.md5(filehandle.read().encode('utf-8')).hexdigest()
                filehandle.close()
        else:
            with open('.sense.cfg', 'r', encoding='utf-8') as filehandle:
                new_hash=hashlib.md5(filehandle.read().encode('utf-8')).hexdigest()
                logger.info('new file hash', new_hash)
                logger.info('old file hash', md5_sense)
                if new_hash == md5_sense:
                    logger.info('no file change')
                    pass
                else:
                    logger.info('loading new file')
                    md5_sense = new_hash #update file hash
                    active_sensors = loadSensors()

                filehandle.close()
    except Exception as ex:
        raise LoggedException(logger, "Something went wrong with checking .sense against its hash..", ex) from None

def getPinState(pin):
    state = GPIO.input(pump_pin[pin])
    logger.info("pin %s state %s" % (pump_pin[pin], state))
    if state:
        return 0
    else:
        return 1

def getSensorState(channel):
    global ADS
    value = ADS.readADC(channel)
    for map_val in ADS_MAP:
        val=ADS_MAP.get(map_val)
        if val[0] <= value <= val[1]:
            return map_val

def updateLog(pin = None, msg = ""):
    if pin == None: return;
    _time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _msg = 0 if msg == "manual" else 1

    pump_data=[pin, _msg]
    db.insert_data_from_pump(time=_time, pump_data=pump_data) 

def pump_on(pin, pump_time = 0):
    updateLog(pin, "auto")
    GPIO.output(pump_pin[pin], GPIO.LOW)
    time.sleep(pump_time)
    GPIO.output(pump_pin[pin], GPIO.HIGH)

def pump_stay_on(pin):
    updateLog(pin, "manual")
    GPIO.output(pump_pin[pin], GPIO.LOW)

def pump_off(pin):
    GPIO.output(pump_pin[pin], GPIO.HIGH)

def getLogs():
    result_arr = []
    try:
        file = glob.glob("/var/log/supervisor/plant_app-stderr*")
        cmd = subprocess.run(['tail', '-5', file[0]], universal_newlines=True, capture_output=True)
        result_arr.append(cmd.stdout)
    except Exception as ex:
        raise LoggedException(logger, "Can't access /var/log/supervisor most likely.", ex) from None
    
    try:
        file = glob.glob("/var/log/supervisor/plant_app-stdout*")
        cmd = subprocess.run(['tail', '-5', file[0]], universal_newlines=True, capture_output=True)
        result_arr.append(cmd.stdout)
    except Exception as ex:
        raise LoggedException(logger, "Can't access /var/log/supervisor most likely.", ex) from None

    
    return result_arr

if __name__ == "__main__":
    print('this file isnt meant to be called directly unless testing')
    pass
    
init()
# logger.info('starting with sensors %s' , reduce(lambda x, y: str(x) + ', ' + str(y), active_sensors))
logger.info('starting with sensors %s' % active_sensors)