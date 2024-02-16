import ADS1x15

# initialize ADS1115 on I2C bus 1 with default address 0x48
ADS=None
hysteresis = 500 #not being used ram is cheap lol

data_map = {
    "wet": [0, 10000],
    "dry": [13001, 22000],
    "watered": [10001, 13000],
    "error":[22001, 50000]
}

modes = {-1:"Unset", 11:"BCM", 10:"BOARD"}
 

pump_pin = []

#water_sensor_pin = [8,12,16] ADS1115 channel 0-3 instead
sensorADSPin=[0,1,2,3]
active_sensors=[]
power_on_count = []
md5_sense=None



sensor = None;
ccs = None;

print('setting up ADS ADC1115 next..')

ADS = ADS1x15.ADS1115(1, 0x48)
ADS.setGain(1)