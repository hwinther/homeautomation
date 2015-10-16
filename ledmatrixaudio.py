#!/usr/bin/python
from ledmatrixbase import LEDMatrixBase
from webservicecommon import WebServiceDefinition, webservice_jsonp
from hacommon import SerializableQueueItem
import logging

import alsaaudio as aa
from struct import unpack
from datetime import datetime
import numpy as np
import wave, sys, time, os
from ledmatrixcolor import CreateColormap

class WebService_PlayWav_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, filename, SharedQueue, ThreadList, rgbm):
		if not filename:
			logging.warn('WebService_PlayWav_And_State_JSONP missing filename argument')
			return 'WebService_PlayWav_And_State_JSONP missing filename argument' #this will in turn cause an exception in JS.. desired? IDK
		filepath = '/home/pi/wav/' + filename #TODO: get this path from config
		if not os.path.exists(filepath):
			logging.info('WebService_PlayWav_And_State_JSONP File path does not exist: ' + filepath)
			return 'WebService_PlayWav_And_State_JSONP File path does not exist: ' + filepath
		#if rgbm.is_audiovisualizing(): #not sure if this will work properly - it did not, we got idle state with music playing
		#	rgbm.StopAudioVisualize()
		logging.info('WebService_PlayWav_And_State_JSONP Playing wav file with audio visualizer:' + filepath)
		SharedQueue.append(SerializableQueueItem('LEDMatrixCore', rgbm.AudioVisualize, filepath))
		time.sleep(0.2) #give the main loop time to fetch this item (alternatively, can we push it directly to the SM?)
		return rgbm.get_json_state()

class WebService_AudioStop_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, SharedQueue, ThreadList, rgbm):
		logging.info('Attempting to stop audio thread')
		if rgbm.is_audiovisualizing():
			rgbm.StopAudioVisualize()
		time.sleep(0.2) #give the main loop time to fetch this item (alternatively, can we push it directly to the SM?)
		return rgbm.get_json_state()
		
class WebService_AudioTest_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, SharedQueue, ThreadList, rgbm):
		logging.info('Attempting to test something in the audio thread')
		if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
			new_freq_step = int(rgbm.current_audio_thread.freq_step * 0.9)
			logging.info('Setting audio thread freq_step to ' + str(new_freq_step) + ' making max freq ' + str(new_freq_step*31) )
			rgbm.current_audio_thread.freq_step = new_freq_step
		return rgbm.get_json_state()
		
class WebService_AudioSetMaxFreq_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, freqmax, SharedQueue, ThreadList, rgbm):
		if not freqmax:
			logging.warn('WebService_AudioSetMaxFreq_And_State_JSONP missing freqmax argument')
			return 'WebService_AudioSetMaxFreq_And_State_JSONP missing freqmax argument'
		logging.info('Attempting to change freqmax for audio thread')
		if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
			new_freq_step = int(int(freqmax) / 32.0) #TODO: get this from screen width config value
			logging.info('Setting audio thread freqmax to ' + str(freqmax) + ' making freq_step ' + str(new_freq_step) )
			rgbm.current_audio_thread.freq_step = new_freq_step
		return rgbm.get_json_state()
		
class WebService_AudioToggleSingleLine_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, SharedQueue, ThreadList, rgbm):
		logging.info('Attempting to toggle singleline in audio thread')
		if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
			logging.info('Toggling singleline on audio thread')
			rgbm.current_audio_thread.singleLine = not rgbm.current_audio_thread.singleLine
		return rgbm.get_json_state()
		
class WebService_AudioToggleBeat_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, SharedQueue, ThreadList, rgbm):
		logging.info('Attempting to toggle beat in audio thread')
		if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
			logging.info('Toggling beat detection on audio thread')
			rgbm.current_audio_thread.beatEnabled = not rgbm.current_audio_thread.beatEnabled
		return rgbm.get_json_state()
		
class WebService_AudioPause_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, SharedQueue, ThreadList, rgbm):
		logging.info('Attempting to pause audio thread')
		if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
			logging.info('Pausing audio thread')
			rgbm.current_audio_thread.paused = True
		return rgbm.get_json_state()
		
class WebService_AudioResume_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, SharedQueue, ThreadList, rgbm):
		logging.info('Attempting to resume audio thread')
		if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
			logging.info('Resuming audio thread')
			rgbm.current_audio_thread.paused = False
		return rgbm.get_json_state()
		
class WebService_AudioSetColormap_And_State_JSONP(object):
	@webservice_jsonp
	def GET(self, jsondatab64, SharedQueue, ThreadList, rgbm):
		if not jsondatab64:
			logging.warn('WebService_AudioSetColormap_And_State_JSONP missing jsondatab64 argument')
			return 'WebService_AudioSetColormap_And_State_JSONP missing jsondatab64 argument'
		logging.info('Attempting to set color map from json data')
		if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
			jsondata = base64.decodestring(jsondatab64)
			jd = json.loads(jsondata)
			newcolormap = CreateColormap(num_steps=jd['num_steps'], 
				start_red=jd['start_red'], start_green=jd['start_green'], start_blue=jd['start_blue'],
				end_red=jd['end_red'], end_green=jd['end_green'], end_blue=jd['end_blue'])
			logging.info('Changed colormap on audio thread')
			rgbm.current_audio_thread.colormap = newcolormap
		return rgbm.get_json_state()


class AudioBeat:
	'''State class used to community with beat_handler thread'''
	def __init__(self):
		self.activate=False
		self.xy=(0,0)

def beat_handler(beat, lights):
	'''beat_handler thread loop, should do something when a beat has been detected in audio thread'''
	lights[0].on = True
	while 1:
		if beat.activate == None: break #end thread
		#if beat.activate:
		#	print 'beat lights activated'
		#	for l in lights:
		#		l.on = True
		#		l.on = False
		#		break
		#	beat.activate=False
		lights[0].xy = beat.xy
		time.sleep(0.1)

class LEDMatrixAudio(LEDMatrixBase):
	'''The Audio class does audio spectogram analysis of audio chunks from a wav file and displays the frequency volume on rgbmatrix leds'''
	
	webservice_definitions = [
		WebServiceDefinition(
			'/audioPlay/(.*)', 'WebService_PlayWav_And_State_JSONP', '/audioPlay/', 'wsAudioPlay'),
		WebServiceDefinition(
			'/audioStop/', 'WebService_AudioStop_And_State_JSONP', '/audioStop/', 'wsAudioStop'),
		WebServiceDefinition(
			'/audioTest/', 'WebService_AudioTest_And_State_JSONP', '/audioTest/', 'wsAudioTest'),
		WebServiceDefinition(
			'/audioToggleSingleLine/', 'WebService_AudioToggleSingleLine_And_State_JSONP', '/audioToggleSingleLine/', 'wsAudioToggleSL'),
		WebServiceDefinition(
			'/audioToggleBeat/', 'WebService_AudioToggleBeat_And_State_JSONP', '/audioToggleBeat/', 'wsAudioToggleBeat'),
		WebServiceDefinition(
			'/audioPause/', 'WebService_AudioPause_And_State_JSONP', '/audioPause/', 'wsAudioPause'),
		WebServiceDefinition(
			'/audioResume/', 'WebService_AudioResume_And_State_JSONP', '/audioResume/', 'wsAudioResume'),
		WebServiceDefinition(
			'/audioSetColormap/(.*)', 'WebService_AudioSetColormap_And_State_JSONP', '/audioSetColormap/', 'wsAudioSetColormap'),
		WebServiceDefinition(
			'/audioSetMaxFreq/(.*)', 'WebService_AudioSetMaxFreq_And_State_JSONP', '/audioSetMaxFreq/', 'wsAudioSetMaxFreq'),
							]
	
	def __init__(self, name, callback_function, rgbmatrix, filepath, beatEnabled=None, singleLine=None, colormap=None):
		LEDMatrixBase.__init__(self, name=name, callback_function=callback_function, rgbmatrix=rgbmatrix)
		
		self.filepath = filepath
		self.beatEnabled = beatEnabled == True #coalesce None/False into False and keep True.. true
		self.singleLine = singleLine == True
		if colormap == None: self.colormap = CreateColormap()
		else: self.colormap = colormap
		self.paused = False
		self.freq_step = 156
		
		#this section initiates the beat thread if required
		self.lights = []
		self.beat = None
		self.beatInitialized = False
		if self.beatEnabled and self.beatInitialized == False:
			self.initBeat()

		#matrix, power, weighting vars.. these should be changeable on runtime to adjust the visualizer
		self.matrix    = [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0]
		self.power     = []
		self.weighting = [2,2,2,2,2,2,2,2, 4,4,4,4,4,4,4,4, 8,8,8,8,8,8,8,8, 16,16,16,16,16,16,16,16] # Change these according to taste
		
	def run(self):
		#try:
		if 1:
			self.rgbmatrix.Clear()
			self.playwavfile(self.filepath)
			self.rgbmatrix.Clear()
		#except:
		#	logging.warn("Unexpected error: " + str(sys.exc_info()[0]))
		logging.debug('LEDMatrixAudio now setting state back to idle')
		self.finalize()

	def initBeat(self):
		if self.beatInitialized == False:
			self.b = phue_Bridge(PHUE_BRIDGE_ADDRESS)
			_lights = self.b.get_light_objects()
			for l in _lights:
				if l.name.startswith('Kitchen'): #TODO: implement a way to pass on desired light entity names
					self.lights.append(l)
					l.on = False #initialize lights by turning them off
					
			self.beat = AudioBeat()
			self._thread = thread.start_new_thread(beat_handler, (self.beat,self.lights,))
			
			logging.info("Audio - beats enabled with these lights: " + str(self.lights) )
			self.beatInitialized = True
		
	def playwavfile(self, filepath):
		# Set up audio
		wavfile = wave.open(filepath, 'r')
		sample_rate = wavfile.getframerate()
		no_channels = wavfile.getnchannels()
		chunk       = 4096 # Use a multiple of 8
		output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL) #, u'sysdefault:CARD=HD') #TODO: use setting value for audio device
		output.setchannels(no_channels)
		output.setrate(sample_rate)
		output.setformat(aa.PCM_FORMAT_S16_LE)
		output.setperiodsize(chunk)
		# Process audio file
		data = wavfile.readframes(chunk)
		t = datetime.now()
		ss = False
		while (self.stop_event == None or not self.stop_event.is_set()) and data != '':
			if self.paused == True:
				time.sleep(0.5)
				continue #wait until pause is unset
		
			output.write(data)
			
			if self.beatEnabled and self.beatInitialized == False:
				self.initBeat()
			
			self.calculate_levels(data, chunk, sample_rate)

			self.rgbmatrix.Clear() #clear all pixels on screen
			for i in range(0, 31):
				for j in range(0, self.matrix[i]-1):
					#r, g, b = (clamp((self.matrix[i]-16)*16,0,255), clampX(self.matrix[i]*16,0,255), 0)
					if self.singleLine == True:
						#print self.matrix[i]-1, 32-self.matrix[i]
						#self.rgbmatrix.SetPixel(i, 32-self.matrix[i], self.matrix[i]*8, (255-(self.matrix[i]*8)), 127)
						self.rgbmatrix.SetPixel(i, 32-self.matrix[i], self.colormap[self.matrix[i]][0], self.colormap[self.matrix[i]][1], self.colormap[self.matrix[i]][2])
						break
					else:
						#self.rgbmatrix.SetPixel(i, 32-j, self.matrix[i]*8, (255-(self.matrix[i]*8)), 127)
						#self.rgbmatrix.SetPixel(i, 32-j, r, g, b)
						self.rgbmatrix.SetPixel(i, 32-j, self.colormap[self.matrix[i]][0], self.colormap[self.matrix[i]][1], self.colormap[self.matrix[i]][2])
				#Set_Column((1<<self.matrix[i])-1,0xFF^(1<<i))
				#mtx.SetPixel(i, 0, 0xFF^(1<<i), 0xFF^(1<<i), 0xFF^(1<<i))

			#special effects with selected hue lights:
			if self.beatEnabled and self.matrix[0] > 30:
				logging.debug('Audio - beat detected')
				self.beat.activate = True
				#lc1={'transitiontime' : 300, 'on' : True, 'bri' : 254}
				#for l in lights:
				#	l.on = True
				#for l in lights:
				#	l.on = False
			if self.beatEnabled:
				self.beat.xy = RGBtoXY(self.colormap[self.matrix[0]][0], self.colormap[self.matrix[0]][1], self.colormap[self.matrix[0]][2])

			data = wavfile.readframes(chunk)

		#cleanup
		if self.beatEnabled or self.beatInitialized:
			self.beat.activate = None #should shut down the thread

	# Return power array index corresponding to a particular frequency
	def piff(self, val, chunk, sample_rate):
		return int(2 * chunk * val / sample_rate)

	def calculate_levels(self, data, chunk, sample_rate):
		#global matrix
		# Convert raw data (ASCII string) to numpy array
		data = unpack("%dh"%(len(data)/2),data)
		data = np.array(data, dtype='h')
		# Apply FFT - real data
		fourier = np.fft.rfft(data)
		# Remove last element in array to make it the same size as chunk
		fourier = np.delete(fourier,len(fourier)-1)
		# Find average 'amplitude' for specific frequency ranges in Hz
		power = np.abs(fourier)
		#TODO: do not create the frequency range on the fly (on every chunk at that), rather make a new init function
		# that __init__ calls with a default step/range, and this will permit the values to be tuned on the fly
		#self.freq_step = 156 #new max is 4992 #100 #62
		freq = 0
		for _midx in range(0,32):
			#print _midx, freq, freq+freq_step
			try:
				self.matrix[_midx] = int(np.mean(power[self.piff(freq,chunk,sample_rate)	 :self.piff(freq+self.freq_step,chunk,sample_rate):1]))
			except ValueError: #ValueError: cannot convert float NaN to integer
				self.matrix[_midx] = 0 #seems like a safe default in this situation
			freq += self.freq_step

		# Tidy up column values for the LED matrix
		self.matrix = np.divide(np.multiply(self.matrix, self.weighting), 1000000)
		# Set floor at 0 and ceiling at 8 for LED matrix
		self.matrix = self.matrix.clip(0,31)
		#return matrix
