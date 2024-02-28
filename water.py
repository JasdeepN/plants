import RPi.GPIO as GPIO
import time
from datetime import datetime
import subprocess
import glob
import db
import json 

import hashlib

from configs import * 

def init():
    global md5_sense
    global active_sensors
    global pump_pin
    global ADS
    GPIO.setwarnings(False)
    # GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
    mode = GPIO.getmode()
    try:
        if modes[mode] == "BCM" or 11:
            pump_pin = [4,17,27,22]
        elif modes[mode] == "BOARD" or 10:
            pump_pin = [7,11,13,15]
    except:
        print('setting GPIO mode')
        GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
        pump_pin = [4,17,27,22]
    print('setting up pump pins %s...' % pump_pin)

    for pin in pump_pin:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
    
    print('pump pins set successfully')

    startup = [False, False, False, False]
    print('setting sensor file defaults all off')
    with open('.sense.cfg', 'w+', encoding='utf-8') as filehandle:
        json.dump(startup, filehandle)
        md5_sense=hashlib.md5(filehandle.read().encode('utf-8')).hexdigest()
        filehandle.close()
    
    active_sensors = startup #no need for file read we start will all sensors off
    print('sensor file set')

    print('setup complete using file hash', md5_sense)
  

def toggle_sensor(pin=None):
    # global file_change
    pin = int(pin)
    global active_sensors
    if pin is None: return
    active_sensors[pin]=not active_sensors[pin]
    with open('.sense.cfg', 'w') as filehandle:
        json.dump(active_sensors, filehandle)
        filehandle.close()


def deactivate(pin=None):
    global active_sensors
    active_sensors[pin] = False
    with open('.sense.cfg', 'w') as filehandle:
        json.dump(active_sensors, filehandle)
        filehandle.close()
    active_sensors = loadSensors() # force reload with sensor disabled

def clear_errors():
    global power_on_count
    power_on_count = [0,0,0,0]

def sensor_state():
    global active_sensors
    return active_sensors

def loadSensors():
    print('loading sensor config...')
    # global file_change
    # file_change = False # turn off read flag
    with open(".sense.cfg", "r") as f:
        _f= f.read().encode('utf-8')
        f.close()
        print('gonna give back', json.loads(_f))
        return json.loads(_f)
    
def get_soil_status(pin = None):
    global sensorADSPin
    global ADS
    if pin == None:
        out = []
        # for pin in water_sensor_pin:
        for pin in sensorADSPin:
            # print('testing channel', pin)
            # GPIO.setup(pin, GPIO.IN)
            out.append(getSensorState(pin)) 
        return out
    else:
        # GPIO.setup(water_sensor_pin[pin], GPIO.IN)
        # return getSensorState(water_sensor_pin[pin])
        # print( ADS.readADC(pin))
        return getSensorState(pin)
   


def auto_water(pump_time = 20, sense_time=60):   
    # global file_change
    global active_sensors
    global power_on_count

    power_on_count=[0,0,0,0]
    try:
        while 1:
            print('start checking the ADS channels')
            checkFile()# if file_change update list of sensors to use
            for pin in sensorADSPin:
                if active_sensors[pin]:
                    print('pin %s running power count=%s' % (pin, power_on_count))
                    if power_on_count[pin] <= 5:
                        dry = get_soil_status(pin) == "dry"
                        print('status', dry)
                        if dry:
                            pump_on(pin, pump_time) # time pump stays on
                            power_on_count[pin] += 1
                        else:
                            power_on_count[pin] = 0 # reset safety counter 
                    else:    
                        pump_off(pin) # just in case
                        print('there might be something wrong with the sensor on pin %d' % pin)
                        deactivate(pin) #stop from running this pump until manually turned back on
                        pass # ? do we need this..probably not but whatever
                else:
                    print('pin %d is inactive' % pin)
            time.sleep(sense_time) # check soil every x seconds        
    except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
        pass

def checkFile():
    global active_sensors
    global md5_sense

    if md5_sense is None:  
        with open('.sense.cfg', 'r', encoding='utf-8') as filehandle:
            md5_sense=hashlib.md5(filehandle.read().encode('utf-8')).hexdigest()
            filehandle.close()
    else:
        with open('.sense.cfg', 'r', encoding='utf-8') as filehandle:
            new_hash=hashlib.md5(filehandle.read().encode('utf-8')).hexdigest()
            print('new file hash', new_hash)
            print('old file hash', md5_sense)
            if new_hash == md5_sense:
                print('no file change')
            else:
                print('loading new file')
                md5_sense=new_hash #update file hash
                active_sensors=loadSensors()

            filehandle.close()

def getPinState(pin):
    # GPIO.setup(pump_pin[pin], GPIO.OUT)
    state = GPIO.input(pump_pin[pin])
    print("pin %s state %s" % (pump_pin[pin], state))
    if state:
        return 0
    else:
        return 1

def getSensorState(channel):
    value = ADS.readADC(channel)
    for map_val in data_map:
        val=data_map.get(map_val)
        if val[0] <= value <= val[1]:
            # print(value)
            # return ("channel %d %s" % (channel, map_val))
            return map_val


def updateLog(pin = None, msg = ""):
    if pin == None: return;
    _time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _msg = 0 if msg == "manual" else 1

    pump_data=[pin, _msg]
    db.insert_data_from_pump(time=_time, pump_data=pump_data)
   

def pump_on(pin, delay = 1):
    # init_output(pump_pin[pin])
    updateLog(pin, "auto")
    GPIO.output(pump_pin[pin], GPIO.LOW)
    time.sleep(delay)
    GPIO.output(pump_pin[pin], GPIO.HIGH)

def pump_stay_on(pin):
    # init_output(pump_pin[pin])
    updateLog(pin, "manual")
    GPIO.output(pump_pin[pin], GPIO.LOW)


def pump_off(pin):
    # init_output(pump_pin[pin])
    GPIO.output(pump_pin[pin], GPIO.HIGH)


def getLogs():
    result_arr = []

    file = glob.glob("/var/log/supervisor/plant_app-stderr*")
    cmd = subprocess.run(['tail', '-5', file[0]], universal_newlines=True, capture_output=True)
    # cmd = cmd.decode('utf8', errors='strict').strip()
    # out = cmd.stdout.decode('utf-8')
    # print('get', cmd.stdout)
   
    result_arr.append(cmd.stdout);

    file = glob.glob("/var/log/supervisor/plant_app-stdout*")
    cmd = subprocess.run(['tail', '-5', file[0]], universal_newlines=True, capture_output=True)
    # cmd = cmd.decode('utf8', errors='strict').strip()
    # out = cmd.stdout.decode('utf-8')
    # print('get', cmd.stdout)
    result_arr.append(cmd.stdout);

  
    return result_arr


if __name__ == "__main__":
    print('this file isnt meant to be called directly unless testing')
    pass
    
init()
print('starting with sensors', active_sensors)