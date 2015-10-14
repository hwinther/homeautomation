#!/usr/bin/python
from ledmatrixbase import LEDMatrixBase
import logging

import alsaaudio as aa
from struct import unpack
from datetime import datetime
import numpy as np
import wave, sys, time
from ledmatrixcolor import CreateColormap

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
