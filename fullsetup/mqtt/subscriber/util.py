userid="000"

sensors = ["temp", "light"]
topic = "ubiss/"
#server="130.225.57.224"
server ="172.20.0.22"
fileserver="172.20.0.21"

#possible_topics = []
# for s in sensors:
#     possible_topics.append(s)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def serialize(payload_list,timestamps,topic):
    string_out=str(topic)
    print(payload_list)
    for entry in payload_list:
        string_out = string_out +"," + str(entry)
    string_out+= ',ts'
    for entry in timestamps:
        string_out = string_out +"," + str(entry)
    return string_out


def send_topics(topic_payload,userid,client):
    output = str(userid)
    if len(topic_payload['topic'])== 1:
        full_topic= topic+topic_payload['topic'][0]
    else:
        full_topic=topic+"multiple"

    for i in range(len(topic_payload["topic"])):
        payload= topic_payload['payload'][i]
        timestamp = topic_payload['ts'][i]

        serialized_input = serialize(payload,timestamp,topic_payload['topic'][i])
        output = output + "," + serialized_input
    print(output)
    print(full_topic)
         
    client.publish(full_topic, output)

    return

# def send_topic(topic_payload,userid, client):
#     output = str(userid)
#     full_topic= topic_payload['topic']

#     payload= topic_payload['payload']
#     timestamp = topic_payload['ts']

#     serialized_input = serialize(payload,timestamp,topic_payload['topic'])
#     output = output + "," + serialized_input
#     print(output)
         
#     client.publish(full_topic, output)

#     return


def prepare_payload(sensors, data, timestamps):
    if len(sensors)==1:
        payload = {"topic":[], "payload":[], "ts":[]}
        for s in sensors:
            payload["topic"].append(s)
        for d in data:
            payload["payload"].append(d)
        for t in timestamps:
            payload["ts"].append(t)
        return payload


    elif len(sensors)!= len(data) and len(sensors)!=len(timestamps):
        print("Must have equal set length of sensors, payload and timestamps")
        return -1
    payload = {"topic":[], "payload":[], "ts":[]}
    for s in sensors:
        payload["topic"].append(s)
    for d in data:
        payload["payload"].append(d)
    for t in timestamps:
        payload["ts"].append(t)
    return payload
    