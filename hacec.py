#!/usr/bin/python
from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add
import logging, json

import time, os

class WebService_CecPowerOn(object):
	@webservice_jsonp
	def GET(self, id, SharedQueue, ThreadList):
		_id = 0
		try:
			_id = int(id)
		except ValueError:
			pass
		if 1:
			logging.info('Cec power on: ' + id)
			SharedQueue.append(SerializableQueueItem(HACec.__name__, CurrentInstance.cec_client_power_on, _id)) #:\
		return CurrentInstance.get_json_status()

class WebService_CecStandby(object):
	@webservice_jsonp
	def GET(self, id, SharedQueue, ThreadList):
		_id = 0
		try:
			_id = int(id)
		except ValueError:
			pass
		if 1:
			logging.info('Cec power on: ' + id)
			SharedQueue.append(SerializableQueueItem(HACec.__name__, CurrentInstance.cec_client_standby, _id))
		return CurrentInstance.get_json_status()

class HACec(HomeAutomationQueueThread):
	webservice_definitions = [
		WebServiceDefinition(
			'/cec/power_on/(\d+)', 'WebService_CecPowerOn', '/cec/power_on/', 'wsCecPowerOn'),
		WebServiceDefinition(
			'/cec/standby/(\d+)', 'WebService_CecStandby', '/cec/standby/', 'wsCecStandby'),
		]

	def __init__(self, name, callback_function, queue, threadlist):
		HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)
		
		self.devices = []
		
		global CurrentInstance
		CurrentInstance = self
	
	def get_json_status(self):
		cecdevices = []
		for x in self.devices:
			powerstatus='Unknown'
			try:
				powerstatus = self.devices[x].is_on()
			except:
				pass
			cecdevices.append( {'Name':self.devices[x].osd_string, 'PowerStatus':powerstatus} )
		return json.dumps({self.__class__.__name__: { 'cecdevices': cecdevices } })
		
	def pre_processqueue(self):
		logging.info('CEC module initialized')
		webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
		self.updatedevices()
		self.timecheck = time.time()
		super(HACec, self).pre_processqueue()
	
	def post_processqueue(self):
		if time.time() - self.timecheck > 30:
			self.timecheck = time.time()
			logging.debug('30s interval')
			self.updatedevices()
		super(HACec, self).post_processqueue()
	
	def cec_client_power_on(self, id):
		logging.debug('Power on: ' + str(id))
		cmd='(echo on ' + str(id) + '; echo q) | cec-client -d 7 -s'
		os.system(cmd)
	
	def cec_client_standby(self, id):
		logging.debug('Standby: ' + str(id))
		os.system('(echo standby ' + str(id) + '; echo q) | cec-client -d 7 -s')
		
	def cec_client_osd(self, txt):
		rng = range(ord('A'), ord('z')) #only allow a-z and space
		rng.append(ord(' '))
		txt = ''.join([i for i in txt if ord(i) in rng])
		logging.debug('OSD text: ' + txt)
		os.system('(echo osd 0 ' + txt + '; echo q) | cec-client -d 7 -s')

	def updatedevices(self):
		pass
		#logging.debug('Updating device list')
		#import cec
		#cec.init()
		#self.devices = cec.list_devices()
		#del(cec)
		#d[0].osd_string
		
	def get_class_name(self):
		return self.__class__.__name__
