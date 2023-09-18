import paho.mqtt.client as mqtt
import pymongo
import os
import util
from datetime import datetime

# root is username, example is password and ip is the docker container's ip
connection = pymongo.MongoClient("mongodb://root:example@172.20.0.19")
# ip of mqtt_mongo_1


#connection = pymongo.MongoClient("mongodb://root:example@130.225.57.224/")

connection.server_info()
# verify connection client.server_info()
#connection.list_database_names()
#print("client")
#server="127.0.0.1"




# The callback for when the client receives a CONNACK response from the server.

def database_generic():

    return


def database_add(topic, payload, sample_timestamps, received_timestamps,userid):
    db = connection["ubiss"]# - create db we should use "test"
    database = db[topic]# - document, we should use [test,light,etc.]
    db_data = []
    for i in range(len(payload)):
        index = {"user": userid, "sensor_value": payload[i], "sample_timestamp":sample_timestamps[i], "received_timestamp":received_timestamps[i]}
        db_data.append(index)
    #print(db_data)
    x = database.insert_many(db_data)# - we insert the data 
    return

#sensors = ["temp", "light"]

def write_to_file(name, data):
    directory=os.getcwd()
    f= open(directory + "/files/" + name+".csv", 'w')
    for line in data:
        f.write(line)
        f.write("\n")
    
def database_export(userid, topic_type):
    print("exporting data for user", userid)
    mydb = connection[str(util.topic[:-1])]
    collections = mydb.list_collection_names()

    if topic_type !="all":
        print("only",topic_type,"is exported here")
        mycollection = mydb[topic_type]
        for post in mycollection.find():
            print(post)
        export_set = []
        for post in mycollection.find():
            if str(post['user']) == str(userid):
                #print("found one")
                #index = str({"userid": post['user'], str(sensortype):post['sensor_value'], 'sample timestamp':post['sample_timestamp'], "received timestamp":post["received_timestamp"]})
                index = "userid, " + str(post['user']) + ', ' + str(topic_type) + ', '
                + str(post['sensor_value']) + ', ' + 'sample_timestamp, ' + str(post['sample_timestamp'])
                + ', ' + "received timestamp, " + str(post["received_timestamp"])
                export_set.append(index)
        write_to_file(userid,export_set)
    else:

        export_set = []
        for ttype in collections:
            mycollection = mydb[ttype]
            for post in mycollection.find():
                if str(post['user']) == str(userid):
                    #print("found one")
                    #index = str({"userid": post['user'], str(s):post['sensor_value'], 'sample_timestamp':post['sample_timestamp'], "received timestamp":post["received_timestamp"]})
                    index = "userid, " + str(post['user']) + ', '  + str(ttype) + ', ' + str(post['sensor_value']) + ', ' + 'sample_timestamp, ' + str(post['sample_timestamp']) + ', ' + "received timestamp, " + str(post["received_timestamp"])
                    export_set.append(index)
        write_to_file(userid,export_set)
    return


def find_generic_topics(payload):
    topics = []
    payloads = []
    payloads_all=[]
    ts = []
    timestamps_all = []
    for index in payload:
          flag = True
          try:
              # try converting to integer
              float(index)
          except ValueError:
              flag = False
          if flag:
              payloads.append(str(index))
              # we have a sample, so we append it to the last topics
          else:
            # not a sample so we consider is a topic
            if ":" in index:
                ts.append(index)
            else:
                if index != "ts":
                    topics.append(index)
                    payloads_all.append(payloads)
                    timestamps_all.append(ts)
                    payloads=[]
                    ts = []
    payloads_all.pop(0)
    payloads_all.append(payloads)
    timestamps_all.append(ts)
    timestamps_all.pop(0)

    return topics, payloads_all, timestamps_all



def find_topics(payload, possible_topics):
    topics = []
    payloads_all=[]
    timestamps_all = []
    payloads=[]
    timestamps=[]
    timestamps_now=0
    for index in payload:
        if index in possible_topics:
            #topics.append(index.split("/")[1])
            topics.append(index)
            payloads_all.append(payloads)
            timestamps_all.append(timestamps)
            payloads=[]
            timestamps = []
            timestamps_now = 0
            continue
        elif index == "ts":
            timestamps_now = 1
            continue
        if timestamps_now==0:
            payloads.append(index)
        elif timestamps_now == 1:
            timestamps.append(index)
    payloads_all.append(payloads)
    payloads_all.pop(0)
    timestamps_all.append(timestamps)
    timestamps_all.pop(0)
    return topics, payloads_all, timestamps_all


#possible_topics = ['test/temp', 'test/light', 'test/humidity', 'test/multiple']
#dir_name="test/"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(util.topic+"#")
# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    print("on_message")
    #print(msg.topic+" "+str(msg.payload))
    now = datetime.now()
    received_timestamp = now.strftime("%d/%H:%M:%S")
    #print(received_timestamp)
    payload = msg.payload.decode('UTF-8').split(",")
    userid = payload[0]
    payload.pop(0)

    if str(msg.topic)==util.topic+'download':
        sensor_type=payload[0]
        database_export(userid,sensor_type)
    elif msg.topic == util.topic+"multiple":
        topics, payloads, sample_timestamps= find_generic_topics(payload)

        for i in range(len(topics)):
            received_timestamps = [received_timestamp]*len(payloads[i])
            if len(sample_timestamps[i])==1:
                corrected_ts=[sample_timestamps[i][0]] * len(payloads[i])
                database_add(topics[i], payloads[i],corrected_ts, received_timestamps ,userid)
                #print(corrected_ts)

            else:
                database_add(topics[i], payloads[i],sample_timestamps[i], received_timestamps ,userid)
            

    else:
        #topic, payloads, timestamps = find_topics(payload,pref.possible_topics)
        topics, payloads, sample_timestamps= find_generic_topics(payload)

        topic=topics[0]
        payloads=payloads[0]
        sample_timestamps=sample_timestamps[0]
        received_timestamps = [received_timestamp]*len(sample_timestamps)

        database_add(topic, payloads, sample_timestamps, received_timestamps ,userid)

client = mqtt.Client(client_id="all_suscriber")
client.on_connect = on_connect
client.on_message = on_message


#client.connect("127.0.0.1",1883,60)
client.connect("172.20.0.22",1883,60)


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
