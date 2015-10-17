#!/usr/bin/python
from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add
#from hasettings import SERIALIR_PORT
import logging, json

import time, os, serial

class WebService_SerialIRSendByte(object):
	@webservice_jsonp
	def GET(self, byte, SharedQueue, ThreadList):
		logging.info('WebService_SerialIRSendByte: ' + byte)
		SharedQueue.append(SerializableQueueItem(HASerialIR.__name__, CurrentInstance.write_byte, byte))
		return CurrentInstance.get_json_status()

class HASerialIR(HomeAutomationQueueThread):
	webservice_definitions = [
		WebServiceDefinition(
			'/serialir/byte/(\d+)', 'WebService_SerialIRSendByte', '/serialir/byte/', 'wsSerialIRSendByte'),
		]

	def __init__(self, name, callback_function, queue, threadlist, baseurl=None):
		HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)
		
		#if baseurl == None:
		#	baseurl = HA_JOINTSPACE_URI
		#self.baseurl = baseurl
		
		self.Serial = serial.Serial('/dev/ttyACM1', 9600, timeout=1)
		
		global CurrentInstance
		CurrentInstance = self
	
	#def run(self):
	#	super(HASerialIR, self).run()
	
	#def get_json_status(self):
	#	return super(HASerialIR, self).get_json_status()
	
	def pre_processqueue(self):
		logging.info('Serial IR module initialized: ' + self.Serial.readline() )
		webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
		self.timecheck = time.time()
		super(HASerialIR, self).pre_processqueue()
	
	def post_processqueue(self):
		if time.time() - self.timecheck > 30:
			self.timecheck = time.time()
			logging.debug('30s interval')
		super(HASerialIR, self).post_processqueue()

	def get_class_name(self):
		return self.__class__.__name__

	#generic methods
	def write_byte(self, byte):
		b = int(byte)
		logging.info('Writing byte: ' + `chr(b)`)
		self.Serial.write(chr(b))
		logging.info('Read: ' + self.Serial.readline())
		return True

	'''
      1 = 100C = power button
      2 = 1086 = audio in
      3 = 1039 = coax
      4 = 1038 = aux
      5 = 106C = optical
      6 = 1069 = BT
      7 = 1087 = arc
      8 = 107E = usb
      
      9 = 1016 = bass up
     10 = 1017 = bass down
    '''
