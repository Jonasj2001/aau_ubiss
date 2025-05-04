
#%%
import time
from enum import Enum
from typing import Literal
import requests
import board
from adafruit_bme680 import Adafruit_BME680_I2C as BME680
from adafruit_veml7700 import VEML7700
from adafruit_sgp30 import Adafruit_SGP30 as SGP30
import paho.mqtt.client as mqtt
i2c = board.I2C()
_bme_oversample_t = Literal["ovr_samp_0","ovr_samp_1","ovr_samp_2",
                          "ovr_samp_4","ovr_samp_8","ovr_samp_16"]

class _bme_oversample(Enum):
    ovr_samp_0  = 0
    ovr_samp_1  = 1
    ovr_samp_2  = 2
    ovr_samp_4  = 4
    ovr_samp_8  = 8
    ovr_samp_16 = 16

class _humidity:
    def __init__(self, sensor: BME680):
        self.sensor = sensor

    def __call__(self):
        """Return Humidity in [%]"""
        return self.sensor.humidity

    def set_oversample_rate(self, rate: _bme_oversample_t | _bme_oversample):
        """The oversampling for the humidity sensor"""
        if type(rate) == str:
            rate = _bme_oversample[rate]
        self.sensor.humidity_oversample = rate.value

class _temperature:
    def __init__(self, sensor: BME680):
        self.sensor = sensor

    def __call__(self):
        """Return temperature in [degC]"""
        return self.sensor.temperature
    
    def set_oversample_rate(self, rate: _bme_oversample_t | _bme_oversample):
        """The oversampling for the temperature sensor"""
        if type(rate) == str:
            rate = _bme_oversample[rate]
        self.sensor.temperature_oversample = rate.value

class _pressure:
    def __init__(self, sensor: BME680):
        self.sensor = sensor

    def __call__(self):
        """Return pressure in [hPa]"""
        return self.sensor.pressure

    def set_oversample_rate(self, rate: _bme_oversample_t | _bme_oversample):
        """The oversampling for the pressure sensor"""
        if type(rate) == str:
            rate = _bme_oversample[rate]
        self.sensor.pressure_oversample = rate.value

class _light:
    """Class for controlling Light parameters of the VEML7700 sensor"""
    class int_time_val(Enum):
        ALS_25MS = VEML7700.ALS_25MS
        ALS_50MS = VEML7700.ALS_50MS
        ALS_100MS = VEML7700.ALS_100MS
        ALS_200MS = VEML7700.ALS_200MS
        ALS_400MS = VEML7700.ALS_400MS
        ALS_800MS = VEML7700.ALS_800MS

    class gain_val(Enum):
        ALS_GAIN_1 = VEML7700.ALS_GAIN_1
        ALS_GAIN_2 = VEML7700.ALS_GAIN_2
        ALS_GAIN_1_8 = VEML7700.ALS_GAIN_1_8
        ALS_GAIN_1_4 = VEML7700.ALS_GAIN_1_4
    
    def __init__(self, sensor: VEML7700):
        self.sensor = sensor

    def __call__(self):
        """Return light level in [Lux], w. autocalibration """
        return self.sensor.autolux

    def get_light_raw(self):
        """Return light level in [Lux] witout autocalibration"""
        return self.sensor.lux
    
    @property
    def integration_time(self):
        return self.sensor.integration_time_value()
    
    @integration_time.setter
    def integration_time(self, int_time: int_time_val):
        if int_time not in self.int_time_val:
            raise ValueError("Invalid value must be in int_time")
        self.sensor.light_integration_time = int_time.value
    
    @property
    def gain(self):
        """Get current gain value"""
        return self.sensor.gain_value()
    
    @gain.setter
    def gain(self, gain: gain_val):
        if gain not in self.gain_val:
             raise ValueError("Invalid value must be in gain_val")
        self.sensor.light_gain = gain.value

class _gas:
    def __init__(self, sensor: SGP30):
        self.sensor = sensor

    def __call__(self):
        """Return TVOC and eCO2 in [ppb] and [ppm]
        
        Returns
        ----
        list : [TVOC, eCO2]
        """
        return [self.sensor.TVOC, self.sensor.eCO2]
    
    def get_baseline(self):
        """Return Baseline values for TVOC and eCO2 in [ppb] and [ppm]
        
        Returns
        -----
        list : [TVOC_base, eCO2_base]
        """
        return [self.sensor.baseline_TVOC, self.sensor.baseline_eCO2]

class _messaging:
    def __init__(self, userid):
        self.userid = userid

    @staticmethod
    def _serialize(payload_list, timestamps, topic):
        string_out=str(topic)
        print(payload_list)
        for entry in payload_list:
            string_out = string_out +"," + str(entry)
        string_out+= ',ts'
        for entry in timestamps:
            string_out = string_out +"," + str(entry)
        return string_out
    
    @staticmethod
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
        
    def send_topics(self, topic_payload) -> None:
        raise NotImplementedError()

class messaging_ip(_messaging):
    @staticmethod
    def _on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

    @staticmethod
    def _on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))

    def __init__(self, server: str, userid="group", topic="ubiss/"):
        super().__init__(userid)
        self.topic = topic
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(server)
    
    def send_topics(self, topic_payload) -> None:
        output = str(self.userid)
        if len(topic_payload['topic'])== 1:
            full_topic= self.topic+topic_payload['topic'][0]
        else:
            full_topic=self.topic+"multiple"

        for i in range(len(topic_payload["topic"])):
            payload= topic_payload['payload'][i]
            timestamp = topic_payload['ts'][i]

            serialized_input = self._serialize(payload,timestamp,topic_payload['topic'][i])
            output = output + "," + serialized_input
            
        self.client.publish(full_topic, output)


class messaging_nbiot(_messaging):
    def __init__(self, userid):
        super().__init__(userid)

class aau_ubiss:
    """AAU Ubiss, board support crate"""
    def __init__(self, server="172.20.0.22", userid="group"):
        bme = BME680(i2c, refresh_rate=100)
        bme.set_gas_heater(None, None)
        veml7700 = VEML7700(i2c)
        sgp30 = SGP30(i2c)

        self.humidity = _humidity(bme)
        self.temperature = _temperature(bme)
        self.pressure = _pressure(bme)
        self.light = _light(veml7700)
        self.gas = _gas(sgp30)
        self.mqtt = messaging_ip(server, userid)
        self._ip = server
        self._uid = userid

    def _fetch_file(self, server, port):
        res = requests.get(
            f"http://{server}:{port}/{self._uid}.csv", timeout=5
            )
        
        with open(f"{self._uid}.csv", "w") as f:
            f.write(res.text)

    def download(self, localhost: bool = False) -> None:
        """Fetch group data from the server"""
        server = self._ip
        port = 9080
        if localhost:
            server = "172.20.0.21"
            port = 8080

        topic = self.mqtt.topic+"download"
        msg = self._uid+",all"
        self.mqtt.client.publish(topic, msg) # Prepare download
        time.sleep(2)
        self._fetch_file(server, port)


        

#%%
if __name__ == "__main__":
    ubiss = aau_ubiss()
    print(ubiss.temperature())
    print(ubiss.pressure())
    print(ubiss.humidity())
