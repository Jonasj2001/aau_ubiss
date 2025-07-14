#%%
import time
from typing import Literal
import serial

class AtMsg:
    """Data class to keep track of entries in AT return statements"""
    def __init__(self, msg: bytes | str):
        if isinstance(msg, bytes):
            msg = msg.decode()
        self.echo = ""
        self.success = ""
        self.response = None
        self._split_msg(msg)

    def _split_msg(self, msg):
        """Split AT command into Echo, msg and success parts."""
        if '\r\r\n' in msg:
            self.echo, msg = msg.split("\r\r\n")
        if "\r\n\r\n" in msg:
            tmp = msg.split("\r\n\r\n")
            if len(tmp) > 1:
                self.response = tmp[:-1]
            msg = tmp[-1]
        if "\r\n" in msg:
            success = msg.split("\r\n")[0]
            self.success = True if success == "OK" else False

    def __str__(self) -> str:
        msg = f"Echo:    {self.echo}\n"\
              f"Output:  {self.response}\n"\
              f"Success: {self.success}"
        return msg

    def __repr__(self) -> str:
        response_sec = ""
        if self.response is not None:
            for entry in self.response:
                response_sec += entry + ";"
        msg = f"{self.echo}; {response_sec} {self.success}"
        return msg

class Sim7020x:
    """SIM7020X API Class"""
    def __init__(self, dev: str, baud = 115200):
        self.ser = serial.Serial(dev, baud)
        """Serial interface for SIM7020x"""
        self.ser.timeout = 0.2 # 200ms timeout
        self._ts_last_cmd = time.monotonic()
        self._cmd_delay = 0.1 # 100ms between commands
        self._mqtt_id = None
        self._mqtt_buffer = 0
        self.hex_mode(False)
        try:
            if self.get_mqtt_connection():
                self.mqtt_discon()
        except IOError:
            pass

    @property
    def cmd_delay(self):
        """Set minimum delay between commands."""
        return self._cmd_delay

    @cmd_delay.setter
    def cmd_delay(self, delay: float):
        self._cmd_delay = delay

    @staticmethod
    def _evaluate_reponse(response: AtMsg,
                          target_response: str):
        """Compare if the responses are correct by looking for the
        target_response as a substring in the reponse.
        """
        if response.response is None:
            return False
        elif target_response in response.response:
            return True
        else:
            return False


    def _send_at_command(
            self,
            at_cmd: str,
            timeout:float = 3):
        """ Send a AT command to the modem

        Parameters
        -----
        at_cmd : str
            AT CMD for the modem
        timeout : float
            Timeout in s
        """
        # Wait for minimum time between commands.
        time_now = time.monotonic()
        if time_now - self._ts_last_cmd < self.cmd_delay:
            sleep_time = (self._ts_last_cmd+self.cmd_delay) - time_now
            time.sleep(sleep_time)

        success: bool = False
        self.ser.read_all() # Empty buffer
        self.ser.write(at_cmd.encode() + b'\r\n')

        # Check for OK.
        reply = b""
        starttime = time.monotonic()

        while time.monotonic() - starttime < timeout:
            reply += self.ser.read(1)
            if reply.endswith(b'OK\r\n'):
                success = True
                break
            elif reply.endswith(b'ERROR\r\n'):
                break

        if success is False:
            timeout_s = False
            if time.monotonic() - starttime > timeout:
                timeout_s = True
            raise IOError(f"Error sending command: {at_cmd}\nResponse: {reply}"\
                          f"\nTimeout {timeout_s}")

        self._ts_last_cmd = time.monotonic()
        reply = AtMsg(reply)
        return reply


    # ----- Generic -----
    def enable_rf(self):
        """Enable rf AT+CFUN=1"""
        reply = self._send_at_command("AT+CFUN=1")
        return reply

    def disable_rf(self):
        """Disable rf AT+CFUN=0"""
        reply = self._send_at_command("AT+CFUN=0", 10)
        return reply

    def set_cops_auto(self):
        """Make modem autoconnect to operator"""
        reply = self._send_at_command(
            "AT+COPS=0"
        )
        return reply

    def set_cops_short(self, shortid: int, mode: int | None = None):
        """Set operator"""
        msg = f"AT+COPS=1,2,\"{shortid}\""
        if mode is not None:
            msg += f",{mode}"
        reply = self._send_at_command(msg)
        return reply

    def get_cops(self):
        """Get operator information"""
        reply = self._send_at_command("AT+COPS?")
        return reply

    def signal_quality(self):
        """Get signal quality"""
        reply = self._send_at_command("AT+CSQ")
        return reply

    def network_registration_status(self):
        """Get network registration status AT+CGREG?"""
        reply = self._send_at_command("AT+CGREG?")
        return reply

    def get_pdp_context(self):
        """Get PDP Context"""
        reply = self._send_at_command("AT+CGCONTRDP")
        return reply

    def connected_operator(self) -> bool:
        """Return True if the modem has connected to an operator"""
        status = self.get_cops()
        if status.response is None:
            return False

        return True

    def connected_network(self) -> bool:
        """Return True if the modem has established an PDP connection"""
        status = self.get_pdp_context()
        if status.response is None:
            return False

        return True


    _pdp_mode = Literal["IP", "IPV6", "IPV4V6", "Non-IP"]
    def set_default_psd(
        self,
        mode: _pdp_mode,
        apn: str,
        username: str = "",
        password: str = ""):
        """Set default PSD, used for creating a PD
        
        Parameters
        -----
        mode : _pdp_mode
            Set the PDP (Packet Data Protocol type) as either
            "IP", "IPV6", "IPV4V6" or Non-IP
        apn : str
            Access point name of the provider.
        username : str
            Username for connection to service provider
        password : str
            Password for connection to service provider 
        """
        suffix: str = ""
        if username != "":
            suffix += f",\"{username}\""
        if password != "":
            suffix += f",\"{password}\""

        reply = self._send_at_command(
            f"AT*MCGDEFCONT=\"{mode}\",\"{apn}\"{suffix}"
        )
        return reply

    def hex_mode(self, state: bool):
        """Send message as HEX or raw"""
        reply = self._send_at_command(f"AT+CREVHEX={int(state)}")
        return reply

    # ----- MQTT -----

    def mqtt_new(
            self,
            ip: str,
            port: int,
            timeout: int = 10000,
            buffer_size: int = 512):
        """Establish a MQTT connection to a server
        
        Parameters
        -----
        ip : str
            Server IP
        port : int
            Server port
        timeout : int
            Command timeout in ms
        buffer_size : int
            Buffer size in bytes
        """
        reply = self._send_at_command(
            f"AT+CMQNEW=\"{ip}\",\"{port}\",{timeout},{buffer_size}",
            10
        )

        # Should return ID / Save ID
        self.get_mqtt_connection()
        self._mqtt_buffer = buffer_size
        return reply

    def get_mqtt_connection(self) -> bool:
        """Check if a MQTT server connection is established"""
        reply = self._send_at_command("AT+CMQNEW?", 1)
        connection = reply.response[0].split(",")
        if connection[2] == "null":
            return False
        else:
            self._mqtt_id = int(connection[0][-1])
            return True



    _mqtt_version = Literal["MQTT 3.1", "MQTT 3.1.1"]
    def mqtt_connection(
            self,
            version: _mqtt_version,
            client_id: str,
            keep_alive_interval: int,
            cleansession: bool = False,
            username: str = "",
            password: str = ""):
        """Establish a session
        
        Parameters
        -----
        version : str
            MQTT Version [MQTT 3.1, MQTT 3.1.1]
        keep_alive_interval : int
            Keep alive interval in seconds
        """
        ver = 3 if version=="MQTT 3.1" else 4
        c_val = 1 if cleansession is True else 0

        suffix: str = ""
        if username != "":
            suffix += f",\"{username}\""
        if password != "":
            suffix += f",\"{password}\""

        reply = self._send_at_command(
            f"AT+CMQCON={self._mqtt_id},{ver},\"{client_id}\","\
            f"{keep_alive_interval},{c_val},0{suffix}"
        )
        return reply


    def mqtt_discon(self):
        """Terminate MQTT Connection"""
        reply = self._send_at_command(
            f"AT+CMQDISCON={self._mqtt_id}"
        )
        return reply

    def mqtt_publish(
            self,
            topic: str,
            message: str,
            qos: int = 2):
        """Publish a MQTT message to the server

        Parameters
        -----
        topic : str
            MQTT Topic to publish the message under
        message : str
            Message to publish
        qos : int
            MQTT QoS, 0: At most once\n
            1: At least once\n 2: Exactly once
        """
        message = message.replace("\n", "").replace("\r","") # Remove CRLF
        if len(message) > self._mqtt_buffer:
            raise ValueError(f"Message is {len(message)} characters "\
                             f"And most not exceed {self._mqtt_buffer}")
        retained = 0
        dup = 0
        reply = self._send_at_command(
            f"AT+CMQPUB={self._mqtt_id},\"{topic}\",{qos},{retained},"\
            f"{dup},{len(message)},\"{message}\""
        )
        return reply
