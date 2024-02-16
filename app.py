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

bootstrap = Bootstrap4(app) 
water.init()
# # 
# id INT NOT NULL AUTO_INCREMENT,
#             time DATETIME NOT NULL,
#             temp DOUBLE NULL,
#             humidity DOUBLE NULL,
#             pressure DOUBLE NULL,
#             gas_resistance DOUBLE NULL,
#             aq_calculated DOUBLE NULL,
#             soil_1 BOOLEAN NULL,
#             soil_2 BOOLEAN NULL,
#             soil_3 BOOLEAN NULL,
#             soil_4 BOOLEAN NULL,
#             PRIMARY KEY (id)


active_apps = [None, None]
   
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

def getSoilStatus():
    status_arr = []
    status_arr.append(water.get_soil_status(0));
    status_arr.append(water.get_soil_status(1));
    status_arr.append(water.get_soil_status(2));
    status_arr.append(water.get_soil_status(3));

    return status_arr

def getPumpStatus():
    pump_arr = []
    pump_arr.append("OFF" if water.getPinState(0) == 0 else "ON");
    pump_arr.append("OFF" if water.getPinState(1) == 0 else "ON");
    pump_arr.append("OFF" if water.getPinState(2) == 0 else "ON");
    pump_arr.append("OFF" if water.getPinState(3) == 0 else "ON");


    
    return pump_arr

def checkRunning(program=None):
    print('checking for', program)
    programs = [
        "auto_water.py",
        "auto_env.py"
    ]
    if program == None: 
        out=[]    
        for target in active_apps:
            if target is not None:
                out.append(programs[target]+" Process Found.")
            else:
                out.append(programs[target] + " not found")
        
        return out
    else:
        retVal = programs[program] + " Not Found."
        try:
            if (active_apps[program] is not None):
                retVal =  "Already running";
        except:
            pass
        return retVal
  
@app.route("/auto/env/test")
def getEnvironmental():
    env_arr = water.getEnvData(False);
    templateData = data_template(title = "Auto", data = env_arr)
    return render_template('auto.html', **templateData)

@app.route("/auto/env/dump/db")
def getDB():
    templateData = data_template(title = "Auto", status=checkRunning(program=1))
    return render_template('tables/sensor_table.html', **templateData)

@app.route('/api/data/sensor')
def data():
    arr = db.get_all_rows(table="SENSOR_READINGS", limit="2000", order="time DESC")
    # print([toDict(row) for row in arr] )
    return {'data': [toDict(row) for row in arr] }

@app.route("/auto/env/dump/pump")
def getRow():
    # arr = db.getRows(3, "PUMPS", where="pump_id = 0", modifier="latest")
    arr = db.get_all_rows(table="PUMPS")
    # print('db ->', arr)
    templateData = data_template(title = "Auto", data = arr)
    return render_template('tables/pump_table.html', **templateData)

@app.route("/auto/env/pump_test")
def getpumpDB():
    arr = water.pumpInsert()
    templateData = data_template(title = "Auto", data = arr)
    return render_template('auto.html', **templateData)


def getAllData():
    _data = []
    _data.append(getSoilStatus());
    _data.append(getPumpStatus());
    # _data.append(getEnvironmentalStatus());
    return _data

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
    # templateData = template(title = "Soil")
    temp = getSoilStatus()
    print(temp)
    templateData = data_template(title = "Soil", data = temp)
    return render_template('soil.html', **templateData)

@app.route("/auto")
def auto():
    templateData = data_template(title = "Auto")
    return render_template('auto.html', **templateData)

@app.route("/auto/env/read")
def get_env():
    water.getEnvData(burn=True);
    templateData = data_template(title = "env", text = "getting status")
    return render_template('auto.html', **templateData)

@app.route("/pump")
def pump():
    templateData = data_template(title = "Pump", data = getPumpStatus())
    return render_template('pump.html', **templateData)


@app.route("/last_watered")
def check_last_watered():
    templateData = data_template(title = "last water", data = water.get_last_watered())
    return render_template('main.html', **templateData)

@app.route("/sensor1")
def action6():
    status = water.get_soil_status(0)
    message = ('plant 1 sensor '+ status) 

    templateData = template(text = message)
    return render_template('main.html', **templateData)

@app.route("/sensor2")
def action7():
    status = water.get_soil_status(1)
    message = ('plant 2 sensor '+ status) 

    templateData = template(text = message)
    return render_template('main.html', **templateData)

@app.route("/sensor3")
def action5():
    status = water.get_soil_status(2)  
    message = ('plant 3 sensor '+ status) 

    templateData = template(text = message)
    return render_template('main.html', **templateData)

# @app.route("/water1")
# def action2():
#     water.pump_on(0)
#     templateData = template(text = "Watered Once")
#     return render_template('main.html', **templateData)

@app.route("/errors/clear")
def clear():
    water.clear_errors()
    templateData = template(text = "errors cleared")
    return render_template('main.html', **templateData)

@app.route("/processes")
def processes():
    templateData = template(text = "ya ya getting processes")
    return render_template('processes.html', **templateData)

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

# active_apps = [
#     subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 0'),start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
#     subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 1'),start_new_session=True, stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
#     subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py 2'),start_new_session=True, stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
# ]

@app.route("/auto/water/<toggle>")
def auto_water(toggle): 
    
    # water_log = open('auto_water.txt', 'a')
    # water_log.write('some text, as header of the file\n')
    # water_log.flush()  # <-- here's something not to forget!


    if toggle == "ON":
        templateData = template(text = "Already Running")

        if (active_apps[0] is None):
            templateData = template(text = "attempting startup...")
            # active_apps[0] = subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py'),start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
          
            # with open('auto_water.txt', 'a') as f:
            #     os.set_blocking(f.fileno(), False)
            #     active_apps[0] = subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_water.py'), stdin=subprocess.DEVNULL, stdout=f.fileno(), stderr=subprocess.STDOUT)
      
            # os.system("/home/admin/plants/.venv/bin/python3 auto_water.py& 0")
            # print(active_apps[0].check_output('python'))
            print("should be running...", active_apps[0] is not None)
    elif active_apps[0] is None:
        templateData = template(text = "Not Turned ON!")
    else:
        try:
            templateData = template(text = "Auto Watering Off")
            os.system("pkill -f 'auto_water.py'")
            active_apps[0] = None
        except:
            templateData = template(text = "error running pkill on AutoWater.py!!!!")
    
    return render_template('main.html', **templateData)



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

@app.route("/about")
def about():
    templateData = template(title = "About")
    return render_template('about.html', **templateData)


@app.route("/auto/env/record/<toggle>")
def record_env(toggle):
    # env_log = open('auto_env.txt', 'a')
    # env_log.write('some text, as header of the file\n')
    # env_log.flush()  # <-- here's something not to forget!

    if toggle == "ON":
        templateData = template(text = "ENV RECORDER ON")
        try:
            if (active_apps[1] is not None):
                templateData = template(text = "Already running env") 
        except:
            pass
        if (active_apps[1] is None):
            templateData = template(text = "attempting startup...")
            active_apps[1] = subprocess.Popen(shlex.split('/home/admin/plants/.venv/bin/python3 auto_env.py'),start_new_session=True, stdin=env_log, stdout=env_log, stderr=env_log),
            # os.set_blocking(env_log.stdout.fileno(), False)
            
            # os.system("/home/admin/plants/.venv/bin/python3 auto_water.py& 1")
            # print(active_apps[1].check_output('python'))
            print("should be running...", active_apps[1] is not None)
    else:
        try:
            templateData = template(text = "ENV RECORDER Off")
            os.system("pkill -f 'auto_env.py'")
            active_apps[1] = None

        except:
            templateData = template(text = "Recorder Not Turned ON!")
    return render_template('main.html', **templateData)




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
