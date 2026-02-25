#!/bin/env python3
import requests
import paho.mqtt.client as mqtt
import sys
import os
import time

mqtt_server = "130.225.37.202"

fileserver = mqtt_server # Use 172.20.0.21 if locally hosted. 
topic = "aauiot/"
userid="group"
data_to_download="all"

def write_to_file(name, rawdata):

    directory=os.getcwd()
    f= open(directory + "/" + name+".csv", 'w')
    data=rawdata.rsplit("\n")
    for line in data:
        f.write(line)
        f.write("\n")

def download(userid):
    port="9080"
    if fileserver == "172.20.0.21":
        port = "8080"
    res = requests.get("http://"+fileserver+":"+port+"/"+userid+".csv")
    print(res.text)
    write_to_file(userid, res.text)




client = mqtt.Client()
client.connect(mqtt_server,1883,60)

if len(sys.argv)>1:
    output=str(sys.argv[1])+","+data_to_download
    client.publish(topic+"download",output) # identifier
    download(sys.argv[1])
	
else:
    output=str(userid)+","+data_to_download
    client.publish(topic+"download",output) # identifier
    time.sleep(2)
    download(userid)
