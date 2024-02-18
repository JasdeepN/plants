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
import subprocess
import shlex
app = Flask(__name__)
# mqtt = Mqtt(app)
# socketio = SocketIO(app)


# DECLARE AND INIT #

bootstrap = Bootstrap4(app) 
water.init()

active_apps = [None, None]
programs = [
    "auto_water.py",
    "auto_env.py"
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
        'eCO2' : self[11]
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

## GET DATA ##
def getSoilStatus():
    return water.get_soil_status()

def getPumpStatus():
    pump_arr = []
    pump_arr.append("OFF" if water.getPinState(0) == 0 else "ON");
    pump_arr.append("OFF" if water.getPinState(1) == 0 else "ON");
    pump_arr.append("OFF" if water.getPinState(2) == 0 else "ON");
    pump_arr.append("OFF" if water.getPinState(3) == 0 else "ON");
    return pump_arr

def getRunning():
    global active_apps
    active_apps = []
    for target in programs:
        active_apps.append(verification(target))
    return active_apps
            
    
def verification(prog):
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == "python" and len(p.cmdline()) > 1 and prog in p.cmdline()[1]:
            return True
    return False


def checkRunning(program=None):
    global programs
    global active_apps
    getRunning()
    print('checking for', program)

    if program == None: 
        out=[]    
        for target in active_apps:
            if target is None:
                out.append(programs[target]+" Process Not Started.")
            elif target is False:
                out.append(programs[target] + " not found")
            else:
                out.append(programs[target] +'Running')
        
        return out
    else:
        retVal = programs[program] + " Not Found."
        try:
            if (active_apps[program] is not None):
                retVal =  "Already running";
        except:
            pass
        return retVal

def getAllData():
    _data = []
    _data.append(getSoilStatus());
    _data.append(getPumpStatus());
    # _data.append(getEnvironmentalStatus());
    return _data


## ROUTES ##
@app.route("/")
def home():
    templateData = template(title = "Home")
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
    templateData = data_template(title = "Environment", status=checkRunning(program=1))
    return render_template('tables/sensor_table.html', **templateData)

@app.route("/pump")
def pump():
    templateData = data_template(title = "Pump", data = getPumpStatus())
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


@app.route("/auto/sensor/<pin>")
def sensor_toggle(pin):
  
    water.toggle_sensor(int(pin))
    status = water.sensor_state()
    templateData = template(title = "Home", text = status)
    return render_template('main.html', **templateData)


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
