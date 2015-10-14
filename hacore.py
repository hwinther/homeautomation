#!/usr/bin/python
from hacommon import ThreadList, QueueList, LoadModulesFromTuple
from hasettings import INSTALLED_APPS, WEBSERVICE_ENABLED, REMOTE_APPS, REMOTE_SOCKET_ENABLED
from habase import HomeAutomationQueueThread
from cli import LEDMatrixSocketClient

import logging, json, time, sys, os, traceback

def HACore():
	'''This class puts it all together, creating a state machine and a socket thread that calls state changes for received commands'''
	logging.info('HomeAutomationCore initialized')
	threadlist = ThreadList()
	sharedqueue = QueueList()
	
	modules = LoadModulesFromTuple(INSTALLED_APPS)
	logging.debug('Modules loaded:')
	for mod in modules:
		logging.debug(mod)
	
	#create threads and so on
	for mod in modules:
		if issubclass(modules[mod].cls, HomeAutomationQueueThread):
			mt = modules[mod].cls(name=mod, callback_function=None, queue=sharedqueue)
		else: #assume its the level below (no queue)
			mt = modules[mod].cls(name=mod, callback_function=None)
		threadlist.append(mt)
	
	logging.debug('Starting up module threads')
	for ti in threadlist:
		ti.start() #start all threads at this point

	if WEBSERVICE_ENABLED:
		from hawebservice import HAWebService
		lmws = HAWebService(name='WebService', callback_function=None, sharedqueue=sharedqueue)
		lmws.daemon = True
		lmws.start()
		threadlist.append(lmws)

	timecheck = time.time()
	while 1:
		#main loop that handles queue and threads, and through executing queue item changes the state of the statemachine
		try:
			for remote_module in REMOTE_APPS:
				remote_addr = remote_module['Address']
				remote_apps = remote_module['INSTALLED_APPS']
				if not 'socketclient' in remote_module.keys():
					remote_module['socketclient'] = LEDMatrixSocketClient(remote_addr) #cache
				
				for item in [i for i in sharedqueue if i.cls in remote_apps]:
					logging.info('Sending queue item to remote host: ' + str(remote_module) )
					remote_module['socketclient'].SendSerializedQueueItem(item.__str__())
					sharedqueue.remove(item)
			time.sleep(0.1)
			
			if time.time() - timecheck > 10:
				timecheck = time.time()
				logging.debug('10s mainloop interval, number of threads: %d, queue items: %d' %
					( len(threadlist), len(sharedqueue) ) )
				for _thread in threadlist:
					if not _thread.isAlive():
						logging.debug('Removing dead thread: ' + _thread.name)
						threadlist.remove(_thread)
		except KeyboardInterrupt:
			logging.info('Detected ctrl+c, exiting main loop and stopping all threads')
			break
		except:
			logging.critical("Unexpected error in main loop (exiting): " + traceback.format_exc() )
			break
	logging.debug('Stopping all threads')
	for _thread in threadlist:
		_thread.stop_event.set() #telling the threads to stop
