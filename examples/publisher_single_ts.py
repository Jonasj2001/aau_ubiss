import time
from aau_ubiss import aau_ubiss

# Insert server IP and your Group Name
SERVER = "130.225.37.241"
GROUP_ID = "group"


if __name__ == "__main__":
    ubiss = aau_ubiss(SERVER, GROUP_ID)

    ARR_SIZE = 6
    ITERATIONS = 10
    SENSOR1 = "light"
    SENSOR2 = "temp"

    data_light = [0] * ARR_SIZE
    timestamp_light = [0] * ARR_SIZE

    data_temp = [0] * ARR_SIZE
    timestamp_temp = [0] * ARR_SIZE

    for _ in range(ITERATIONS):
        for idx in range(ARR_SIZE):
            sample, ts = ubiss.light()
            data_light[idx] = sample
            timestamp_light[idx] = ts

            sample, ts = ubiss.temperature()
            data_temp[idx] = sample
            timestamp_temp[idx] = ts
            time.sleep(1)

        payload = ubiss.mqtt.prepare_payload(
            [SENSOR1, SENSOR2],
            [data_light, data_temp],
            [[timestamp_light[0]], [timestamp_temp]])
        
        ubiss.mqtt.send_topics(payload)

    exit()