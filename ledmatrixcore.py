#!/usr/bin/python
from habase import HomeAutomationQueueThread
from hacommon import ThreadList, QueueList, LoadModulesFromTuple
from halogging import InitLogging, LogConcat
from hasettings import BASE_DIR, LEDMATRIXCORE_APPS
from webservicecommon import webservicedecorator_globals_add, webservice_state_instances_add
from ledmatrixcolor import CreateColormap
#from dgfont import displayCurrentTime
from rgbmatrix import Adafruit_RGBmatrix
import logging, time, sys, os, json

#STATE MACHINE
from transitions import Machine
from transitions.core import MachineError

#MODULES:
from ledmatriximage import LEDMatrixImage
from ledmatrixaudio import LEDMatrixAudio
from ledmatrixsocketservice import LEDMatrixSocketServiceUDP

from ledmatrixanimations import SplashScreen, ScreensaverA, CylonScan

#TODO: should perhaps be merged with LEDMatrixCore class so as to be more in line with other modules (self contained and inheriting from habase*)
class RGBMatrix(object):
	def __init__(self, rgbmatrix, sharedqueue, threadlist):
		self.rgbmatrix = rgbmatrix
		self.sharedqueue = sharedqueue
		self.threadlist = threadlist
		self.current_audio_thread = None

	def get_json_state(self):
		audiostate = ''
		audiostate_paused = False
		if self.current_audio_thread != None and self.current_audio_thread.isAlive():
			audiostate = self.current_audio_thread.filepath.split(os.sep)[-1] #try to get the filename out of the path
			audiostate_paused = self.current_audio_thread.paused
		return json.dumps({'LEDMatrixCore': {'state': self.state, 'audiostate': audiostate, 'audiostate_paused':audiostate_paused } })

	def on_enter_settingpixel(self, x, y, r, g, b):
		logging.debug("We've just entered state settingpixel!")
		self.rgbmatrix.SetPixel(x, y, r, g, b) #TODO: just do it directly for now
		self.to_idle()

	def on_enter_clearing(self):
		logging.debug("We've just entered state clearing!")
		self.rgbmatrix.Clear() #TODO: just do it directly for now
		self.to_idle()

	def on_enter_audiovisualizing(self, filename):
		logging.debug("We've just entered state audiovisualizing!")
		lma = LEDMatrixAudio(name='Audio', rgbmatrix=self.rgbmatrix, sharedqueue=self.sharedqueue, callback_function=self.to_idle, filepath=filename) #which one is it?
		lma.start()
		self.current_audio_thread = lma
		self.threadlist.append(lma)

	def on_enter_stopaudiovisualizing(self):
		if self.current_audio_thread != None and self.current_audio_thread.isAlive():
			self.current_audio_thread.stop_event.set()
		self.to_idle()

	def on_enter_settingmatrixfromimage(self, imagedata):
		logging.debug("We've just entered state settingmatrixfromimage!")
		lmi = LEDMatrixImage(name='Image', rgbmatrix=self.rgbmatrix, callback_function=self.to_idle, imagebase64=imagedata)
		lmi.start()
		self.threadlist.append(lmi)
	
	def on_enter_splashscreen(self):
		SplashScreen(self.rgbmatrix)
		self.to_idle()
	
	def on_enter_screensaver(self):
		#ScreensaverA(self.rgbmatrix)
		#SplashScreen(self.rgbmatrix)
		self.to_idle() #stop overriding the damn state machine D:

class LEDMatrixCore(HomeAutomationQueueThread):
	"""@staticmethod
	def webservice_definitions():
		WebServiceDefinitions = []
		modules = LoadModulesFromTuple(LEDMATRIXCORE_APPS)
		for mod in modules:
			if modules[mod].cls.webservice_definitions != None:
				WebServiceDefinitions.extend(modules[mod].cls.webservice_definitions)
		return WebServiceDefinitions"""

	def __init__(self, name, callback_function, queue, threadlist):
		'''This class puts it all together, creating a state machine and a socket thread that calls state changes for received commands'''
		HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

		logging.info('LEDMatrixCore initialized')
		self.rgbmatrix = Adafruit_RGBmatrix(32, 1)
		self.rgbm = RGBMatrix(self.rgbmatrix, self.queue, self.threadlist)
	
		self.transitions = [
			{ 'trigger': 'SetPixel', 'source': 'idle', 'dest': 'settingpixel' },
			{ 'trigger': 'Clear', 'source': 'idle', 'dest': 'clearing' },
			{ 'trigger': 'AudioVisualize', 'source': 'idle', 'dest': 'audiovisualizing' },
			{ 'trigger': 'StopAudioVisualize', 'source': 'audiovisualizing', 'dest': 'stopaudiovisualizing' },
			{ 'trigger': 'SetMatrixFromImgBase64', 'source': 'idle', 'dest': 'settingmatrixfromimage' },
			{ 'trigger': 'Screensaver', 'source': 'idle', 'dest': 'screensaver' },
			{ 'trigger': 'SplashScreen', 'source': 'idle', 'dest': 'splashscreen' },
		]
		self.states=['idle', 'settingpixel', 'clearing', 'audiovisualizing', 'settingmatrixfromimage',
				'stopaudiovisualizing', 'screensaver', 'splashscreen']
		
		self.machine = Machine(model = self.rgbm,
			states = self.states, transitions = self.transitions, initial = 'idle')

		lmssu = LEDMatrixSocketServiceUDP(name='SocketService', callback_function=None, rgbmatrix=self.rgbmatrix, rgbm=self.rgbm, queue=queue)
		#lmssu.start()
		threadlist.append(lmssu) #hacore should start() it afterwards
		
		global CurrentInstance
		CurrentInstance = self
		
	def pre_processqueue(self):
		webservicedecorator_globals_add(rgbm=self.rgbm)
		webservice_state_instances_add(self.__class__.__name__, self.rgbm.get_json_state)
		self.rgbm.to_splashscreen()
		self.timecheck = time.time()
		super(LEDMatrixCore, self).pre_processqueue()
		
	def post_processqueue(self):
		if time.time() - self.timecheck > 30:
			self.timecheck = time.time()
			logging.debug('30s interval')
			if self.rgbm.is_idle():
				self.rgbm.Screensaver()
		super(LEDMatrixCore, self).post_processqueue()
		
	def get_class_name(self):
		return self.__class__.__name__
		
	def exec_item(self, item):
		try:
			if self.rgbm.is_idle(): #dont process more items from the queue unless the state machine is back to idle
				super(LEDMatrixCore, self).exec_item(item) #while this might look strange its the proper way of overriding methods
		except MachineError as e:
			logging.warn('Caught state exception (retrying later) ' + str(sys.exc_info()[0]) )
			return False
	
	"""
	while 1:
		#main loop that handles queue and threads, and through executing queue item changes the state of the statemachine
		try:
			if rgbm.is_idle():
				try:
					for item in queue:
						if item() == None:
							queue.remove(item)
						else:
							#try to translate the str in item into a function call within this context
							logging.debug('attempting to translate function call in deserialized queue item: ' + item.func)
							#res = self
							i = 0
							for x in item.func.split('.'):
								if i == 0:
									res = locals()[x]
								else:
									res = getattr(res, x)
								i+=1
							logging.debug('res = ' + str(res))
							item.func = res #let it be handled on the next iteration..
							if item() == None:
								queue.remove(item)
								logging.debug('removed item after translate and call')
						#item() #runs the saved function and arguments
						#queue.remove(item)
					time.sleep(0.1)
				except MachineError as e:
					logging.error('Caught state exception (ignoring this command) ' + str(sys.exc_info()[0]) )
					time.sleep(0.2) #sleep longer so the state has a better chance at changing
			else:
				time.sleep(0.2)
			
			if time.time() - timecheck > 10:
				timecheck = time.time()
				logging.debug(LogConcat('10s mainloop interval, number of threads:', len(threadlist), 
					', state:', rgbm.state, ', queue items:', len(queue) ))
				for _thread in threadlist:
					if not _thread.isAlive():
						logging.debug('Removing dead thread: ' + _thread.name)
						threadlist.remove(_thread)
				if rgbm.is_idle():
					#display clock or screensaver
					rgbm.Screensaver()
				#	if drawClock:
				#		if drawClockClear: rgbmatrix.Clear()
				#		displayCurrentTime(rgbmatrix, 0, 0, 0, 0, 255)
		except KeyboardInterrupt:
			logging.info('Detected ctrl+c, exiting main loop and stopping all threads')
			break
		#except:
		#	logging.critical(LogConcat("Unexpected error in main loop (exiting):", sys.exc_info()[0]))
		#	break
	for _thread in threadlist:
		_thread.stop_event.set() #telling the threads to stop
	"""

#if __name__ == '__main__':
#	InitLogging(BASE_DIR + os.sep + 'rgbmatrix.log')
#	rgbmatrix = Adafruit_RGBmatrix(32, 1)
#	LEDMatrixCore(rgbmatrix)
