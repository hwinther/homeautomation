#!/usr/bin/python

#Going to just straight up rip this format from django settings ;)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os, logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WEBSERVICE_LISTEN_ADDRESS = '0.0.0.0:8080'

INSTALLED_APPS = ( 'HAWebService',
			'HAJointSpace',
			'HACec',
			'SensorDHT',
			'HAPhilipsHue',
			'HASerialIR',
			'HATestApp',
                  )
				  
LOGLEVEL = logging.INFO

REMOTE_APPS = [
                                { 'Address': ('rpi2.oh.wsh.no', 5111), 'INSTALLED_APPS': ('LEDMatrixCore') },
                        ]

REMOTE_SOCKET_LISTEN_ADDRESS = ('0.0.0.0', 5111)

HA_JOINTSPACE_URI = 'http://192.168.1.9:1925'

from Adafruit_DHT import AM2302, DHT11, DHT22
SENSOR_DHT_SENSOR_TYPE = DHT11
SENSOR_DHT_SENSOR_PIN = 4

HA_PHILIPS_HUE_BRIDGE = '192.168.1.2'

SENSORDHT_PLOTDATA_PATH = '/usr/wsh/plotdata'
