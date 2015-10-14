#!/usr/bin/python
import logging, threading, time, json
from hacommon import QueueList

class HomeAutomationThread(threading.Thread):
	webservice_definition = None
	
	def __init__(self, name, callback_function):
		threading.Thread.__init__(self)
		self.stop_event = threading.Event()
		self.setName(name)
		self.callback_function = callback_function
	
	def finalize(self):
		if self.callback_function != None:
			self.callback_function()
	
	def get_json_status(self):
		return json.dumps({self.__class__.__name__: []})
		
	def get_class_name(self):
		return self.__class__.__name__
	
class HomeAutomationQueueThread(HomeAutomationThread):
	def __init__(self, name, callback_function, queue):
		HomeAutomationThread.__init__(self, name, callback_function)
		if queue == None: queue = QueueList()
		self.queue = queue
	
	def pre_processqueue(self):
		pass #bad naming, before processing queue items at all

	def processqueue(self):
		self.pre_processqueue()
		clsname = self.get_class_name()
		while not self.stop_event.is_set():
			for item in [i for i in self.queue if i.cls == clsname]:
				#TODO: should really be True.. but this will be used until the modules return the right default value via decorator
				if item() == None:
					self.queue.remove(item)
				else:
					#try to translate the str in item into a function call within this context
					logging.debug('attempting to translate function call in deserialized queue item: ' + item.func)
					res = self
					for x in item.func.split('.'):
						res = getattr(res, x)
					logging.debug('res = ' + str(res))
					item.func = res #let it be handled on the next iteration..
			self.post_processqueue()
			
			time.sleep(0.1)
		self.finalize()
		
	def run(self):
		self.processqueue()
		
	def post_processqueue(self):
		pass

	def get_class_name(self):
		return self.__class__.__name__
	