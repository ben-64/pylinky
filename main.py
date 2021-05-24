import sys
import network
import time
import machine
import socket
import uos
from umqttsimple import MQTTClient

# Without that, serial does not work, I don't know why
uos.dupterm(None, 1)

class Linky(object):
    KEYS = [b"PAPP",b"IINST",b"BASE"]
    def __init__(self,debug):
        self.uart = machine.UART(0,1200)
        self.uart.init(1200, bits=7, parity=0, stop=1,rxbuf=200,timeout=100)
        self.debug = debug

    def raw_read(self):
        r = None
        while r is None:
            r = self.uart.read()
        self.debug.print("%r|" % r)
        return r

    def readframe(self):
        """ Read a full Linky Frame """
        stop = False
        while not stop:
            s = self.raw_read()
            # Wait for the beginning of the frame
            while b"\x02" not in s:
                s += self.raw_read()
            s = s[s.find(b"\x02")+1:]

            # Wait for the end of the frame
            while b"\x03" not in s:
                s += self.raw_read()

            end_pos = s.find(b"\x03")

            # All keys need to be in the frame, otherwise we retry
            # I don't know why, but it happens
            for key in Linky.KEYS:
                if not key in s: break
            else:
                stop = True

        return s[:end_pos]

    def parse_frame(self,frame):
        """ Parse a full Linky frame """
        r = {}
        for info in frame.split(b"\r"):
            info = info.lstrip(b"\n").rstrip(b"\n")
            data = info.split(b" ")
            if len(data) == 3 or len(data) == 2:
                if data[0] in Linky.KEYS: 
                    val = str(int(data[1])).encode()
                else:
                    val = data[1]
                r[data[0]] = val # data[2] is checksum
        return r

    def get_data(self):
        frame = self.readframe()
        self.debug.println("\nFrame: %r" % (frame,))
        data = self.parse_frame(frame)
        return data


class Debug(object):
    """ Classe to debug, because it is not easy with micropython """
    def __init__(self,config="debug.txt"):
        self.config = config
        self.load_config()
        if self.enable:
            self.sock  = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.connect()

    def load_config(self):
        try:
            with open(self.config,"r") as f:
                conf = f.readlines()
            self.enable = False
            if len(conf) >= 1:
                dst,port = conf[0].split(":")
                self.srv = (dst,int(port))
                self.enable = True
        except OSError:
            self.enable = False

    def connect(self):
        """ Wait until connect """
        while True:
            try:
                self.sock.connect(self.srv)
                break
            except:
                time.sleep(1)

    def print(self,msg):
        if self.enable:
            self.sock.send(msg)

    def println(self,msg):
        self.print(msg+"\n")

class MQTT(object):
    def __init__(self,config="mqtt.txt"):
        self.user = None
        self.password = None
        self.root = b""
        self.config = config
        self.enable = True
        self.load_config()
        if self.enable:
            self.mqtt = MQTTClient("pylinky",self.server,user=self.user,password=self.password)
            self.mqtt.connect()

    def load_config(self):
        try:
            with open(self.config,"r") as f:
                conf = f.readlines()
            if len(conf) > 0: self.server = conf[0].strip()
            if len(conf) > 1: self.user = conf[1].strip()
            if len(conf) > 2: self.password = conf[2].strip()
            if len(conf) > 3: self.root = conf[3].strip().encode()
        except OSError:
            self.enable = False

    def publish(self,tag,value):
        if self.enable: self.mqtt.publish(self.root+b"/"+tag,value)


def connect_wifi(config):
    with open(config,"r") as f:
        ssid = f.readline().strip()
        passwd = f.readline().strip()
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid,passwd)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())


def main(seconds):
    connect_wifi("wifi.txt")
    debug = Debug("debug.txt")
    mqtt = MQTT("mqtt.txt")

    try:
        linky = Linky(debug)
    except Exception as e:
        debug.println("Unable to create Linky() : %r" % (e,))
        sys.exit(1)
    
    pitinfo_led = machine.Pin(12,machine.Pin.OUT)

    while True:
        pitinfo_led.on()
        try:
            d = linky.get_data()
            #debug.println("%r" % (d,))
            if b"PAPP" in d:  mqtt.publish(b"power", d[b"PAPP"])
            if b"BASE" in d: mqtt.publish(b"base", d[b"BASE"])
            if b"IINST" in d: mqtt.publish(b"instant", d[b"IINST"])
        except Exception as e:
            debug.println("Unable to read on linky : %r" % (e,))
        pitinfo_led.off()
        time.sleep(seconds)

main(10)
