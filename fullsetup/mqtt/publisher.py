import time
import paho.mqtt.client as mqtt
#import defines as pref
import util

#topic = "test"
server="130.225.57.224"
server ="172.20.0.22"

# The callback for when the client receives a CONNACK response from the server.


client = mqtt.Client(client_id="user101")
client.on_connect = util.on_connect
client.on_message = util.on_message

client.connect(server,1883,60)
userid1=101 # These are specified for each device
userid2=202
userid3=303

################## Get samples ############################
content1=util.prepare_payload(["bleh"],[[19,20,20]],[["13:10", "13:20", "13:30"]])

content2=util.prepare_payload(["temp","light"],[[19,20,20],[10,15,15,20,17]], [["13:10", "13:20", "13:30"], ["13:10", "13:15", "13:20", "13:25","13:30"]])


content3=util.prepare_payload(["temp","light"],[[5,7,10],[-1,-4,-9,-10,-8]],[["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]])
content4=util.prepare_payload(["temp","light"],[[-5,-7,-10],[1,4,9,10,8]],[["13:01", "14:01", "15:01"], ["13:31", "14:31", "15:31", "16:31","17:31"]])
################### Sending - nb-iot connection missing #################################

util.send_multi_topics(content1,userid1,client)

time.sleep(1)
util.send_multi_topics(content2,userid2,client)

time.sleep(1)
util.send_multi_topics(content3,userid3,client)
time.sleep(1)
util.send_multi_topics(content4,userid3,client)
time.sleep(1)
output=str(userid3)+","+"all"

client.publish(util.topic+"download",output) # identifier
time.sleep(5)
#client.publish(pref.topic+"download",userid1) # identifier


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
