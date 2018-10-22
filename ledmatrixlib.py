#!/usr/bin/python
# coding=utf-8

####################################################
# LED Matrix Library - by Hans Chr Winther-Sorensen
#  - this is a collection of various useful functions
#  - a few of which I did not write but found out
#  - on the internets, if I make this public
#  - I can only hope I will have the good sense
#  - to credit those authors first.
#
# * 30.09.2015
#
####################################################

# SETTINGS SECTION
PHUE_BRIDGE_ADDRESS = '192.168.1.2'  # set this to your bridge hostname or IP, it is used with audio beat detection
# END SETTINGS SECTION

# IMPORT SECTION
# Generic
from datetime import datetime
from struct import unpack
import numpy as np
import wave
import sys
import os
import time
import thread
import base64
import logging
import threading
# COLOR
import math
# RGBmatrix
from rgbmatrix import Adafruit_RGBmatrix  # Requires rgbmatrix.so present in the same directory.
# DGfont
from dgfont import letters as dgfont_letters
# AUDIO
import alsaaudio as aa
# Philips hue
from phue import Bridge as phue_Bridge
# IMAGE
from PIL import Image
from PIL import ImageDraw
# SOCKET
import socket
import select
# STATE MACHINE
from transitions import Machine
from transitions.core import MachineError
# WEBSERVICE
import web
import json


# IMPORT SECTION END


# COLOR SECTION
def EnhanceColor(normalized):
    """Softening the colors?"""
    if normalized > 0.04045:
        return math.pow((normalized + 0.055) / (1.0 + 0.055), 2.4)
    else:
        return normalized / 12.92


# This is based on original code from http://stackoverflow.com/a/22649803 (above and below)
def RGBtoXY(r, g, b):
    """Convert RGB to Philips hue XY format"""
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    r_final = EnhanceColor(r_norm)
    g_final = EnhanceColor(g_norm)
    b_final = EnhanceColor(b_norm)

    x = r_final * 0.649926 + g_final * 0.103455 + b_final * 0.197109
    y = r_final * 0.234327 + g_final * 0.743075 + b_final * 0.022598
    z = r_final * 0.000000 + g_final * 0.053077 + b_final * 1.035763

    if x + y + z == 0:
        return 0, 0
    else:
        x_final = x / (x + y + z)
        y_final = y / (x + y + z)
    return x_final, y_final


def clamp(n, minn, maxn):
    """Clamp value within minimum and maximum values. E.g. 256 -> 255, -1 -> 0"""
    return max(min(maxn, n), minn)


def clampX(n, minn, maxn):
    """Flip clamped max value to min value, not sure if this is very useful"""
    x = clamp(n, minn, maxn)
    if x == maxn: return minn
    return x


def CreateColormap(num_steps=None, start_red=None, start_green=None, start_blue=None, end_red=None, end_green=None,
                   end_blue=None):
    """
    Creates a color map based on starting and ending points for each color in the RGB format
    Default values for most will do, they are 0-255 (max-min) and 32 steps
     (32 pixel height for screen when using this with an audio visualizer)
    """
    if num_steps is None: num_steps = 32

    if start_red is None: start_red = 0
    if start_green is None: start_green = 255
    if start_blue is None: start_blue = 0

    if end_red is None: end_red = 255
    if end_green is None: end_green = 0
    if end_blue is None: end_blue = 0

    # TEST set, blue to purple to orange
    # if start_red == None: start_red = 0 #0
    # if start_green == None: start_green = 0 #255
    # if start_blue == None: start_blue = 255 #0
    # if end_red == None: end_red = 255 #255
    # if end_green == None: end_green = 127 #0
    # if end_blue == None: end_blue = 0 #0

    red_diff = end_red - start_red
    green_diff = end_green - start_green
    blue_diff = end_blue - start_blue

    # Note: This is all integer division
    red_step = red_diff / num_steps
    green_step = green_diff / num_steps
    blue_step = blue_diff / num_steps

    current_red = start_red
    current_green = start_green
    current_blue = start_blue

    colormap = []
    for i in range(0, num_steps):
        current_red += red_step
        current_green += green_step
        current_blue += blue_step
        # print color
        # print i, current_red, current_green, current_blue
        # i+=1
        colormap.append([clamp(current_red, 0, 255), clamp(current_green, 0, 255), clamp(current_blue, 0, 255)])
    return colormap


# END COLOR SECTION

# DGFONT SECTION
def displayLetter(matrix, letter, x_rel, y_rel, r, g, b):
    """
    Display letter with RBGmatrix instance, starting at x_rel/y_rel and using colors r, g, b
    Returns new relative position that is clear off the letter
    """
    # print 'displaying letter ' + letter + ' at ' + str(x_rel) + ', ' + str(y_rel)
    x = 0
    y = y_rel
    first_run = True
    iteration = 0
    for rows in dgfont_letters[letter]:
        x = x_rel
        for col in rows:
            # print col
            if col == 1:
                matrix.SetPixel(x, y, r, g, b)
            x += 1
        y += 1
    return x, y


def displayText(matrix, text, x_rel, y_rel, r, g, b):
    """
    Display series of letters with RGBmatrix instance, starting at x_rel/y_rel and using colors r, g, b
    Returns new relative position that is clear off the text
    """
    x = x_rel
    y = y_rel
    for letter in text:
        x, y = displayLetter(matrix, letter, x, y, r, g, b)
        y = y_rel  # one line
        x += 1
    return x, y_rel + 6  # last is y, calculate one line height with 1 pixel spacer


def displayCurrentTime(matrix, x_rel, y_rel, r, g, b):
    """
    Displays current hour and minute with RBGmatrix instance at x_rel/y_rel and using colors r, g, b
    """
    dtime = datetime.now().strftime('%H:%M')
    y = y_rel
    x, y = displayText(matrix, dtime, x_rel, y, r, g, b)


# print datetime.now(), rnd, x, y
# END DGFONT SECTION


# AUDIO SECTION
class AudioBeat:
    """State class used to community with beat_handler thread"""

    def __init__(self):
        self.activate = False
        self.xy = (0, 0)


def beat_handler(beat, lights):
    """beat_handler thread loop, should do something when a beat has been detected in audio thread"""
    lights[0].on = True
    while 1:
        if beat.activate is None:
            break  # end thread
        # if beat.activate:
        #   print 'beat lights activated'
        #   for l in lights:
        #     l.on = True
        #     l.on = False
        #     break
        #   beat.activate=False
        lights[0].xy = beat.xy
        time.sleep(0.1)


class Audio:
    """The Audio class does audio spectogram analysis of audio chunks from a wav file and displays the frequency
    volume on rgbmatrix leds """

    def __init__(self, rgbmatrix, beatEnabled=None, singleLine=None, colormap=None):
        self.rgbmatrix = rgbmatrix
        self.beatEnabled = beatEnabled == True  # coalesce None/False into False and keep True.. true
        self.singleLine = singleLine == True
        if colormap is None:
            self.colormap = CreateColormap()
        else:
            self.colormap = colormap

        # self.beatEnabled = True #TODO: remove this, its a temporary test
        # self.singleLine = True

        # this section initiates the beat thread if required
        self.lights = []
        self.beat = None
        self.beatInitialized = False
        if self.beatEnabled and self.beatInitialized is False:
            self.initBeat()

            # matrix, power, weighting vars.. these should be changeable on runtime to adjust the visualizer
        self.matrix = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.power = []
        self.weighting = [2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8, 16, 16, 16, 16, 16,
                          16, 16, 16]
        self.b = None
        self._thread = None

        # Change these according to taste
        # weighting = [2,2,2,2,2,2,2,2,8,8,8,8,8,8,8,8,16,16,16,16,32,32,32,32,64,64,64,64,64,64,64,64]

    def initBeat(self):
        if self.beatInitialized is False:
            self.b = phue_Bridge(PHUE_BRIDGE_ADDRESS)
            _lights = self.b.get_light_objects()
            for l in _lights:
                if l.name.startswith('Kitchen'):  # TODO: implement a way to pass on desired light entity names
                    self.lights.append(l)
                    l.on = False  # initialize lights by turning them off

            self.beat = AudioBeat()
            self._thread = thread.start_new_thread(beat_handler, (self.beat, self.lights,))

            logging.info("Audio - beats enabled with these lights: " + str(self.lights))
            self.beatInitialized = True

    def playwavfile(self, filepath, stop_event=None):
        # Set up audio
        wavfile = wave.open(filepath, 'r')
        sample_rate = wavfile.getframerate()
        no_channels = wavfile.getnchannels()
        chunk = 4096  # Use a multiple of 8
        output = aa.PCM(aa.PCM_PLAYBACK,
                        aa.PCM_NORMAL)  # , u'sysdefault:CARD=HD') #TODO: use setting value for audio device
        output.setchannels(no_channels)
        output.setrate(sample_rate)
        output.setformat(aa.PCM_FORMAT_S16_LE)
        output.setperiodsize(chunk)
        # Process audio file
        data = wavfile.readframes(chunk)
        t = datetime.now()
        ss = False
        while (stop_event is None or not stop_event.is_set()) and data != '':
            output.write(data)

            if self.beatEnabled and self.beatInitialized is False:
                self.initBeat()

            self.calculate_levels(data, chunk, sample_rate)

            self.rgbmatrix.Clear()  # clear all pixels on screen
            for i in range(0, 31):
                for j in range(0, self.matrix[i] - 1):
                    # r, g, b = (clamp((self.matrix[i]-16)*16,0,255), clampX(self.matrix[i]*16,0,255), 0)
                    if self.singleLine is True:
                        # print self.matrix[i]-1, 32-self.matrix[i]
                        # self.rgbmatrix.SetPixel(i, 32-self.matrix[i], self.matrix[i]*8, (255-(self.matrix[i]*8)), 127)
                        self.rgbmatrix.SetPixel(i, 32 - self.matrix[i], self.colormap[self.matrix[i]][0],
                                                self.colormap[self.matrix[i]][1],
                                                self.colormap[self.matrix[i]][2])
                        break
                    else:
                        # self.rgbmatrix.SetPixel(i, 32-j, self.matrix[i]*8, (255-(self.matrix[i]*8)), 127)
                        # self.rgbmatrix.SetPixel(i, 32-j, r, g, b)
                        self.rgbmatrix.SetPixel(i, 32 - j, self.colormap[self.matrix[i]][0],
                                                self.colormap[self.matrix[i]][1], self.colormap[self.matrix[i]][2])
                        # Set_Column((1<<self.matrix[i])-1,0xFF^(1<<i))
                        # mtx.SetPixel(i, 0, 0xFF^(1<<i), 0xFF^(1<<i), 0xFF^(1<<i))

                        # special effects with selected hue lights:
            if self.beatEnabled and self.matrix[0] > 30:
                logging.debug('Audio - beat detected')
                self.beat.activate = True
                # lc1={'transitiontime' : 300, 'on' : True, 'bri' : 254}
                # for l in lights:
            # l.on = True
            # for l in lights:
            # l.on = False
            if self.beatEnabled:
                self.beat.xy = RGBtoXY(self.colormap[self.matrix[0]][0], self.colormap[self.matrix[0]][1],
                                       self.colormap[self.matrix[0]][2])

            data = wavfile.readframes(chunk)

            # cleanup
        if self.beatEnabled or self.beatInitialized:
            self.beat.activate = None  # should shut down the thread

    # Return power array index corresponding to a particular frequency
    def piff(self, val, chunk, sample_rate):
        return int(2 * chunk * val / sample_rate)

    def calculate_levels(self, data, chunk, sample_rate):
        # global matrix
        # Convert raw data (ASCII string) to numpy array
        data = unpack("%dh" % (len(data) / 2), data)
        data = np.array(data, dtype='h')
        # Apply FFT - real data
        fourier = np.fft.rfft(data)
        # Remove last element in array to make it the same size as chunk
        fourier = np.delete(fourier, len(fourier) - 1)
        # Find average 'amplitude' for specific frequency ranges in Hz
        power = np.abs(fourier)
        # TODO: do not create the frequency range on the fly (on every chunk at that), rather make a new init function
        # that __init__ calls with a default step/range, and this will permit the values to be tuned on the fly
        freq_step = 156  # new max is 4992 #100 #62
        freq = 0
        for _midx in range(0, 32):
            # print _midx, freq, freq+freq_step
            try:
                self.matrix[_midx] = int(np.mean(
                    power[self.piff(freq, chunk, sample_rate):self.piff(freq + freq_step, chunk, sample_rate):1]))
            except ValueError:  # ValueError: cannot convert float NaN to integer
                self.matrix[_midx] = 0  # seems like a safe default in this situation
            freq += freq_step

        # Tidy up column values for the LED matrix
        self.matrix = np.divide(np.multiply(self.matrix, self.weighting), 1000000)
        # Set floor at 0 and ceiling at 8 for LED matrix
        self.matrix = self.matrix.clip(0, 31)

        # return matrix


class AudioThread(threading.Thread):
    def __init__(self, rgbmatrix, filepath, name=None, callback_func=None, stop_event=None):
        threading.Thread.__init__(self)
        self.rgbmatrix = rgbmatrix
        self.filepath = filepath
        if name is not None:
            self.setName(name)
        self.callback_func = callback_func
        self.stop_event = stop_event
        self.audio = Audio(rgbmatrix)

    def run(self):
        try:
            # if 1:
            self.rgbmatrix.Clear()
            self.audio.playwavfile(self.filepath, self.stop_event)
            self.rgbmatrix.Clear()
        except:
            logging.warn(LogConcat("Unexpected error:", sys.exc_info()[0]))
        logging.debug('AudioThread now setting state back to idle')
        if self.callback_func is not None:
            self.callback_func()


# END AUDIO SECTION

# IMAGE SECTION
def alpha_to_color(image, color=(255, 255, 255)):
    """Set all fully transparent pixels of an RGBA image to the specified color.
    This is a very simple solution that might leave over some ugly edges, due
    to semi-transparent areas. You should use alpha_composite_with color instead.

    Source: http://stackoverflow.com/a/9166671/284318

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """
    x = np.array(image)
    r, g, b, a = np.rollaxis(x, axis=-1)
    r[a == 0] = color[0]
    g[a == 0] = color[1]
    b[a == 0] = color[2]
    x = np.dstack([r, g, b, a])
    return Image.fromarray(x, 'RGBA')


def alpha_composite(front, back):
    """Alpha composite two RGBA images.

    Source: http://stackoverflow.com/a/9166671/284318

    Keyword Arguments:
    front -- PIL RGBA Image object
    back -- PIL RGBA Image object

    """
    front = np.asarray(front)
    back = np.asarray(back)
    result = np.empty(front.shape, dtype='float')
    alpha = np.index_exp[:, :, 3:]
    rgb = np.index_exp[:, :, :3]
    falpha = front[alpha] / 255.0
    balpha = back[alpha] / 255.0
    result[alpha] = falpha + balpha * (1 - falpha)
    old_setting = np.seterr(invalid='ignore')
    result[rgb] = (front[rgb] * falpha + back[rgb] * balpha * (1 - falpha)) / result[alpha]
    np.seterr(**old_setting)
    result[alpha] *= 255
    np.clip(result, 0, 255)
    # astype('uint8') maps np.nan and np.inf to 0
    result = result.astype('uint8')
    result = Image.fromarray(result, 'RGBA')
    return result


def alpha_composite_with_color(image, color=(255, 255, 255)):
    """Alpha composite an RGBA image with a single color image of the
    specified color and the same size as the original image.

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """
    back = Image.new('RGBA', size=image.size, color=color + (255,))
    return alpha_composite(image, back)


def pure_pil_alpha_to_color_v1(image, color=(255, 255, 255)):
    """Alpha composite an RGBA Image with a specified color.

    NOTE: This version is much slower than the
    alpha_composite_with_color solution. Use it only if
    numpy is not available.

    Source: http://stackoverflow.com/a/9168169/284318

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """

    def blend_value(back, front, a):
        return (front * a + back * (255 - a)) / 255

    def blend_rgba(back, front):
        result = [blend_value(back[i], front[i], front[3]) for i in (0, 1, 2)]
        return tuple(result + [255])

    im = image.copy()  # don't edit the reference directly
    p = im.load()  # load pixel array
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            p[x, y] = blend_rgba(color + (255,), p[x, y])

    return im


def pure_pil_alpha_to_color_v2(image, color=(255, 255, 255)):
    """Alpha composite an RGBA Image with a specified color.

    Simpler, faster version than the solutions above.

    Source: http://stackoverflow.com/a/9459208/284318

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """
    image.load()  # needed for split()
    background = Image.new('RGB', image.size, color)
    background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
    return background


def SetMatrixFromImgBase64(rgbmatrix, imgdatab64, callback_func=None, stop_event=None):
    """Sets rgbmatrix to image based on HTML inline image format"""

    if imgdatab64.find('data:image/png;base64,') != -1:
        ext = 'png'
        imgdatacleanb64 = imgdatab64.replace('data:image/png;base64,', '')
    elif imgdatab64.find('data:image/gif;base64,') != -1:
        ext = 'gif'
        imgdatacleanb64 = imgdatab64.replace('data:image/gif;base64,', '')
    else:
        logging.info(LogConcat('invalid image data', imgdatab64))
        return

    if ext == 'png':
        logging.info('displaying png')
        imgdata = base64.decodestring(imgdatacleanb64)
        open('/tmp/matrix.temp.' + ext, 'wb').write(imgdata)
        os.system('convert /tmp/matrix.temp.' + ext + ' png32:/tmp/matrix.temp.32.png')
        image = Image.open('/tmp/matrix.temp.32.png')
        image.load()
        img = image.resize((32, 32))
        # If image has an alpha channel
        if image.mode == 'RGBA':
            logging.debug('converting RGBA image')
            img = pure_pil_alpha_to_color_v2(img)  # remove alpha layer
        rgbmatrix.SetImage(img.im.id, 0, 0)
    elif ext == 'gif':
        logging.info('displaying gif')
        imgdata = base64.decodestring(imgdatacleanb64)
        open('/tmp/matrix.temp.' + ext, 'wb').write(imgdata)
        image = Image.open('/tmp/matrix.temp.' + ext)
        frame = 1
        while stop_event is None or not stop_event.is_set():
            logging.debug(LogConcat('frame', frame))
            img = image.resize((32, 32))
            animframe_in = '/tmp/matrix.animframe%d.png' % frame
            animframe_out = '/tmp/matrix.animframe%d.out.png' % frame
            img.save('/tmp/matrix.animframe%d.png' % frame)
            os.system('convert ' + animframe_in + ' png32:' + animframe_out)
            img = Image.open(animframe_out)
            img.load()
            rgbmatrix.SetImage(img.im.id, 0, 0)
            time.sleep(0.05)
            try:
                image.seek(image.tell() + 1)
            except:
                logging.debug(LogConcat('detected end at frame', frame))
                break
            frame += 1
    if callback_func is not None:
        logging.debug('Setting state back to idle')
        callback_func()


# END IMAGE SECTION

# SOCKET SECTION
# class ThreadState: #deprecated in favor of threading.Event
#   def __init__(self):
#     self.running = True

# needs to be set on both client and server side, used to determine the beginning and end of commands
SOCKET_SPLITCHARS = '\x01\x02\x03\x04'


def DefaultSocketCommandHandler(rgbmatrix, cmd, addr):
    """Socket command handler that blocks while perfroming rgbmatrix actions"""
    # set pixel command: 127 X Y R G B
    #				    0   1 2 3 4 5
    if len(cmd) == 0: return  # must be invalid
    datacmd = cmd[0]
    dataarg = ''
    if len(cmd) > 1:
        dataarg = cmd[1:]
    logging.debug(LogConcat('handling cmd ' + str(ord(datacmd)) + ' [', dataarg, '] for', addr))
    if ord(datacmd) == 126:
        logging.info('Clearing screen')
        rgbmatrix.Clear()
    elif ord(datacmd) == 127 and len(cmd) == 6:
        x, y, r, g, b = ord(dataarg[0]), ord(dataarg[1]), ord(dataarg[2]), ord(dataarg[3]), ord(dataarg[4])
        logging.info('Setting matrix pixel at x=' + str(x) + ' y=' + str(y) + ' to color r=' + str(r) + ',g=' + str(
            g) + ',b=' + str(b))
        rgbmatrix.SetPixel(x, y, r, g, b)
    elif ord(datacmd) == 128:
        logging.info('Displaying image')
        SetMatrixFromImgBase64(rgbmatrix, dataarg)
    elif ord(datacmd) == 129:
        filepath = '/home/pi/wav/' + dataarg
        if not os.path.exists(filepath):
            logging.info(LogConcat('(Play wav) File does not exist:', filepath))
            return
        logging.info(LogConcat('Playing wav file with audio visualizer:', filepath))
        a = Audio(rgbmatrix)
        a.playwavfile(filepath)


class StateSocketCommand:
    def __init__(self, rgbm, queue):
        self.rgbm = rgbm
        self.queue = queue

    def StateSocketCommandHandler(self, rgbmatrix, cmd, addr):
        """Socket command handler that blocks while perfroming rgbmatrix actions"""
        # set pixel command: 127 X Y R G B
        #				    0   1 2 3 4 5
        if len(cmd) == 0: return  # must be invalid
        datacmd = cmd[0]
        dataarg = ''
        if len(cmd) > 1:
            dataarg = cmd[1:]
        logging.debug(LogConcat('handling cmd ' + str(ord(datacmd)) + ' [', dataarg, '] for', addr))
        if ord(datacmd) == 126:
            logging.info('Clearing screen')
            self.queue.append(StateQueueItem(self.rgbm.Clear))
        elif ord(datacmd) == 127 and len(cmd) == 6:
            x, y, r, g, b = ord(dataarg[0]), ord(dataarg[1]), ord(dataarg[2]), ord(dataarg[3]), ord(dataarg[4])
            logging.info('Setting matrix pixel at x=' + str(x) + ' y=' + str(y) + ' to color r=' + str(r) + ',g=' + str(
                g) + ',b=' + str(b))
            self.queue.append(StateQueueItem(self.rgbm.SetPixel, x, y, r, g, b))
        elif ord(datacmd) == 128:
            logging.info('Displaying image')
            self.queue.append(StateQueueItem(self.rgbm.SetMatrixFromImgBase64, dataarg))
        elif ord(datacmd) == 129:
            filepath = '/home/pi/wav/' + dataarg
            if not os.path.exists(filepath):
                logging.info(LogConcat('(Play wav) File does not exist:', filepath))
                return
            logging.info(LogConcat('Playing wav file with audio visualizer:', filepath))
            self.queue.append(StateQueueItem(self.rgbm.AudioVisualize, filepath))
        elif ord(datacmd) == 130:
            # stop playing wav file
            logging.info('Attempting to stop audio thread')
            # self.queue.append(StateQueueItem(self.rgbm.StopAudioVisualize)) #will not work because the queuehandler is waiting for is_idle
            if self.rgbm.is_audiovisualizing():
                self.rgbm.StopAudioVisualize()
        else:
            logging.warn('Unknown command, not doing anything')


def SocketBufferHandler(rgbmatrix, d, a, di, socketcommandhandler):
    """Handles your socket buffers and shit, yo"""
    if a not in di.keys():
        di[a] = ''
    buff = di[a] + d
    l = buff.split(SOCKET_SPLITCHARS)
    if len(l) == 0:
        return
    if l[-1] == '':  # complete data
        for x in l:
            if x == '':
                continue
            socketcommandhandler(rgbmatrix, x, a)
            di[a] = ''  # clear buffer just to be sure
    else:
        for x in l[:-1]:
            if x == '':
                continue
            socketcommandhandler(rgbmatrix, x, a)
        di[a] = l[-1]  # last data added back to buffer
    return di


def SocketListener(rgbmatrix, stop_event, socketcommandhandler=None):
    if socketcommandhandler is None:
        socketcommandhandler = DefaultSocketCommandHandler
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # for tcp set option to reuse
    s.bind(('', 1234))
    logging.info('SocketListener listening on 0.0.0.0:1234 (UDP)')
    s.setblocking(False)
    bufferdict = {}  # dictionary that keeps each clients buffer when the received data becomes segmented
    while not stop_event.is_set():
        ready = select.select([s], [], [], 1)
        if ready[0]:
            data, addr = s.recvfrom(1024 * 16)
            bufferdict = SocketBufferHandler(rgbmatrix, data, addr, bufferdict, socketcommandhandler)


# END SOCKET SECTION

# LOGGING SECTION
def InitLogging():
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler("/usr/wsh/rpi/new_servercode/ledmatrix.log")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)


def LogConcat(*args):
    sl = []
    for x in args:
        sl.append(str(x))
    return ' '.join(sl)


# END LOGGING SECTION

# STATE SECTION
class ThreadAndEvent:
    def __init__(self, name, t, e):
        self.name = name
        self.t = t
        self.e = e


class ThreadList(list):
    pass


class QueueList(list):
    """
    Yes, this strictly isnt necessary due to the nature of lists in python (thread safety),
     but it still feels better being explicit like this
    """
    pass  # could potentially override the append method to only allow statequeueitems


class StateQueueItem:
    def __init__(self, func, *args):
        self.func = func
        self.args = args

    def __call__(self):
        self.func(*self.args)


class RGBMatrix(object):
    def __init__(self, rgbmatrix, threadlist):
        self.rgbmatrix = rgbmatrix
        self.threadlist = threadlist
        self.current_audio_threadandevent = None

    def on_enter_settingpixel(self, x, y, r, g, b):
        logging.debug("We've just entered state settingpixel!")
        self.rgbmatrix.SetPixel(x, y, r, g, b)
        self.to_idle()

    def on_enter_clearing(self):
        logging.debug("We've just entered state clearing!")
        self.rgbmatrix.Clear()  # just do it directly for now
        self.to_idle()

    def on_enter_audiovisualizing(self, filename):
        logging.debug("We've just entered state audiovisualizing!")
        t1_stop = threading.Event()
        t1 = AudioThread(self.rgbmatrix, filename, name='AudioThread', callback_func=self.to_idle, stop_event=t1_stop)
        # TODO: is it filename or actually filepath?
        # t1 = threading.Thread(name='AudioThread',
        #              target=AudioThread,
        #              args=(self.rgbmatrix,filename,self.to_idle,t1_stop,))
        t1.start()
        # once all worker threads are proper instances of Thread then this shouldn't be required.
        tae = ThreadAndEvent('AudioThread', t1, t1_stop)
        # Maybe subclass threading.Thread and set stop_event by default to ensure that it will
        #  always be there instead of this wrapping object
        self.current_audio_threadandevent = tae
        self.threadlist.append(tae)

    def on_enter_settingmatrixfromimage(self, imagedata):
        logging.debug("We've just entered state settingmatrixfromimage!")
        t1_stop = threading.Event()  # TODO: separate setmatrix blocking method from thread code like Audio/AudioThread
        t1 = threading.Thread(name='SetMatrixFromImgBase64',
                              target=SetMatrixFromImgBase64,
                              args=(self.rgbmatrix, imagedata, self.to_idle, t1_stop,))
        t1.start()
        self.threadlist.append(ThreadAndEvent('SetMatrixFromImgBase64', t1, t1_stop))

    def on_enter_stopaudiovisualizing(self):
        if self.current_audio_threadandevent is not None and self.current_audio_threadandevent.t.isAlive():
            self.current_audio_threadandevent.e.set()  # tell the thread to stop via thread.Event
        self.to_idle()


def StateSocket(rgbmatrix):
    """
    This class puts it all together, creating a state machine and
     a socket thread that calls state changes for received commands
    """
    logging.info('StateSocket started')
    # global threadlist #ack..
    threadlist = ThreadList()
    global rgbm  # :\
    rgbm = RGBMatrix(rgbmatrix, threadlist)
    transitions = [
        {'trigger': 'SetPixel', 'source': 'idle', 'dest': 'settingpixel'},
        {'trigger': 'Clear', 'source': 'idle', 'dest': 'clearing'},
        {'trigger': 'AudioVisualize', 'source': 'idle', 'dest': 'audiovisualizing'},
        {'trigger': 'StopAudioVisualize', 'source': 'audiovisualizing', 'dest': 'stopaudiovisualizing'},
        {'trigger': 'SetMatrixFromImgBase64', 'source': 'idle', 'dest': 'settingmatrixfromimage'},
    ]
    machine = Machine(model=rgbm,
                      states=['idle', 'settingpixel', 'clearing', 'audiovisualizing', 'settingmatrixfromimage',
                              'stopaudiovisualizing'],
                      transitions=transitions, initial='idle')
    global queue  # :\
    queue = QueueList()

    ssc = StateSocketCommand(rgbm, queue)
    # TODO: make a wrapper for the thread initialization
    t1_stop = threading.Event()  # stop_event.wait(1) #works like time.sleep(1)
    t1 = threading.Thread(name='SocketListener',
                          target=SocketListener,
                          args=(rgbmatrix, t1_stop, ssc.StateSocketCommandHandler,))
    t1.start()
    threadlist.append(ThreadAndEvent('SocketListener', t1,
                                     t1_stop))  # this may be too much, maybe thread could hold event itself somehow?

    # this event actually has no function as the WebService instance will not get it passed in and
    #  couldn't use it anyway
    t1_stop = threading.Event()
    # however it is supposed to stop when the parent thread stops due to the daemon setting
    t1 = WebServiceThread()
    t1.daemon = True
    t1.start()
    threadlist.append(ThreadAndEvent('WebServiceThread', t1, t1_stop))

    drawClock = False
    drawClockClear = True
    timecheck = time.time()
    while 1:
        # main loop that handles queue and threads, and
        #  through executing queue item changes the state of the statemachine
        try:
            if rgbm.is_idle():
                try:
                    for item in queue:
                        item()  # runs the saved function and arguments
                        queue.remove(item)
                    time.sleep(0.1)
                except MachineError as e:
                    logging.error('Caught state exception (ignoring this command) ' + str(sys.exc_info()[0]))
                    time.sleep(0.2)  # sleep longer so the state has a better chance at changing
            else:
                time.sleep(0.2)

            if time.time() - timecheck > 10:
                timecheck = time.time()
                logging.debug(LogConcat('10s mainloop interval, number of threads:', len(threadlist),
                                        ', state:', rgbm.state, ', queue items:', len(queue)))
                for te in threadlist:
                    if not te.t.isAlive():
                        logging.debug('Removing dead thread: ' + te.name)
                        threadlist.remove(te)
                if rgbm.is_idle():
                    # display clock or screensaver
                    if drawClock:
                        if drawClockClear:
                            rgbmatrix.Clear()
                        displayCurrentTime(rgbmatrix, 0, 0, 0, 0, 255)
        except KeyboardInterrupt:
            logging.info('Detected ctrl+c, exiting main loop and stopping all threads')
            break
        except:
            logging.critical(LogConcat("Unexpected error in main loop (exiting):", sys.exc_info()[0]))
            break
    for te in threadlist:
        te.e.set()  # telling the threads to stop


# END STATE SECTION

# WEBSERVICE SECTION
class WebService_Index(object):
    def GET(self, name):
        if not name:
            name = 'world'
        return 'Hello, ' + name + '!'


class WebService_Definition_JSONP(object):
    def GET(self):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        d = dict()
        d['Definitions'] = []
        for wsdi in WebServiceDefinitions:
            d['Definitions'].append({'Name': wsdi.jsname, 'URL': wsdi.jsurl, 'UseArg1': wsdi.useArg1})
        return '%s(%s)' % (callback_name, json.dumps(d))


class WebService_State_JSONP(object):
    def GET(self):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        audiostate = ''
        # TODO: wrap this shit in a function in rgbm
        if rgbm.current_audio_threadandevent is not None and rgbm.current_audio_threadandevent.t.isAlive():
            audiostate = rgbm.current_audio_threadandevent.t.filepath
        return '%s(%s)' % (callback_name, json.dumps({'state': rgbm.state, 'audiostate': audiostate}))


class WebService_PlayWav_And_State_JSONP(object):
    def GET(self, filename):
        if not filename:
            # this will in turn cause an exception in JS.. desired? IDK
            logging.warn('WebService_PlayWav_And_State_JSONP missing filename arguent')
            return 'WebService_PlayWav_And_State_JSONP missing filename arguent'
        filepath = '/home/pi/wav/' + filename
        if not os.path.exists(filepath):
            logging.info('WebService_PlayWav_And_State_JSONP File path does not exist: ' + filepath)
            return 'WebService_PlayWav_And_State_JSONP File path does not exist: ' + filepath
            # not sure if this will work properly - it did not, we got idle state with music playing
            # if rgbm.is_audiovisualizing():
        # rgbm.StopAudioVisualize()
        logging.info('WebService_PlayWav_And_State_JSONP Playing wav file with audio visualizer:' + filepath)
        queue.append(StateQueueItem(rgbm.AudioVisualize, filepath))
        time.sleep(
            0.2)  # give the main loop time to fetch this item (alternatively, can we push it directly to the SM?)
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        audiostate = ''
        # TODO: wrap this shit in a function in rgbm
        if rgbm.current_audio_threadandevent is not None and rgbm.current_audio_threadandevent.t.isAlive():
            audiostate = rgbm.current_audio_threadandevent.t.filepath
        return '%s(%s)' % (callback_name, json.dumps({'state': rgbm.state, 'audiostate': audiostate}))


class WebService_StopWav_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to stop audio thread')
        if rgbm.is_audiovisualizing():
            rgbm.StopAudioVisualize()
        time.sleep(
            0.2)  # give the main loop time to fetch this item (alternatively, can we push it directly to the SM?)
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        return '%s(%s)' % (callback_name, json.dumps({'state': rgbm.state, 'audiostate': ''}))


class WebService_Test_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to stop audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        audiostate = ''
        # TODO: wrap this shit in a function in rgbm
        if rgbm.current_audio_threadandevent is not None and rgbm.current_audio_threadandevent.t.isAlive():
            audiostate = rgbm.current_audio_threadandevent.t.filepath
            newcolormap = CreateColormap(start_red=0, start_green=0, start_blue=255, end_red=255, end_green=127,
                                         end_blue=0)
            logging.info('Changed colormap on audio thread')
            rgbm.current_audio_threadandevent.t.audio.colormap = newcolormap
        return '%s(%s)' % (callback_name, json.dumps({'state': rgbm.state, 'audiostate': audiostate}))


class WebService_AudioToggleSingleLine_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to toggle singleline in audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        audiostate = ''
        # TODO: wrap this shit in a function in rgbm
        if rgbm.current_audio_threadandevent is not None and rgbm.current_audio_threadandevent.t.isAlive():
            audiostate = rgbm.current_audio_threadandevent.t.filepath
            logging.info('Toggling singleline on audio thread')
            rgbm.current_audio_threadandevent.t.audio.singleLine = not rgbm.current_audio_threadandevent.t.audio.singleLine
        return '%s(%s)' % (callback_name, json.dumps({'state': rgbm.state, 'audiostate': audiostate}))


class WebService_AudioToggleBeat_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to toggle beat in audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        audiostate = ''
        # TODO: wrap this shit in a function in rgbm
        if rgbm.current_audio_threadandevent is not None and rgbm.current_audio_threadandevent.t.isAlive():
            audiostate = rgbm.current_audio_threadandevent.t.filepath
            logging.info('Toggling beat detection on audio thread')
            rgbm.current_audio_threadandevent.t.audio.beatEnabled = not rgbm.current_audio_threadandevent.t.audio.beatEnabled
        return '%s(%s)' % (callback_name, json.dumps({'state': rgbm.state, 'audiostate': audiostate}))


class WebServiceDefinition:
    def __init__(self, url, cl, jsurl, jsname, useArg1):
        self.url = url  # path
        self.cl = cl  # class (as str)
        self.jsurl = jsurl
        self.jsname = jsname
        self.useArg1 = useArg1


class WebServiceDefinitionList(list):
    pass


class WebServiceThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global WebServiceDefinitions
        WebServiceDefinitions = WebServiceDefinitionList()
        WebServiceDefinitions.append(WebServiceDefinition(
            '/state/', 'WebService_State_JSONP', '/state/', 'wsState', False))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/playWav/(.*)', 'WebService_PlayWav_And_State_JSONP', '/playWav/', 'wsPlayWav', True))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/stopWav/', 'WebService_StopWav_And_State_JSONP', '/stopWav/', 'wsStopWav', False))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/test/', 'WebService_Test_And_State_JSONP', '/test/', 'wsTest', False))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioToggleSingleLine/', 'WebService_AudioToggleSingleLine_And_State_JSONP', '/audioToggleSingleLine/',
            'wsAudioToggleSL', False))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioToggleBeat/', 'WebService_AudioToggleBeat_And_State_JSONP', '/audioToggleBeat/', 'wsAudioToggleBeat',
            False))

    def run(self):
        urls = (
            '/definitions/', 'WebService_Definition_JSONP',
            # '/state/', 'WebService_State_JSONP',
            # '/playWav/(.*)', 'WebService_PlayWav_And_State_JSONP',
            # '/stopWav/', 'WebService_StopWav_And_State_JSONP',
            # '/test/', 'WebService_Test_And_State_JSONP',
            # '/audioToggleSingleLine/', 'WebService_AudioToggleSingleLine_And_State_JSONP',
            # '/audioToggleBeat/', 'WebService_AudioToggleBeat_And_State_JSONP',
            # '/(.*)', 'WebService_Index',
        )
        for wsdi in WebServiceDefinitions:
            urls = urls + (wsdi.url, wsdi.cl)
        urls = urls + ('/(.*)', 'WebService_Index')
        app = web.application(urls, globals())
        logging.info('Starting up WebService app')
        app.run()


# END WEBSERVICE SECTION


if __name__ == '__main__':
    InitLogging()
    logging.info('running some tests..')
    mtx = Adafruit_RGBmatrix(32, 1)

    # logging.info('test audio system')
    # a = Audio(mtx)
    # a.playwavfile('/home/pi/wav/savant_alchemist.wav')
    # mtx.Clear()
    #
    # logging.info('test clock/font system')
    # displayCurrentTime(mtx, 0, 0, 0, 127, 127)
    # time.sleep(2)
    # mtx.Clear()
    #
    # logging.info('test image system')
    # SetMatrixFromImgBase64(mtx, 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAg'+
    #     'CAYAAABzenr0AAABT0lEQVR4nO2XMY6DMBBFTZRij5Ay'+
    #     'JXQuOUaOwRG23DJH4Bh7DEo6KLfcI6QjBf6W/GdHNpGicbGvQbbHFv/j8Zhm2zZXQtd1ZYGBdV2b'+
    #     'krjTkUXfwVkbYMXzPCfj08clafeP36TtvU/ma46YO9DwHoDycd0VsbLINXXA/fwdB6eGdn+yE/U4'+
    #     'IJRDICtj5YwSP4VudsLcAZEF8ZtDKSseMisqDsV1vU/6zR1o2rbdnJN5HoEiKP9UsgLcQ/wY2kp2'+
    #     '+OCEuQPqSSjIKee4MZMtAXMH/l9A3wO5E68UrKNkQz0OoGqhBkz8whjXqiOtw/RUE1yoCfU4ALhq'+
    #     'CegsFyjzUGUZcwfEfYCZx1vS9sP3S/3Msix13AfUO2FU0n8l46hiXD21fjft8+EElANzB8qrYUC7'+
    #     'N6j3iQzmDog9AMReeBHt24N6HQBH/4oZTTkwd+AJOCiLlC/o6gAAAAAASUVORK5CYII=')
    # time.sleep(2)
    # mtx.Clear()

    # logging.info('test socket system (listen for 10 sec then end the thread)')
    # ts = ThreadState()
    # t = thread.start_new_thread(SocketListener, (mtx,ts,))
    #
    # inp = raw_input('Press <ENTER> to exit\n')
    # #time.sleep(10)
    # ts.running = False

    StateSocket(mtx)

    logging.info('exiting once all threads are done..')
