# Introduction

Micropython program used to monitor ERDF Linky teleinfo and send some values in MQTT.

# Hardware

It is used on a Nodemcu (ESP 8266), with a micropython firmware. In addition a PITInfo v1.2 (https://hallard.me/pitinfov12-light/) is used for teleinfo.

# Setup

The main.py file and umqttsimple.py (https://github.com/micropython/micropython-lib/tree/master/umqtt.simple) has to be uploaded on the ESP 8266. For example if [webrep](https://github.com/micropython/webrepl) is setup:

```bash
$ webrepl_cli.py main.py $IP_ESP:main.py
$ webrepl_cli.py umqttsimple.py $IP_ESP:umqttsimple.py
```

## Configuration

A configuration file (wifi.txt) is needed, with a first line corresponding to the SSID and the second line to the password of the Wi-Fi network.

A second one (mqtt.txt) it not needed, but program is useless if this file is not present. It allows to configure the MQTT server. The first line is the server address, the second the user, the third the password, and the fourth the root path for the MQTT topic.

A last configuration called debug.txt allows the program to send some debug messages in TCP. It contains only one line : `dst:port`.

# Metrics

Metrics sent in MQTT:
- /linky/power
- /linky/instant
- /linky/base

# Webrepl

It is possible to interrupt the main.py program by connecting to webrepl and then hitting CTRL-C. It interrupts the python code and gives you a python shell.
