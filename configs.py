import ADS1x15
import subprocess
# initialize ADS1115 on I2C bus 1 with default address 0x48
ADS=None
hysteresis = 500 #not being used ram is cheap lol

data_map = {
    "disconnected":[0, 8000],
    "wet": [8001, 10000],
    "dry": [13001, 22000],
    "watered": [10001, 13000],
    "error 1":[22001, 50000]
}

modes = {-1:"Unset", 11:"BCM", 10:"BOARD"}
 

pump_pin = []

#water_sensor_pin = [8,12,16] ADS1115 channel 0-3 instead
sensorADSPin=[0,1,2,3]
active_sensors=[]
power_on_count = []
md5_sense=None
currentEnvironmentVars=[]

sensor = None;
ccs = None;

print('setting up ADS ADC1115 next..')

ADS = ADS1x15.ADS1115(1, 0x48)
ADS.setGain(1)

def getADSRaw(channel):
    return ADS.readADC(channel)

def getAllADSRaw():
    retVal = []
    for channel in sensorADSPin:
        retVal.append(getADSRaw(channel))
    return retVal

def start_process(proc):
    check = check_process(proc);
    if (check[0] == 0): return check[1] 
    process = subprocess.Popen(['sudo', 'supervisorctl', 'start', proc],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    process.wait()
    # returncode = process.wait()
    # print('RETURN CODE {0}'.format(returncode))
    return process.stdout.read().decode()

def check_process(proc):
    process = subprocess.Popen(['sudo', 'supervisorctl', 'status', proc],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    returncode = process.wait()
    # print('RETURN CODE {0}'.format(returncode))
    return [returncode, process.stdout.read().decode()]
