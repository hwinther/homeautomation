#!/usr/bin/python
from hacommon import StateQueueItem, ThreadList, QueueList
from halogging import InitLogging, LogConcat
from hasettings import BASE_DIR
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
from ledmatrixwebservice import LEDMatrixWebService
from ledmatrixsocketservice import LEDMatrixSocketServiceUDP

def SplashScreen(rgbmatrix):
	"""xstart = 0
	xend = 32
	for r in range(0, 8):
		if r == 4:
			xstart = xstart + 8
			xend = xend - 8
		for x in range(xstart, xend):
			for y in range(0, 32):
				if r % 2 == 0: rgbmatrix.SetPixel(x, y, 255, 0, 0)
				else: rgbmatrix.SetPixel(32-x, y, 255, 0, 0)
			time.sleep(0.025)
			rgbmatrix.Clear()
	return"""
	for b in range(16):
		for g in range(8):
			for r in range(8):
				rgbmatrix.SetPixel(
				  (b / 4) * 8 + g,
				  (b & 3) * 8 + r,
				  (r * 0b001001001) / 2,
				  (g * 0b001001001) / 2,
				   b * 0b00010001)
	time.sleep(0.5)
	rgbmatrix.Clear()
	from PIL import Image
	image = Image.open("ledmatrix.png")
	image.load()          # Must do this before SetImage() calls
	#rgbmatrix.Fill(0x6F85FF) # Fill screen to sky color
	for n in range(32, -image.size[0], -1): # Scroll R to L
		rgbmatrix.SetImage(image.im.id, n, 0)
		time.sleep(0.015)
	rgbmatrix.Clear()
	
def ScreensaverA(rgbmatrix):
	from PIL import Image, ImageDraw
	image = Image.new("1", (32, 32)) # Can be larger than matrix if wanted!!
	draw  = ImageDraw.Draw(image)    # Declare Draw instance before prims
	# Draw some shapes into image (no immediate effect on matrix)...
	draw.rectangle((0, 0, 31, 31), fill=0, outline=1)
	draw.line((0, 0, 31, 31), fill=1)
	draw.line((0, 31, 31, 0), fill=1)
	# Then scroll image across matrix...
	for n in range(-32, 33): # Start off top-left, move off bottom-right
		rgbmatrix.Clear()
		# IMPORTANT: *MUST* pass image ID, *NOT* image object!
		rgbmatrix.SetImage(image.im.id, n, n)
		time.sleep(0.05)

#TODO: Should this be moved out too?
class RGBMatrix(object):
	def __init__(self, rgbmatrix, threadlist):
		self.rgbmatrix = rgbmatrix
		self.threadlist = threadlist
		self.current_audio_thread = None

	def get_json_state(self):
		audiostate = ''
		audiostate_paused = False
		if self.current_audio_thread != None and self.current_audio_thread.isAlive():
			audiostate = self.current_audio_thread.filepath.split(os.sep)[-1] #try to get the filename out of the path
			audiostate_paused = self.current_audio_thread.paused
		return json.dumps({'state': self.state, 'audiostate': audiostate, 'audiostate_paused':audiostate_paused })

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
		lma = LEDMatrixAudio(name='Audio', rgbmatrix=rgbmatrix, callback_function=self.to_idle, filepath=filename) #which one is it?
		lma.start()
		self.current_audio_thread = lma
		self.threadlist.append(lma)

	def on_enter_stopaudiovisualizing(self):
		if self.current_audio_thread != None and self.current_audio_thread.isAlive():
			self.current_audio_thread.stop_event.set()
		self.to_idle()

	def on_enter_settingmatrixfromimage(self, imagedata):
		logging.debug("We've just entered state settingmatrixfromimage!")
		lmi = LEDMatrixImage(name='Image', rgbmatrix=rgbmatrix, callback_function=self.to_idle, imagebase64=imagedata)
		lmi.start()
		self.threadlist.append(lmi)
		
	def on_enter_splashscreen(self):
		SplashScreen(rgbmatrix)
		self.to_idle()
		
	def on_enter_screensaver(self):
		#ScreensaverA(rgbmatrix)
		#SplashScreen(rgbmatrix)
		self.to_idle()

def LEDMatrixCore(rgbmatrix):
	'''This class puts it all together, creating a state machine and a socket thread that calls state changes for received commands'''
	logging.info('LEDMatrixCore started')
	threadlist = ThreadList()
	queue = QueueList()
	rgbm = RGBMatrix(rgbmatrix, threadlist)
	
	transitions = [
		{ 'trigger': 'SetPixel', 'source': 'idle', 'dest': 'settingpixel' },
		{ 'trigger': 'Clear', 'source': 'idle', 'dest': 'clearing' },
		{ 'trigger': 'AudioVisualize', 'source': 'idle', 'dest': 'audiovisualizing' },
		{ 'trigger': 'StopAudioVisualize', 'source': 'audiovisualizing', 'dest': 'stopaudiovisualizing' },
		{ 'trigger': 'SetMatrixFromImgBase64', 'source': 'idle', 'dest': 'settingmatrixfromimage' },
		{ 'trigger': 'Screensaver', 'source': 'idle', 'dest': 'screensaver' },
		{ 'trigger': 'SplashScreen', 'source': 'idle', 'dest': 'splashscreen' },
	]
	machine = Machine(model=rgbm,
		states=['idle', 'settingpixel', 'clearing', 'audiovisualizing', 'settingmatrixfromimage',
			'stopaudiovisualizing', 'screensaver', 'splashscreen'], transitions=transitions, initial='idle')

	lmws = LEDMatrixWebService(name='WebService', callback_function=None, rgbmatrix=rgbmatrix, g_rgbm=rgbm, g_queue=queue)
	lmws.daemon = True
	lmws.start()
	threadlist.append(lmws)
	
	lmssu = LEDMatrixSocketServiceUDP(name='SocketService', callback_function=None, rgbmatrix=rgbmatrix, rgbm=rgbm, queue=queue)
	lmssu.start()
	threadlist.append(lmssu)
	
	rgbm.to_splashscreen()
	
	#drawClock = False
	#drawClockClear = True
	timecheck = time.time()
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

if __name__ == '__main__':
	InitLogging(BASE_DIR + os.sep + 'rgbmatrix.log')
	rgbmatrix = Adafruit_RGBmatrix(32, 1)
	LEDMatrixCore(rgbmatrix)
