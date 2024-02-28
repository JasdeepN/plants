from flask import Flask, render_template, redirect, url_for
import psutil
import datetime
import water
import os
import json
import db 
# from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap4
# from flask_mqtt import Mqtt
from env_monitor import getLastReading
from subprocess import call
import subprocess
from configs import start_process, check_process, getAllADSRaw

app = Flask(__name__)
# mqtt = Mqtt(app)
# socketio = SocketIO(app)

# DECLARE AND INIT #

bootstrap = Bootstrap4(app) 
water.init()

active_apps = [None, None]
programs = [
    "water",
    "environmental_recorder",
]

######

### LOCAL FUNCTION DEFINITIONS ### 
def toDict(self):
    # print ('got', len(self))
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
    # print ('pump got', len(self))
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

def table_template(title = "", data = [], text = "", table= None, status=None):
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
    status_arr.append("OFF" if water.getPinState(0) == 0 else "ON");
    status_arr.append("OFF" if water.getPinState(1) == 0 else "ON");
    status_arr.append("OFF" if water.getPinState(2) == 0 else "ON");
    status_arr.append("OFF" if water.getPinState(3) == 0 else "ON");

    rawData = getAllADSRaw();

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
    # print('last water', temp)

def getEnvironmentStatus():
    current = db.query(query='''SELECT * FROM SENSOR_READINGS ORDER BY id DESC LIMIT 1;''')
    # current = snapshot()
    return current


def getActiveSensor():
    return water.sensor_state()

def getHostStats():
    # proc=call()
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
    _data.append(getSoilStatus());
    _data.append(getLastWatered());
    _data.append(getEnvironmentStatus());
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
    data = water.getLogs();
    print('logs =', logs)
    templateData = data_template(title = "Logs", data = data);
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


@app.route("/water1/<toggle>")
def pump1(toggle):
    running = False
    if toggle == "ON":
        water.pump_stay_on(0)
    else:
        water.pump_off(0)

    templateData = data_template(title = "Pump", data = getPumpStatus())
    return render_template('pump.html', **templateData)

@app.route("/water2/<toggle>")
def pump2(toggle):
    running = False

    if toggle == "ON":
        water.pump_stay_on(1)
    else:
        water.pump_off(1)

    templateData = data_template(title = "Pump", data = getPumpStatus())
    return render_template('pump.html', **templateData)

@app.route("/water3/<toggle>")
def pump3(toggle):
    running = False
    if toggle == "ON":
        water.pump_stay_on(2)
    else:
        water.pump_off(2)

    templateData = data_template(title = "Pump", data = getPumpStatus())
    return render_template('pump.html', **templateData)

@app.route("/water4/<toggle>")
def pum43(toggle):
    running = False
    if toggle == "ON":
        water.pump_stay_on(3)
    else:
        water.pump_off(3)

    templateData = data_template(title = "Pump", data = getPumpStatus())
    return render_template('pump.html', **templateData)


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
    # print([toDict(row) for row in arr] )
    return {'data': [toDict(row) for row in arr] }


@app.route('/api/data/pumps')
def pump_data():
    arr = db.get_all_rows(table="PUMPS", limit="200000", order="time DESC")
    # print([toPumpDict(row) for row in arr] )
    return {'data': [toPumpDict(row) for row in arr] }


@app.route('/api/process/water/start')
def start_water():
    # print([toPumpDict(row) for row in arr] )
    templateData = template(text = start_process('water'))
    return render_template('processes.html', **templateData)
    # return water.start_process();


# THE ONLY ONE???

# active_apps = [
#     subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 0'),start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
#     subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 1'),start_new_session=True, stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
#     subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 2'),start_new_session=True, stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
# ]



# @app.route("/auto/water2/<toggle>")
# def auto_water2(toggle):
#     if toggle == "ON":
#         templateData = template(text = "Auto Watering 2 On")
#         try:
#             if (active_apps[1] is not None):
#                 templateData = template(text = "Already running") 
#         except:
#             pass
#         if (active_apps[1] is None):
#             templateData = template(text = "attempting startup...")
#             active_apps[1] = subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 1'),start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
#             # os.system("/home/admin/plants/.venv/bin/python3 auto_water.py& 1")
#             # print(active_apps[1].check_output('python'))
#             print("should be running...", active_apps[1] is not None)
#     else:
#         try:
#             templateData = template(text = "Auto Watering 2 Off")
#             os.system("pkill -f 'auto_water.py 1'")
#             active_apps[1] = None

#         except:
#             templateData = template(text = "Not Turned ON!")
#     return render_template('main.html', **templateData)

# @app.route("/auto/water3/<toggle>")
# def auto_water3(toggle):
#     if toggle == "ON":
#         templateData = template(text = "Auto Watering 3 On")
#         try:
#             if (active_apps[2] is not None):
#                 templateData = template(text = "Already running") 
#         except:
#             pass
#         if (active_apps[2] is None):
#             templateData = template(text = "attempting startup...")
#             active_apps[2] = subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 2'),start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
#             # os.system("/home/admin/plants/.venv/bin/python3 auto_water.py& 2")
#             # print(active_apps[2].check_output('python'))
#             print("should be running...", active_apps[2] is not None)
#     else:
#         try:
#             templateData = template(text = "Auto Watering 3 Off")
#             os.system("pkill -f 'auto_water.py 2'")
#             active_apps[2] = None

#         except:
#             templateData = template(text = "Not Turned ON!")
#     return render_template('main.html', **templateData)



# @app.route("/auto/water4/<toggle>")
# def auto_water4(toggle):
#     running = False
#     if toggle == "ON":
#         templateData = template(text = "Auto Watering 4 On")
#         for process in psutil.process_iter():
#             try:
#                 if process.cmdline()[1] == 'auto_water3.py':
#                     templateData = template(text = "Already running")
#                     running = True
#             except:
#                 pass
#         if not running:
#             os.system("/home/admin/plants/.venv/bin/python4 auto_water.py& 4")
#     else:
#         templateData = template(text = "Auto Watering 4 Off")
#         os.system("pkill -f auto_water3.py")

#     return render_template('main.html', **templateData)





# @socketio.on('publish')
# def handle_publish(json_str):
#     data = json.loads(json_str)
#     mqtt.publish(data['topic'], data['message'])


# @socketio.on('subscribe')
# def handle_subscribe(json_str):
#     data = json.loads(json_str)
#     mqtt.subscribe(data['topic'])


# @socketio.on('unsubscribe_all')
# def handle_unsubscribe_all():
#     mqtt.unsubscribe_all()


# @mqtt.on_message()
# def handle_mqtt_message(client, userdata, message):
#     data = dict(
#         topic=message.topic,
#         payload=message.payload.decode()
#     )
#     socketio.emit('mqtt_message', data=data)


# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     print(level, buf)



# @socketio.on('my event')
# def handle_my_custom_event(json):
#     print('received json: ' + str(json))

# @socketio.on('run')
# def handle_my_run(**args):
#     for arg  in args:
#         print("need to do", arg)

# @socketio.on("/auto/env/burn_in")
# def burn():
#     socketio.emit('run', "burn")

#     # water.runBurnIn();
#     templateData = data_template(title = "BURN", text = "running burn in")
#     return render_template('auto.html', **templateData)

    
# @socketio.on('fe data')
# def handle_my_custom_event(json):
#     print('FE EVENT: ' + str(json))
    



# if __name__ == '__main__':
#     socketio.run(app, host='0.0.0.0', port=80, use_reloader=False, debug=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)