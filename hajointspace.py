#!/usr/bin/python
from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add
from hasettings import HA_JOINTSPACE_URI
import logging, json

import time, os, urllib, urllib2

class WebService_HARemoteKey(object):
	@webservice_jsonp
	def GET(self, keyname, SharedQueue, ThreadList):
		logging.info('WebService_HARemoteKey: ' + keyname)
		SharedQueue.append(SerializableQueueItem(HAJointSpace.__name__, CurrentInstance.remote_key, keyname)) #:\
		return CurrentInstance.get_json_status()

class HAJointSpace(HomeAutomationQueueThread):
	webservice_definitions = [
		#WebServiceDefinition(
		#	'/sensor/list', 'WebService_SensorList_JSONP', '/sensor/list', 'wsSensorList'),
		WebServiceDefinition(
			'/jointspace/remote/(\w+)', 'WebService_HARemoteKey', '/jointspace/remote', 'wsJSRemoteKey'),
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
	
	def remote_key(self, key):
		logging.debug('Remote key: ' + str(key))
		url = self.baseurl + '/1/input/key'
		data = json.dumps( {'key': str(key) } )
		req = urllib2.Request(url, data)
		response = urllib2.urlopen(req)
		content = response.read()
		return content
	
	def pre_processqueue(self):
		logging.info('JointSpace module initialized')
		webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
		self.timecheck = time.time()
		super(HAJointSpace, self).pre_processqueue()
	
	def post_processqueue(self):
		if time.time() - self.timecheck > 30:
			self.timecheck = time.time()
			logging.debug('30s interval')
			imageb64data = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABT0lEQVR4nO2XMY6DMBBFTZRij5Ay'+\
'JXQuOUaOwRG23DJH4Bh7DEo6KLfcI6QjBf6W/GdHNpGicbGvQbbHFv/j8Zhm2zZXQtd1ZYGBdV2b'+\
'krjTkUXfwVkbYMXzPCfj08clafeP36TtvU/ma46YO9DwHoDycd0VsbLINXXA/fwdB6eGdn+yE/U4'+\
'IJRDICtj5YwSP4VudsLcAZEF8ZtDKSseMisqDsV1vU/6zR1o2rbdnJN5HoEiKP9UsgLcQ/wY2kp2'+\
'+OCEuQPqSSjIKee4MZMtAXMH/l9A3wO5E68UrKNkQz0OoGqhBkz8whjXqiOtw/RUE1yoCfU4ALhq'+\
'CegsFyjzUGUZcwfEfYCZx1vS9sP3S/3Msix13AfUO2FU0n8l46hiXD21fjft8+EElANzB8qrYUC7'+\
'N6j3iQzmDog9AMReeBHt24N6HQBH/4oZTTkwd+AJOCiLlC/o6gAAAAAASUVORK5CYII=' #testing..
			#self.queue.append( SerializableQueueItem('LEDMatrixCore', 'rgbm.SetMatrixFromImgBase64', imageb64data) )
		super(HAJointSpace, self).post_processqueue()

	def get_class_name(self):
		return self.__class__.__name__
