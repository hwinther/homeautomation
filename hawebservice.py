#!/usr/bin/python
from habase import HomeAutomationQueueThread
import logging

import web, json, os, time, base64, types, traceback
from hasettings import INSTALLED_APPS
from hacommon import SerializableQueueItem, LoadModulesFromTuple
from webservicecommon import WebServiceDefinition, WebServiceDefinitionList, webservicedecorator_init, webservice_state_jsonp

class WebService_Index(object):
	def GET(self, name):
		if not name: 
			name = 'world'
		return 'Hello, ' + name + '!' + '<br><br>' + `globals()`

class WebService_State_JSONP(object): #TODO: should get all module states
	@webservice_state_jsonp
	def GET(self, **kwargs):
		jsondata = '{'
		for key, value in kwargs.iteritems():
			jsondata += '"' + key + '": ' + value() + ','
		jsondata += '}'
		return jsondata

class WebService_Definition_JSONP(object):
	def GET(self):
		callback_name = web.input(callback='jsonCallback').callback
		web.header('Content-Type', 'application/javascript')
		d = {}
		d['Definitions'] = []
		for wsdi in WebServiceDefinitions:
			d['Definitions'].append({'Name': wsdi.jsname, 'URL': wsdi.jsurl})
		return '%s(%s)' % (callback_name, json.dumps(d) )

class HAWebService(HomeAutomationQueueThread):
	webservice_definitions = [
			WebServiceDefinition(
				'/state/', 'WebService_State_JSONP', '/state/', 'wsState'),
							]

	def __init__(self, name, callback_function, queue, threadlist):
		HomeAutomationQueueThread.__init__(self, name = name, callback_function = callback_function,
											queue = queue, threadlist = threadlist)

		global WebServiceDefinitions
		WebServiceDefinitions = WebServiceDefinitionList()
		
		modules = LoadModulesFromTuple(INSTALLED_APPS)
		for mod in modules:
			wsdef = modules[mod].cls.webservice_definitions
			
			if wsdef != None:
				if type(wsdef) == types.FunctionType:
					logging.debug('wsdef is function, trying to execute')
					wsdef_addition = wsdef() #extend submodules or other dynamic collection
					if type(wsdef_addition) == types.ListType:
						wsdef = wsdef_addition
				elif type(wsdef) != types.ListType:
					wsdef = []
				
				WebServiceDefinitions.extend(wsdef)
				logging.debug(str(len(wsdef)) + ' definitions loaded from module ' + mod)
				
				for wsdi in wsdef:
					try:
						_c = getattr(modules[mod].module, wsdi.cl)
						globals()[wsdi.cl] = _c #just a little hacky
					except AttributeError:
						logging.warn('Unexpected exception caught while loading WSD ' + wsdi.cl + ' from module ' + mod + ' - ' + traceback.format_exc() )
		
		logging.info(str(len(WebServiceDefinitions)) + ' definitions loaded.')
		
		global SharedQueue
		SharedQueue = queue
		
		global ThreadList
		ThreadList = threadlist
		
		webservicedecorator_init(SharedQueue=SharedQueue, ThreadList=ThreadList)

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
