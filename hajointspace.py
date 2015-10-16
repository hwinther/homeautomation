#!/usr/bin/python
from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add
from hasettings import HA_JOINTSPACE_URI
import logging, json

import time, os, urllib, urllib2

class WebService_HARemoteKey(object):
	@webservice_jsonp
	def GET(self, key, SharedQueue, ThreadList):
		logging.info('WebService_HARemoteKey: ' + key)
		SharedQueue.append(SerializableQueueItem(HAJointSpace.__name__, CurrentInstance.set_input_key, key))
		return CurrentInstance.get_json_status()

class HAJointSpace(HomeAutomationQueueThread):
	webservice_definitions = [
		WebServiceDefinition(
			'/jointspace/remote/(\w+)', 'WebService_HARemoteKey', '/jointspace/remote/', 'wsJSRemoteKey'),
		]

	def __init__(self, name, callback_function, queue, threadlist, baseurl=None):
		HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)
		
		if baseurl == None:
			baseurl = HA_JOINTSPACE_URI
		self.baseurl = baseurl
		
		global CurrentInstance
		CurrentInstance = self
	
	#def run(self):
	#	super(HAJointSpace, self).run()
	
	#def get_json_status(self):
	#	return super(HAJointSpace, self).get_json_status()
	
	def pre_processqueue(self):
		logging.info('JointSpace module initialized')
		webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
		self.timecheck = time.time()
		super(HAJointSpace, self).pre_processqueue()
	
	def post_processqueue(self):
		if time.time() - self.timecheck > 30:
			self.timecheck = time.time()
			logging.debug('30s interval')
		super(HAJointSpace, self).post_processqueue()

	def get_class_name(self):
		return self.__class__.__name__

	#generic methods
	def post_request(self, method_uri, **args):
		url = self.baseurl + method_uri #'/1/input/key'
		data = json.dumps(args)
		req = urllib2.Request(url, data)
		response = urllib2.urlopen(req) #response.headers.type #'text/html'  'application/json'
		content = response.read() #response.getcode() #int
		return response.code == 200 #TODO: throw exception in other cases, and include errormessage from content
	
	def get_request(self, method_uri):
		url = self.baseurl + method_uri
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		content = response.read()
		if response.headers.type == 'application/json':
			content = json.loads(content)
		return response.code == 200, content
		
	def get_request_json(self, method_uri):
		url = self.baseurl + method_uri
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		content = response.read()
		if response.headers.type == 'application/json':
			return json.loads(content) #TODO: we may be getting json even if its not code=200.. then what?
		else:
			return '{}' #empty deserialized json format
	#end generic methods
	
	#Ambilight methods
	def get_ambilight_topology(self):
		'''GET ambilight/topology'''
		return self.get_request_json('/1/ambilight/topology')
	
	def get_ambilight_mode(self):
		'''GET ambilight/mode'''
		return self.get_request_json('/1/ambilight/mode')
	
	def set_ambilight_mode(self, current):
		'''POST ambilight/mode'''
		return self.post_request('/1/ambilight/mode', current=current)
	
	def get_ambilight_measured(self):
		'''GET ambilight/measured'''
		return self.get_request_json('/1/ambilight/measured')
	
	def get_ambilight_processed(self):
		'''GET ambilight/processed'''
		return self.get_request_json('/1/ambilight/processed')
	
	def get_ambilight_cached(self):
		'''GET ambilight/cached'''
		return self.get_request_json('/1/ambilight/cached')
	
	def set_ambilight_cached(self, **kwargs):
		'''POST ambilight/cached
		{
			"r": 100,
			"g": 210,
			"b": 30
		}'''
		return self.post_request('/1/ambilight/cached', **kwargs)
	
	#Audio methods
	def get_audio_volume(self):
		'''GET audio/volume
		returns
		{
			"muted": false,
			"current": 18,
			"min": 0,
			"max": 60
		}'''
		return self.get_request_json('/1/audio/volume')
	
	def set_audio_volume(self, muted, current):
		'''POST audio/volume'''
		return self.post_request('/1/audio/volume', muted=muted, current=current)
	
	#Channel list methods
	def get_channellists(self):
		'''GET channellists'''
		return self.get_request_json('/1/channellists')
		
	def get_channellists_id(self, id):
		'''GET channellists/id'''
		return self.get_request_json('/1/channellists/' + id)

	#Channel methods
	def get_channels(self):
		'''GET channels'''
		return self.get_request_json('/1/channels')
	
	def get_channels_current(self):
		'''GET channels/current'''
		return self.get_request_json('/1/channels/current')
	
	def set_channels_current(self, id):
		'''POST channels/current'''
		return self.post_request('/1/channels/current', id=id)
	
	def get_channels_id(self, id):
		'''GET channels/id'''
		return self.get_request_json('/1/channels/' + id)

	#Input methods
	def set_input_key(self, key):
		'''POST input/key'''
		return self.post_request('/1/input/key', key=key)

	#Source methods
	def get_sources(self):
		'''GET sources'''
		return self.get_request_json('/1/sources')
	
	def get_sources_current(self):
		'''GET sources/current'''
		return self.get_request_json('/1/sources/current')
	
	def set_sources_current(self, id):
		'''POST sources/current'''
		return self.post_request('/1/sources/current', id=id)
	
	#System methods
	def get_system(self):
		'''GET system'''
		return self.get_request_json('/1/system')
	
	def get_system_country(self):
		'''GET system/country'''
		return self.get_request_json('/1/system/country')
	
	def get_system_name(self):
		'''GET system/name'''
		return self.get_request_json('/1/system/name')
	
	def get_system_menulanguage(self):
		'''GET system/menulanguage'''
		return self.get_request_json('/1/system/menulanguage')
	
	def get_system_model(self):
		'''GET system/model'''
		return self.get_request_json('/1/system/model')
	
	def get_system_serialnumber(self):
		'''GET system/serialnumber'''
		return self.get_request_json('/1/system/serialnumber')
	
	def get_system_softwareversion(self):
		'''GET system/softwareversion'''
		return self.get_request_json('/1/system/softwareversion')
