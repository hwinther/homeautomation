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

def webservicedecorator_init(sharedqueue):
	global SharedQueue
	SharedQueue = sharedqueue

def webservice_jsonp(f):
	"""Usage:
       @webservice_json
       def GET(self):
           ..."""
	def decorated(*args, **kwargs):
		logging.info('decorator entered')
		print "Arguments were: %s, %s" % (args, kwargs)
		callback_name = web.input(callback='jsonCallback').callback
		web.header('Content-Type', 'application/javascript')
		#kwargs['SharedQueue'] = SharedQueue #idk
		return '%s(%s)' % (callback_name, f(*args, SharedQueue=SharedQueue) )
	return decorated
