import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, return_code):
    if return_code == 0:
        print("connected")
        client.subscribe("test/1")
    else:
        print("could not connect, return code:", return_code)
        client.failed_connect = True


def on_message(client, userdata, message):
    print("Received message: ", str(message.payload.decode("utf-8")))


broker_hostname ="172.0.10.3"
port = 1883 

client = mqtt.Client("pi")
client.username_pw_set(username="user", password="password") # uncomment if you use password auth
client.on_connect = on_connect
client.on_message = on_message
client.failed_connect = False

client.connect(broker_hostname, port) 
client.loop_start()

# this try-finally block ensures that whenever we terminate the program earlier by hitting ctrl+c, it still gracefully exits
try:
    while True and client.failed_connect == False:
        time.sleep(1)
    if client.failed_connect == True:
        print('Connection failed, exiting...')

finally:
    client.disconnect()
    client.loop_stop()
