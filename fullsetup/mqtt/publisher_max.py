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
userid=101 #NOTE should be replaced with the ID of the group

######################### Logic for furter programming #######################

# sample, timestamps = Get_samples()
# Logic for what to do....
# Connect via nb-iot and send message - client-side logic
# Prepare messages and input into ["topic", "payload", "timestamps"]
# Message is sent via mqtt to the server


#example of getting max sample observed every minute seconds
counter = 0
arr_size = 6
sensor = "light"
userid=102
extra_counter=0
while(1):
    data = [0] * arr_size
    timestamps = [0] * arr_size
    time.sleep(10)
    sample,ts  = get_sample(sensor)
    data[counter]=int(sample)
    timestamps[counter]=str(ts)
    counter+=1

    if counter == arr_size:
        extra_counter+=1
        counter = 0
        max_sample=max(data)
        index = data.index(max_sample)
        
        sample_ts = [timestamps[index]]
        max_sample = [str(max_sample)]
        data=util.prepare_payload([sensor],[max_sample],[sample_ts])
        util.send_topics(data,userid,client)
        data = [0] * arr_size
        timestamps = [0] * arr_size
        print("sent max sample")
        if extra_counter == 10:
            exit()

        

    


client.loop_forever()
