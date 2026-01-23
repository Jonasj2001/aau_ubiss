import time
from aauiot import aau_iot, MqttData

# Insert server IP and your Group Name
SERVER = "130.225.37.241"
GROUP_ID = "group"


if __name__ == "__main__":
    iot = aau_iot(SERVER, GROUP_ID)
    iot.mqtt_connect("NBIoT")

    ARR_SIZE = 6
    ITERATIONS = 10
    SENSOR1 = "light"
    SENSOR2 = "temp"

    for _ in range(ITERATIONS):
        data_light = MqttData(SENSOR1, timestamps=iot.get_time())
        data_temp = MqttData(SENSOR2, timestamps=iot.get_time())
        for idx in range(ARR_SIZE):
            sample, ts = iot.light()
            data_light.add_measurement(sample)

            sample, ts = iot.temperature()
            data_temp.add_measurement(sample)
            time.sleep(1)

        iot.mqtt.send_topics(data_light)
        iot.mqtt.send_topics(data_temp)

    time.sleep(3)
    iot.mqtt.discon()
    exit()