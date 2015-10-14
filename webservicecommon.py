#!/usr/bin/python
import logging, web

class WebServiceDefinition:
	def __init__(self, url, cl, jsurl, jsname):
		self.url = url #path
		self.cl = cl #class (as str)
		self.jsurl = jsurl #start URL for JS (arguments will be / separated behind this)
		self.jsname = jsname #JS bind css class name

class WebServiceDefinitionList(list):
	pass
	
def webservicedecorator_globals_add(**kwargs):
	global webservice_globals
	for key, value in kwargs.iteritems():
		webservice_globals[key] = value
		
def webservice_state_instances_add(name, inst):
	global webservice_state_instances
	webservice_state_instances[name] = inst

def webservicedecorator_init(**kwargs):
	global webservice_globals
	webservice_globals = {}
	for key, value in kwargs.iteritems():
		webservice_globals[key] = value #perhaps just clone/copy the kwargs dict directly?
	global webservice_state_instances
	webservice_state_instances = {}

def webservice_state_jsonp(f):
	def decorated(*args, **kwargs):
		callback_name = web.input(callback='jsonCallback').callback
		web.header('Content-Type', 'application/javascript')
		for key, value in webservice_state_instances.iteritems():
			kwargs[key] = value
		return '%s(%s)' % (callback_name, f(*args, **kwargs) )
	return decorated

def webservice_jsonp(f):
	"""Usage:
       @webservice_jsonp
       def GET(self):
           ..."""
	def decorated(*args, **kwargs):
		#logging.info('decorator entered')
		#logging.debug("Arguments were: %s, %s" % (args, kwargs))
		callback_name = web.input(callback='jsonCallback').callback
		web.header('Content-Type', 'application/javascript')
		#kwargs['SharedQueue'] = SharedQueue #idk
		for key, value in webservice_globals.iteritems():
			kwargs[key] = value
		#logging.debug('decorated: ' + str(kwargs.keys()))
		retval = f(*args, **kwargs)
		logging.debug('decorator got retval: ' + retval)
		return '%s(%s)' % (callback_name, retval )
	return decorated
