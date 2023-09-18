import time
import paho.mqtt.client as mqtt
import  util
import sensor_api as sapi

#server="130.225.57.224" #mqtt broker hosted at AAU


# The callback for when the client receives a CONNACK response from the server.


client = mqtt.Client()
client.on_connect = util.on_connect
client.on_message = util.on_message





client.connect(util.server,1883,60)
userid=101 #NOTE should be replaced with the ID of the group

######################### Logic for furter programming #######################

# sample, timestamps = Get_samples()
# Logic for what to do....
# Connect via nb-iot and send message - client-side logic
# Prepare messages and input into ["topic", "payload", "timestamps"]
# Message is sent via mqtt to the server


#example of getting max sample observed every 10 seconds

# running = 1
# last_send = 0
# samples=[]
# sample_tss=[]
# id=userid3
# while(running):
#     time.sleep(1)
#     sensor_type="light"
#     sample,sample_ts = get_sample(sensor_type)
#     if sample_ts == -1:
#         continue
#     samples.append(sample)
#     sample_tss.append(sample)
#     if last_send == 10:
#         sample_to_send=max(samples)
#         ts_to_send = samples.index(sample_to_send)
#         content=prepare_payload([sensor_type],[[sample_to_send]],[[ts_to_send]])
#         send_multi_topics(content,id)




################## Get samples ############################
content1={"topic":util.topic+"temp", "payload":[-5,-7,-10], "ts": ["13:01", "14:01", "15:01"]}
#content2={"topic":["temp","light"], "payload":[[5,7,10],[1,4,9,10,8]], "ts": [["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]]}
#content3={"topic":["temp","light"], "payload":[[5,7,10],[-1,-4,-9,-10,-8]], "ts": [["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]]}
#content4={"topic":["temp","light"], "payload":[[-5,-7,-10],[1,4,9,10,8]], "ts": [["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]]}

content1=util.prepare_payload(["temp"],[[-5,-7,-10]],[["13:01", "14:01", "15:01"]])
content2=util.prepare_payload(["temp","light"],[[5,7,10],[1,4,9,10,8]],[["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]])
content3=util.prepare_payload(["temp","light"],[[5,7,10],[-1,-4,-9,-10,-8]],[["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]])
content4=util.prepare_payload(["temp","light"],[[-5,-7,-10],[1,4,9,10,8]],[["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]])
################### Sending - nb-iot connection missing #################################

util.send_topics(content1,userid,client)
time.sleep(1)
util.send_topics(content4,userid,client)
time.sleep(1)
util.send_topics(content2,userid,client)
time.sleep(1)
util.send_topics(content3,userid,client)
time.sleep(1)
output=str(userid)+","+"all"

client.publish(util.topic+"download",output) # identifier
time.sleep(5)
#client.publish(pref.topic+"download",userid1) # identifier


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
