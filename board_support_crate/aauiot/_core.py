
#%%
import time
from enum import Enum
from typing import Literal
from datetime import datetime
import requests
from pytz import UTC
import board
from adafruit_bme680 import Adafruit_BME680_I2C as BME680
from adafruit_veml7700 import VEML7700
from adafruit_sgp30 import Adafruit_SGP30 as SGP30
import paho.mqtt.client as mqtt
from aauiot._sim7020e import Sim7020x
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

def _get_time():
    """Get current time in UTC"""
    frmt_str = "%H:%M:%S"
    ts = datetime.now(tz=UTC)
    return ts.strftime(frmt_str)

def _time_decorater(func):
    """Decorator to append timestamp to output"""
    def _decorator(*args, **kwargs):
        results = func(*args, **kwargs)
        ts = _get_time()
        return results, ts
    return _decorator

class _humidity:
    def __init__(self, sensor: BME680):
        self.sensor = sensor

    @_time_decorater
    def __call__(self):
        """Return Humidity in [%]"""
        return self.sensor.humidity

    def set_oversample_rate(self, rate: _bme_oversample_t | _bme_oversample):
        """The oversampling for the humidity sensor"""
        if isinstance(rate, str):
            rate = _bme_oversample[rate]
        self.sensor.humidity_oversample = rate.value

class _temperature:
    def __init__(self, sensor: BME680):
        self.sensor = sensor

    @_time_decorater
    def __call__(self):
        """Return temperature in [degC]"""
        return self.sensor.temperature

    def set_oversample_rate(self, rate: _bme_oversample_t | _bme_oversample):
        """The oversampling for the temperature sensor"""
        if isinstance(rate, str):
            rate = _bme_oversample[rate]
        self.sensor.temperature_oversample = rate.value

class _pressure:
    def __init__(self, sensor: BME680):
        self.sensor = sensor

    @_time_decorater
    def __call__(self):
        """Return pressure in [hPa]"""
        return self.sensor.pressure

    def set_oversample_rate(self, rate: _bme_oversample_t | _bme_oversample):
        """The oversampling for the pressure sensor"""
        if isinstance(rate, str):
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

    @_time_decorater
    def __call__(self):
        """Return light level in [Lux], w. autocalibration """
        return self.sensor.autolux

    @_time_decorater
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

    @_time_decorater
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

class MqttData:
    """Data class for parsing Sensor data, to MQTT broker."""
    def __init__(self,
                 identifier: str,
                 values: list | None = None,
                 timestamps: str | list[str] | None = None
                 ):
        self._ident = identifier
        if values is None:
            self.vals = []
        elif isinstance(values, list):
            self.vals = values
        else:
            raise ValueError("Values must be empty or list.")

        if timestamps is None:
            self.ts = []
        elif isinstance(timestamps, str):
            self.ts = [timestamps]
        elif isinstance(timestamps, list):
            if len(timestamps) != len(self.vals):
                raise ValueError(
                    f"Timestamps have incorrect len {len(timestamps)}"\
                    f"\nMust be 0,1 or Same as values.")
            self.ts = timestamps

    def __len__(self):
        return len(self.serialize())

    @property
    def identifier(self):
        return self._ident
    
    def add_measurement(self,
                        val: object,
                        ts: None | str = None) -> int:
        """Add measurement to data object
        
        Params
        -----
        val : object
            Data which can be represented as a string
        ts : None | str
            Timestamp associated with datapoint, if None is giving,
            all points will use the first timestamp.
        
        Returns
        -----
        buffer_remainder : int
            Remaining space, before object is bigger than MQTT buffer.

        Raises
        -----
        ValueError
          If the object has no associated timestamps and None is given.
        ValueError
          If there are more timestamps than samples
        ValueError
          If there are less timestamps than samples but more than one.
        ValueError
          If the Timestamps are not string formatted.
        """
        if ts is None:
            if len(self.ts) == 0:
                raise ValueError("The object need at least one timestamp")
            if len(self.ts) > 1:
                raise ValueError("The number of timestamps must be 1 or "\
                                 "match the number of samples.")
        elif isinstance(ts, str):
            if len(self.ts) == len(self.vals):
                self.ts.append(ts)
            else:
                raise ValueError("The number of timestamps must be 1 or "\
                                 "match the number of samples")
        else:
            raise ValueError("Timestamp must be of type str formatted "\
                             "as \"HH:MM:SS\"")
        self.vals.append(val)
        return 512 - len(self)

    def serialize(self):
        """Serialize object to a ASCII string."""
        output = self._ident
        for val in self.vals:
            output += f",{val:.4g}"
        output += ",ts"
        for ts in self.ts:
            output += f",{ts}"
        return output



class _messaging:
    def __init__(self,
                 server,
                 port:int = 1883,
                 topic: str = "ubiss/",
                 userid: str = "group",
                 keepalive: int = 600):
        self._uid = userid
        self._ip = server
        self._port = port
        self.topic = topic
        self._keepalive = keepalive

    def send_topics(self, data: MqttData) -> None:
        """Send Sensordata, to the MQTT server"""
        raise NotImplementedError()

    def publish(self, topic, payload):
        """Publish a MQTT message to the server"""
        raise NotImplementedError()

class messaging_ip(_messaging):
    @staticmethod
    def _on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

    @staticmethod
    def _on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))

    def __init__(self,
                 server,
                 port: int = 1883,
                 topic: str = "ubiss/",
                 userid: str = "group", 
                 keepalive: int = 600):
        super().__init__(server, port, topic, userid, keepalive)
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(self._ip, self._port, self._keepalive)

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def send_topics(self, data: MqttData) -> None:
        topic = self.topic + data.identifier
        output = self._uid + "," + data.serialize()
        self.client.publish(topic, output)


class messaging_nbiot(_messaging):
    def __init__(self,
                 server,
                 port: int = 1883,
                 topic: str = "ubiss/",
                 userid: str = "group",
                 keepalive: int = 600,
                 device = "/dev/ttyAMA0"):
        super().__init__(server, port, topic, userid, keepalive)
        self.sim = Sim7020x(device)
        self._connect_sim()

    def _connect_sim(self):
        self.sim.disable_rf()
        self.sim.set_cops_short(23802)
        self.sim.set_default_psd("IP", "telenor.iot")
        self.sim.enable_rf()
        while self.sim.connected_network() is False:
            pass
        self.sim.mqtt_new(self._ip, self._port)
        self.sim.mqtt_connection("MQTT 3.1", self._uid, self._keepalive)

    def discon(self):
        """Disconnect from MQTT and disable RF"""
        self.sim.mqtt_discon()
        self.sim.disable_rf()

    def publish(self, topic, payload):
        """Publish MQTT message"""
        self.sim.mqtt_publish(topic, payload)

    def send_topics(self, data: MqttData) -> None:
        topic = self.topic + data.identifier
        output = self._uid + "," + data.serialize()
        self.sim.mqtt_publish(topic, output)






class aau_iot:
    """AAU IoT, board support crate"""
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
        self.mqtt = None
        self._ip = server
        self._uid = userid

    def _fetch_file(self, server, port):
        res = requests.get(
            f"http://{server}:{port}/{self._uid}.csv", timeout=5
            )

        with open(f"{self._uid}.csv", "w") as f:
            f.write(res.text)
    
    _mqtt_mode = Literal["IP", "NBIoT"]
    def mqtt_connect(self,
                     mode: _mqtt_mode = "IP",
                     port: int = 1883,
                     topic: str = "ubiss/"):
        """Setup MQTT Connection over IP or NB-IoT"""
        if mode == "IP":
            self.mqtt = messaging_ip(self._ip, port, topic, self._uid)
        elif mode == "NBIoT":
            self.mqtt = messaging_nbiot(self._ip, port, topic, self._uid)
        else:
            raise ValueError(
                f"Invalid mode: must be in: {aau_iot._mqtt_mode.__args__}")
        
    def download(self, localhost: bool = False) -> None:
        """Fetch group data from the server"""
        server = self._ip
        port = 9080
        if localhost:
            server = "172.20.0.21"
            port = 8080

        if self.mqtt is None:
            raise IOError("MQTT Connection must be established first.")
        
        topic = self.mqtt.topic+"download"
        msg = self._uid+",all"
        self.mqtt.publish(topic, msg) # Prepare download
        time.sleep(2)
        self._fetch_file(server, port)

    @staticmethod
    def get_time():
        """Return current time in HH:MM:SS"""
        return _get_time()


#%%
if __name__ == "__main__":
    ubiss = aau_iot()
    print(ubiss.temperature())
    print(ubiss.pressure())
    print(ubiss.humidity())
