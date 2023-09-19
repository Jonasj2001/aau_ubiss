import requests
import paho.mqtt.client as mqtt
import sys
import util
import os
import time

userid=util.userid
data_to_download="all"

def write_to_file(name, rawdata):
	
    directory=os.getcwd()
    f= open(directory + "/" + name+".csv", 'w')
    data=rawdata.rsplit("\n")
    for line in data:
        f.write(line)
        f.write("\n")

def download(userid):
	server=util.server
	#server= "130.225.57.224" # if background is run on a separate host, then use the host ip of that pc
	#port="9080" # Similarly this is the exposed port for the separate host

	server="172.20.0.21" # IF run locally on the same host via docker
	port="8080" # Similarly if run locally 
	res = requests.get("http://"+server+":"+port+"/"+userid+".csv")
	write_to_file(userid, res.text)




client = mqtt.Client()
client.connect(util.server,1883,60)
client.on_connect = util.on_connect
client.on_message = util.on_message





if len(sys.argv)>1:
	output=str(sys.argv[1])+","+data_to_download
	client.publish(util.topic+"download",output) # identifier
	download(sys.argv[1])
	
else:
	output=str(userid)+","+data_to_download
	client.publish(util.topic+"download",output) # identifier
	time.sleep(2)
	download(userid)
