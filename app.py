from flask import Flask, render_template, redirect, url_for

import water
import datetime
from flask_bootstrap import Bootstrap4
import subprocess
from common import *
import logging
import db
logger = logging.getLogger(__name__)

try:
    app = Flask(__name__)
except Exception as ex:
    raise LoggedException(logger, "Error in Flask process.", ex)
bootstrap = Bootstrap4(app) 
water.init()

active_apps = [None, None]
programs = [
    "water",
    "environmental_recorder",
]

### LOCAL FUNCTION DEFINITIONS ### 
def toDict(self):
    return {
        'Row ID' : self[0],
        'Date' : self[1],
        'Temp' : self[2],
        'Humidity' : self[3],
        'Pressure(kPa)' : self[4],
        'Gas Resistance(Ohms)' : self[5],
        'AQI' : self[6],
        'Soil 1' : self[7],
        'Soil 2' : self[8],
        'Soil 3' : self[9],
        'Soil 4' : self[10],
        'eCO2' : self[11],
        'TVOC' : self[12]
    }

def toPumpDict(self):
    return {
        'Row ID' : self[0],
        'Pump ID' : self[1],
        'Date' : self[2],
        'Method' : self[3],
    }

## TEMPLATES ##
def template(title = "", text = ""):
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M:%S")
    templateData = {
        'title' : title,
        'time' : timeString,
        'text' : text
        }
    return templateData

def data_template(title = "", data = [], text = "", status=None):
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M:%S")
    templateData = {
        'title' : title,
        'time' : timeString,
        'data' : data,
        'text' : text,
        'status': status,
        }
    return templateData

def table_template(title = "", data = [], text = "", table=None, status=None):
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M:%S")
    templateData = {
        'title' : title,
        'time' : timeString,
        'data' : data,
        'text' : text,
        'status': status,
        'table': table,
        }
    return templateData

def home_template(soil, last_water, current_env, programs, active_sensors, host_data, title = "Home"):
    now = datetime.datetime.now()
    timeString = now.strftime("%c")
    templateData = {
        'time': timeString,
        'title' : title,
        'soil': soil,
        'last_water': last_water,
        'current_env': current_env,
        'programs': programs,
        'active_sensors': active_sensors,
        'host_data': host_data
        }
    return templateData

## GET DATA ##
def getSoilStatus():
    return water.get_soil_status()

def getPumpStatus():
    retVal = []
    status_arr = []
    status_arr.append("OFF" if water.getPinState(0) == 0 else "ON")
    status_arr.append("OFF" if water.getPinState(1) == 0 else "ON")
    status_arr.append("OFF" if water.getPinState(2) == 0 else "ON")
    status_arr.append("OFF" if water.getPinState(3) == 0 else "ON")

    rawData = getAllADSRaw()

    retVal.append(status_arr)
    retVal.append(rawData)
    return retVal

def getLastWatered():
    return db.query(query='''select PUMPS.* from PUMPS ,
           (select pump_id,max(time) as date
                from PUMPS
                group by pump_id) max_date
             where PUMPS.pump_id=max_date.pump_id
             and PUMPS.time=max_date.date  ORDER BY PUMPS.pump_id ASC ;''')

def getEnvironmentStatus():
    current = db.query(query='''SELECT * FROM SENSOR_READINGS ORDER BY id DESC LIMIT 1;''')
    return current

def getActiveSensor():
    return water.sensor_state()

def getHostStats():
    # TODO: Add temperature of Pi, esp32 should be able to also report core temp
    proc=subprocess.check_output(["./hwid.sh"]) 
    return proc.decode().split('\n') 

def getRunning(program=None):
    global programs
    ret=[]
    for prog in programs:
        ret.append(check_process(prog))

    return ret

def getAllData():
    _data = []
    _data.append(getSoilStatus())
    _data.append(getLastWatered())
    _data.append(getEnvironmentStatus())
    _data.append(getRunning())
    _data.append(getActiveSensor())
    _data.append(getHostStats())
    return _data

## ROUTES ##
@app.route("/")
def home():
    templateData = home_template(title = "Home", *getAllData())
    return render_template('main.html', **templateData)

@app.route("/logs")
def logs():
    data = water.getLogs()
    print('logs =', logs)
    templateData = data_template(title = "Logs", data = data)
    return render_template('logs.html', **templateData)

@app.route("/soil")
def soil():
    temp = getSoilStatus()
    templateData = table_template(title = "Soil", data = temp)
    return render_template('tables/pump_table.html', **templateData)

@app.route("/environment")
def environment():
    templateData = data_template(title = "Environment", status=check_process("environmental_recorder"))
    return render_template('tables/sensor_table.html', **templateData)

@app.route("/pump")
def pump():
    templateData = data_template(title = "Pump", data = getPumpStatus(), text=water.sensor_state())
    return render_template('pump.html', **templateData)

@app.route("/processes")
def processes():
    templateData = template(text = "ya ya getting processes")
    return render_template('processes.html', **templateData)

## ACTIVE ROUTES ## 
@app.route("/errors/clear")
def clear():
    water.clear_errors()
    templateData = template(text = "errors cleared")
    return render_template('main.html', **templateData)

@app.route("/water/<pin>/<toggle>")
def pump_toggle(toggle, pin):
    if toggle == "ON":
        water.pump_stay_on(int(pin))
    else:
        water.pump_off(int(pin))

    templateData = data_template(title = "Pump", data = getPumpStatus())
    return render_template('pump.html', **templateData)

# @app.route("/water1/<toggle>")
# def pump1(toggle):
#     if toggle == "ON":
#         water.pump_stay_on(0)
#     else:
#         water.pump_off(0)

#     templateData = data_template(title = "Pump", data = getPumpStatus())
#     return render_template('pump.html', **templateData)

# @app.route("/water2/<toggle>")
# def pump2(toggle):
#     if toggle == "ON":
#         water.pump_stay_on(1)
#     else:
#         water.pump_off(1)

#     templateData = data_template(title = "Pump", data = getPumpStatus())
#     return render_template('pump.html', **templateData)

# @app.route("/water3/<toggle>")
# def pump3(toggle):
#     if toggle == "ON":
#         water.pump_stay_on(2)
#     else:
#         water.pump_off(2)

#     templateData = data_template(title = "Pump", data = getPumpStatus())
#     return render_template('pump.html', **templateData)

# @app.route("/water4/<toggle>")
# def pum43(toggle):
#     if toggle == "ON":
#         water.pump_stay_on(3)
#     else:
#         water.pump_off(3)

#     templateData = data_template(title = "Pump", data = getPumpStatus())
#     return render_template('pump.html', **templateData)


@app.route("/water/sensor/<pin>")
def sensor_toggle(pin):
    water.toggle_sensor(int(pin))
    status = water.sensor_state()
    templateData = data_template(title = "Pump", text = status, data = getPumpStatus())
    return render_template('pump.html', **templateData)

#### API ROUTE #####
@app.route('/api/data/sensor')
def data():
    arr = db.get_all_rows(table="SENSOR_READINGS", limit="200000", order="time DESC")
    return {'data': [toDict(row) for row in arr] }

@app.route('/api/data/pumps')
def pump_data():
    arr = db.get_all_rows(table="PUMPS", limit="200000", order="time DESC")
    return {'data': [toPumpDict(row) for row in arr] }

@app.route('/api/process/water/start')
def start_water():
    templateData = template(text = start_process('water'))
    return render_template('processes.html', **templateData)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)