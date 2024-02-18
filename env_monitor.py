import bme680
import time
from datetime import datetime
import db
import RPi.GPIO as GPIO
from water import get_soil_status
import adafruit_ccs811
import busio
import board

from configs import *


def burnIn(_time = 300, save=True):
    
    start_time = time.time()
    curr_time = time.time()
    burn_in_time = _time

    burn_in_data = []
     
    if save: f = open("burn_data.txt", "w")
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            burn_in_data.append(gas)
            # print('Gas: {0} Ohms'.format(gas))
            if save: f.write('{:.2f}\n'.format(gas))
            time.sleep(1)
    if save: f.close()
    return burn_in_data


def runBurnIn():
    burnIn(300, True)

def aqScore(gas, use_saved_value=True):
    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25


    if use_saved_value:
        burn_in_data = []
        #get from file saved value
        file = open('burn_data.txt', 'r') 
        for y in file.readlines():
            burn_in_data.append(float(y))        
    else:
        burn_in_data = burnIn(30, True)

    gas_baseline = sum(burn_in_data[-50:]) / 50.0

    gas_offset = gas_baseline - gas
    hum = sensor.data.humidity
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
    _time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    sensor_aggregate =[*ss, *soil_status]
    db.insert_data(time=_time, *sensor_aggregate)

    time.sleep(60) 


def poll():
    ss = snapshot(False)
    print("SS", *ss)
    if len(ss) < 5:
        burnIn(5, False)
        ss = snapshot(False)
    soil_status = get_soil_status()
    
    sensor_aggregate =[*ss, *soil_status]
    print(sensor_aggregate)
    time.sleep(5) 

def snapshot(burn=False, attempt=0):
    global sensor
    global ccs
    attempt += 1;
    if sensor is None: raise("BME680 COMMS ERROR")
    snap = [];
    if attempt == 3:
        raise Exception('no sensor reading bme680')

    if not sensor.data.heat_stable:
        burn = True;

    if burn:
        burnIn(5, False)
        time.sleep(0.25) # give sensor a second to calculate probably dont need this to be honest

    if sensor.get_sensor_data():
        ccs.set_environmental_data(sensor.data.humidity, sensor.data.temperature)
        # print(sensor.data.temperature)
        snap.append(sensor.data.temperature)
        snap.append(sensor.data.pressure)
        snap.append(sensor.data.humidity)

        if sensor.data.heat_stable:
            snap.append(sensor.data.gas_resistance)
            snap.append(aqScore(sensor.data.gas_resistance))
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

    if len(snap) < 5:
        snapshot(False, attempt)
    return snap




def toggle_reset():
    GPIO.output(23, GPIO.LOW)
    time.sleep(.2)
    GPIO.output(23, GPIO.HIGH)
    time.sleep(0.5)



def init():
    global sensor
    global ccs
    if sensor is None and ccs is None:
   
        GPIO.setup(23, GPIO.OUT)
        GPIO.output(23, GPIO.HIGH)
        i2c = busio.I2C(board.SCL, board.SDA)   # uses board.SCL and board.SDA

            
        toggle_reset() # do this early so any start up stuff can happen

        try:
            sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
            sensor.set_humidity_oversample(bme680.OS_2X)
            sensor.set_pressure_oversample(bme680.OS_4X)
            sensor.set_temperature_oversample(bme680.OS_8X)
            sensor.set_filter(bme680.FILTER_SIZE_3)
            sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

            print('\n\nInitial reading:')
            for name in dir(sensor.data):
                value = getattr(sensor.data, name)

                if not name.startswith('_'):
                    print('{}: {}'.format(name, value))

            sensor.set_gas_heater_temperature(320)
            sensor.set_gas_heater_duration(150)
            sensor.select_gas_heater_profile(0)
        except:
            raise RuntimeError('no BME680')

        try:
        
            ccs =  adafruit_ccs811.CCS811(i2c, 0x5a)
        except:
            raise RuntimeError('ccs811 error')
    

def env_record(startup=False):
    if startup:
        init()
        print(burnIn(5, False))

    while True:
        poll_insert();  


# These calibration data can safely be commented
# out, if desired.

# print('Calibration data:')
# for name in dir(sensor.calibration_data):

#     if not name.startswith('_'):
#         value = getattr(sensor.calibration_data, name)

#         if isinstance(value, int):
#             print('{}: {}'.format(name, value))

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.



# Up to 10 heater profiles can be configured, each
# with their own temperature and duration.
# sensor.set_gas_heater_profile(200, 150, nb_profile=1)
# sensor.select_gas_heater_profile(1)

if __name__ == "__main__":
    print('this file isnt meant to be called directly unless testing')
    init()
    print('starting from env')
    try:
       while 1:
            burnIn(5, True)
            poll()      
    except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
        pass
