import time
import paho.mqtt.client as mqtt
import util
import sensor_api as sapi



def get_sample(sensortype):
    #placeholder where we will insert the real sensor functions.
    sample, sample_ts = -1, -1
    if sensortype == "light":
        sample, sample_ts= sapi.get_light_sample()

        #("%d/%m/%Y %H:%M:%S")
    elif sensortype == "temp":
        sample, sample_ts = sapi.get_temperature_sample()

    else:
        print("must specify a type of sensor")
        print(sapi.permitted_sensors)
        return sample, sample_ts
    return sample, sample_ts


# The callback for when the client receives a CONNACK response from the server.


client = mqtt.Client()
client.on_connect = util.on_connect
client.on_message = util.on_message




print(util.server)
client.connect(util.server,1883,60)
######################### Logic for furter programming #######################

# sample, timestamps = Get_samples()
# Logic for what to do....
# Connect via nb-iot and send message - client-side logic
# Prepare messages and input into ["topic", "payload", "timestamps"]
# Message is sent via mqtt to the server


#example of getting max sample observed every minute seconds
counter = 0
arr_size = 6
sensor1 = "light"
sensor2= "temp"
userid=util.userid
extra_counter=0
data_light = [0] * arr_size
timestamps_light = [0] * arr_size
data_temp = [0] * arr_size
timestamps_temp = [0] * arr_size
while(1):

    time.sleep(1)
    sample,ts  = get_sample(sensor1)
    data_light[counter]=round(sample, 2)
    timestamps_light[counter]=str(ts)



    sample,ts  = get_sample(sensor2)
    data_temp[counter]=round(sample, 2)
    timestamps_temp[counter]=str(ts)
    counter+=1

    if counter == arr_size:
        extra_counter+=1
        counter = 0

        data=util.prepare_payload([sensor1, sensor2], [data_light, data_temp], [[timestamps_light[0]], [timestamps_temp[0]]])
        util.send_topics(data,userid,client)
        data_light = [0] * arr_size
        timestamps_light = [0] * arr_size
        data_temp = [0] * arr_size
        timestamps_temp = [0] * arr_size
        print("sent max sample")
        if extra_counter == 10:
            exit()

        

    
client.loop_forever()
