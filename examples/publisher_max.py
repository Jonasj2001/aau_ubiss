import time
from aauiot import aau_iot, MqttData

# Insert server IP and your Group Name
SERVER = "130.225.37.241" 
GROUP_ID = "group"



if __name__ == "__main__":
    iot = aau_iot(SERVER, GROUP_ID)
    iot.mqtt_connect("NBIoT")

    ARR_SIZE = 6
    SENSOR = "light"
    ITERATIONS = 10

    data = [0] * ARR_SIZE
    timestamps = [""] * ARR_SIZE

    for _ in range(ITERATIONS):
        for idx in range(ARR_SIZE):
            sample, ts = iot.light()
            data[idx] = sample
            timestamps[idx] = ts
            time.sleep(1)

        max_sample = max(data)
        index = data.index(max_sample)
        sample_ts = timestamps[index]

        msg = MqttData(SENSOR, [max_sample], sample_ts)

        iot.mqtt.send_topics(msg)
        print("Max sample sent")

    time.sleep(3)
    iot.mqtt.discon()
    exit()
