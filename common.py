import ADS1x15
import subprocess
import os
import logging
import datetime
import io
import traceback
import atexit
from db import create_connection
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DEBUG = os.getenv('DEBUG')
LOGFILE = os.getenv("LOGFILE_NAME")
ADS_1115_ADDR = int(os.getenv("ADS1115_ADDR"), 16)

conn = create_connection();
while conn is None:
  print("waiting for db");
  logger.info('no db..waiting')
cursor = conn.cursor(buffered=True);

def exit_handler():
    logger.info("Exit Cleanly.")

atexit.register(exit_handler);

def get_exception_traceback_str(exc: Exception) -> str:
    # Ref: https://stackoverflow.com/a/76584117/
    file = io.StringIO()
    traceback.print_exception(exc, file=file)
    return file.getvalue().rstrip()

class LoggedException(Exception):
    """ An exception that also logs the msg to the given logger. """
    def __init__(self, logger: logging.Logger, msg: str, ex: Exception):
        logger.error(msg)
        if ex is not None: 
            trace = get_exception_traceback_str(ex)
            logger.error(ex)
            logger.error(trace)
            print(trace)
        super().__init__(msg)

logging.basicConfig(filename=LOGFILE,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

now = datetime.datetime.now()
timeString = now.strftime("%H:%M:%S")
logger.info(' > > > > > App start @ ' + timeString + ' < < < < < ')

ADS = None
ADS_MAP = {
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

bme_680 = None;
ccs = None;

logger.info('Setting up ADS ADC1115..')
try:
    ADS = ADS1x15.ADS1115(1, ADS_1115_ADDR)
    ADS.setGain(1)
except Exception as ex:
    raise LoggedException(logger, 'Couldn\'t setup ADS1115.', ex) from None

logger.info('ADS1115 setup complete.')

def getADSRaw(channel):
    global ADS
    return ADS.readADC(channel)
  
def getAllADSRaw():
    retVal = []
    for channel in sensorADSPin:
        retVal.append(getADSRaw(channel))
    return retVal

"""
Starts process using supervisord (supervisorctl)
"""
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

"""
Checks if process is running through supervisor 
"""
def check_process(proc):
    process = subprocess.Popen(['sudo', 'supervisorctl', 'status', proc],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    returncode = process.wait()
    # print('RETURN CODE {0}'.format(returncode))
    return [returncode, process.stdout.read().decode()]

