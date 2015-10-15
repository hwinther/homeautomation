#!/usr/bin/python
from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add
from hasettings import HA_PHILIPS_HUE_BRIDGE
import logging, json

import time, os
from phue import Bridge

class WebService_SetLightState(object):
	@webservice_jsonp
	def GET(self, id, state, SharedQueue, ThreadList):
		_state = state.lower() == 'true'
		logging.info('WebService_SetLightState id ' + id + ' state ' + str(_state))
		SharedQueue.append(SerializableQueueItem(HAPhilipsHue.__name__, CurrentInstance.set_light_state, id, _state))
		time.sleep(0.5) #let the state get updated.. or just set it in cache directly?
		return CurrentInstance.get_json_status() #TODO: return cache + this change?

#class WebService_SetLightState(object):
#	@webservice_jsonp
#	def GET(self, id, state, SharedQueue, ThreadList):
#		_state = state == 'True'
#		logging.info('WebService_SetLightState id ' + id + ' state ' + str(_state))
#		SharedQueue.append(SerializableQueueItem(HAPhilipsHue.__name__, CurrentInstance.set_light_state, id, _state))
#		return '{}' #CurrentInstance.get_json_status() #TODO: return cache + this change?
		
class HAPhilipsHue(HomeAutomationQueueThread):
	webservice_definitions = [
		WebServiceDefinition(
			'/philipshue/setState/([a-zA-Z0-9 ]+)/(\w+)', 'WebService_SetLightState', '/philipshue/setState/', 'wsHueSetState'),
		]

	def __init__(self, name, callback_function, queue, threadlist, bridgeip=None):
		HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)
		
		if bridgeip == None:
			bridgeip = HA_PHILIPS_HUE_BRIDGE
		self.bridgeip = bridgeip
		self.bridge = None
		self.lights = {}
		self.relevant_light_attrs = ('name', 'on', 'saturation', 'hue', 'brightness')
		self.cache = []
		
		global CurrentInstance
		CurrentInstance = self
	
	#def run(self):
	#	super(HAPhilipsHue, self).run()
	
	def get_json_status(self):
		return json.dumps({self.__class__.__name__: { 'lights': self.cache }})
	
	def set_light_state(self, id, state):
		if id in self.lights.keys():
			l = self.lights[id]
			l.on = state
			#update cache value also
			for l in self.cache:
				if l['name'] == id:
					l['on'] = state
		return True
		
	def update_light_cache(self):
		logging.info('updating light status cache')
		self.cache = []
		for key, value in self.lights.iteritems():
			#self.cache[key] = {}
			d = {}
			for attr in self.relevant_light_attrs:
				#self.cache[key][attr] = getattr(value, attr)
				d[attr] = getattr(value, attr)
			self.cache.append(d)
	
	def update_light_instances(self):
		logging.info('updating light instances')
		namesfound = []
		added, removed = 0, 0
		for l in self.bridge.lights:
			if not l.name in namesfound: namesfound.append(l.name)
			if not l.name in self.lights.keys():
				self.lights[l.name]=l
				added+=1
		for name in self.lights.keys():
			if not name in namesfound:
				self.lights.pop(name, None)
				removed+=1
		if added != 0 or removed != 0:
			logging.info('Added ' + str(added) + ' lights and removed ' + str(removed))
	
	def pre_processqueue(self):
		logging.info('Philips Hue module initialized')
		self.bridge = Bridge(self.bridgeip)
		webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
		self.update_light_instances()
		self.timecheck = time.time()
		self.update_light_cache()
		self.cachetime = time.time()
		logging.info('PhilipsHue module ready')
		
		super(HAPhilipsHue, self).pre_processqueue()
	
	def post_processqueue(self):
		if time.time() - self.timecheck > 60:
			self.timecheck = time.time()
			logging.info('30s interval')
			self.update_light_instances()
		
		if time.time() - self.cachetime > 30:
			self.cachetime = time.time()
			self.update_light_cache()

		super(HAPhilipsHue, self).post_processqueue()

	def get_class_name(self):
		return self.__class__.__name__
