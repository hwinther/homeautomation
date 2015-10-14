#!/usr/bin/python
import pickle, importlib, types, logging

class SerializableQueueItem:
	def __init__(self, cls, func, *args):
		self.cls = cls #class
		self.func = func
		self.args = args
	def __call__(self):
		#logging.debug('SerializableQueueItem func type: ' + str(type(self.func)) + ' callable? ' + str(callable(self.func)))
		if type(self.func) == types.FunctionType or callable(self.func):
			self.func(*self.args)
		elif type(self.func) == types.StringType:
			logging.debug('this call needs to be processed in the main thread context before being called')
			return False
	def __str__(self):
		return pickle.dumps(self)
	@staticmethod
	def __fromstr__(str):
		return pickle.loads(str)

class ThreadList(list):
	pass

class QueueList(list):
	'''Yes, this strictly isnt necessary due to the nature of lists in python (thread safety), but it still feels better being explicit like this'''
	pass #could potentially override the append method to only allow SerializableQueueItems
	
class ModuleDefinition:
	def __init__(self, mod, cls):
		self.module = mod
		self.cls = cls #class
	def __str__(self):
		return str(self.module) + ' - ' + str(self.cls)
	def __repr__(self):
		return self.__str__()

def LoadModulesFromTuple(modules):
	module_dict = {}
	for module in modules:
		mod = importlib.import_module(module.lower())
		cls = getattr(mod, module)
		module_dict[module] = ModuleDefinition(mod, cls)
	return module_dict
