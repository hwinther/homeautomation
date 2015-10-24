#!/usr/bin/python
from habase import HomeAutomationThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add
from hasettings import SENSOR_DHT_SENSOR_TYPE, SENSOR_DHT_SENSOR_PIN, SENSORDHT_PLOTDATA_PATH
import logging, json, os

import Adafruit_DHT, time

class WebService_SensorList(object):
    @webservice_jsonp
    def GET(self, SharedQueue, ThreadList):
        logging.info('WebService_SensorList listing available sensors')
        return CurrentInstance.get_json_status()

class SensorDHT(HomeAutomationThread):
    webservice_definitions = [
		WebServiceDefinition(
			'/sensor/list', 'WebService_SensorList', '/sensor/list', 'wsSensorList'),
		#WebServiceDefinitions.append(WebServiceDefinition(
		#	'/sensor/(\d+)', 'WebService_SensorState_JSONP', '/sensor', 'wsSensorState'),
	]

    def __init__(self, name, callback_function):
        HomeAutomationThread.__init__(self, name, callback_function)

        self.id = 1
        self.sensor = SENSOR_DHT_SENSOR_TYPE
        self.pin = SENSOR_DHT_SENSOR_PIN
        self.sensors = [self]
        self.humidity = 0.0
        self.temperature = 0.0

        global CurrentInstance
        CurrentInstance = self

    def run(self):
        logging.info('DHT module initialized')
        webservice_state_instances_add(self.get_class_name(), self.get_json_status)
        timecheck = time.time()
        while not self.stop_event.is_set():
            time.sleep(1)
            humidity_previous = self.humidity
            temperature_previous = self.temperature
            self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            if humidity_previous != self.humidity or temperature_previous != self.temperature:
                # values have changed, add to plot data
                open(SENSORDHT_PLOTDATA_PATH + os.sep + time.strftime('%d.%m.%y.plotdata'), 'a').write('%.02f\t%.02f\n' %(self.temperature, self.humidity) )
            #after 15 tries/30 seconds, None, None
            if time.time() - timecheck > 60:
                timecheck = time.time()
                logging.debug('60 interval - temperature: ' + str(self.temperature) + ' Humidity: ' + str(self.humidity))
            time.sleep(1)

    def get_json_status(self):
        a = []
        for s in self.sensors:
            a.append( {'Id':s.id, 'Type':s.get_class_name(), 'Values':{'Temperature':s.temperature, 'Humidity':s.humidity} } )
        return json.dumps({self.get_class_name(): a})

    def get_class_name(self):
        return self.__class__.__name__
