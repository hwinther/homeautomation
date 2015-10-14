#!/usr/bin/python
from habase import HomeAutomationThread
import logging

import web, json, os, time, base64, importlib
from hasettings import INSTALLED_APPS
from hacommon import SerializableQueueItem, LoadModulesFromTuple
from webservicecommon import WebServiceDefinition, WebServiceDefinitionList, webservicedecorator_init

#from sensordht import SensorDHT
#from hacec import HACec
#from hajointspace import HAJointSpace

class WebService_Index(object):
	def GET(self, name):
		if not name: 
			name = 'world'
		return 'Hello, ' + name + '!' + '<br><br>' + `globals()`

class WebService_State_JSONP(object): #TODO: should get all module states
	def GET(self):
		callback_name = web.input(callback='jsonCallback').callback
		web.header('Content-Type', 'application/javascript')
		return '%s(%s)' % (callback_name, '{}' )

class WebService_Definition_JSONP(object):
	def GET(self):
		callback_name = web.input(callback='jsonCallback').callback
		web.header('Content-Type', 'application/javascript')
		d = {}
		d['Definitions'] = []
		for wsdi in WebServiceDefinitions:
			d['Definitions'].append({'Name': wsdi.jsname, 'URL': wsdi.jsurl})
		return '%s(%s)' % (callback_name, json.dumps(d) )

class HAWebService(HomeAutomationThread):
	def __init__(self, name, callback_function, sharedqueue):
		HomeAutomationThread.__init__(self, name, callback_function)

		global WebServiceDefinitions
		WebServiceDefinitions = WebServiceDefinitionList()
		
		modules = LoadModulesFromTuple(INSTALLED_APPS)
		for mod in modules:
			if modules[mod].cls.webservice_definitions != None:
				WebServiceDefinitions.extend(modules[mod].cls.webservice_definitions)
				logging.debug(str(len(modules[mod].cls.webservice_definitions)) + ' definitions loaded from module ' + mod)
				for wsdi in modules[mod].cls.webservice_definitions:
					_c = getattr(modules[mod].module, wsdi.cl)
					globals()[wsdi.cl] = _c #just a little hacky
		
		WebServiceDefinitions.append(WebServiceDefinition(
			'/state/', 'WebService_State_JSONP', '/state/', 'wsState'))
		
		logging.info(str(len(WebServiceDefinitions)) + ' definitions loaded.')
		
		global SharedQueue
		SharedQueue = sharedqueue
		
		webservicedecorator_init(sharedqueue)

	def run(self):
		urls = (
				'/definitions/', 'WebService_Definition_JSONP',
				)
		for wsdi in WebServiceDefinitions:
			urls = urls + (wsdi.url, wsdi.cl)
		urls = urls + ('/(.*)', 'WebService_Index')
		logging.debug(str(urls))
		app = web.application(urls, globals())
		logging.info('Starting up WebService app')
		app.run()
