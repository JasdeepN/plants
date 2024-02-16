import busio
import adafruit_ccs811
import time
import board
from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
i2c = busio.I2C(board.SCL, board.SDA)
GPIO.setup(23, GPIO.OUT)
GPIO.output(23, GPIO.HIGH)

def toggle_reset():
    GPIO.output(23, GPIO.LOW)
    time.sleep(.2)
    GPIO.output(23, GPIO.HIGH)


toggle_reset()
sleep(1)
ccs =  adafruit_ccs811.CCS811(i2c, 0x5a)


while not ccs.data_ready:
    time.sleep(1)
    pass

while True:
    print("CO2: {} PPM, TVOC: {} PPB".format(ccs.eco2, ccs.tvoc))
    time.sleep(60)