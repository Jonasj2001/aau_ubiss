import time
from aau_ubiss import aau_ubiss

# Insert server IP and your Group Name
SERVER = "192.168.2.8"
GROUP_ID = "ubiss"



if __name__ == "__main__":
    ubiss = aau_ubiss(SERVER, GROUP_ID)

    ARR_SIZE = 6
    SENSOR = "light"
    ITERATIONS = 10

    data = [0] * ARR_SIZE
    timestamps = [0] * ARR_SIZE

    for _ in range(ITERATIONS):
        for idx in range(ARR_SIZE):
            sample, ts = ubiss.light()
            data[idx] = sample
            timestamps[idx] = ts
            time.sleep(1)

        max_sample = max(data)
        index = data.index(max_sample)
        sample_ts = timestamps[index]

        payload = ubiss.mqtt.prepare_payload([SENSOR], [[max_sample]], [[sample_ts]])
        ubiss.mqtt.send_topics(payload)
        print("Max sample sent")

    exit()
