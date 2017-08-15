#!/usr/bin/python
from ledmatrixbase import LEDMatrixBase
import logging
import web
import json
import os
import time
import base64
from hacommon import SerializableQueueItem
from ledmatrixcolor import CreateColormap


class WebService_Index(object):
    def GET(self, name):
        if not name:
            name = 'world'
        return 'Hello, ' + name + '!' + '<br><br>' + `globals()`


class WebService_Definition_JSONP(object):
    def GET(self):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        d = {}
        d['Definitions'] = []
        for wsdi in WebServiceDefinitions:
            d['Definitions'].append({'Name': wsdi.jsname, 'URL': wsdi.jsurl})
        return '%s(%s)' % (callback_name, json.dumps(d))


class WebService_State_JSONP(object):
    def GET(self):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_PlayWav_And_State_JSONP(object):
    def GET(self, filename):
        if not filename:
            logging.warn('WebService_PlayWav_And_State_JSONP missing filename argument')
            return 'WebService_PlayWav_And_State_JSONP missing filename argument'  # this will in turn cause an exception in JS.. desired? IDK
        filepath = '/home/pi/wav/' + filename  # TODO: get this path from config
        if not os.path.exists(filepath):
            logging.info('WebService_PlayWav_And_State_JSONP File path does not exist: ' + filepath)
            return 'WebService_PlayWav_And_State_JSONP File path does not exist: ' + filepath
            # if rgbm.is_audiovisualizing(): #not sure if this will work properly - it did not, we got idle state with music playing
        #	rgbm.StopAudioVisualize()
        logging.info('WebService_PlayWav_And_State_JSONP Playing wav file with audio visualizer:' + filepath)
        queue.append(SerializableQueueItem(rgbm.AudioVisualize, filepath))
        time.sleep(0.2)  # give the main loop time to fetch this item (alternatively, can we push it directly to the SM?)
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioStop_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to stop audio thread')
        if rgbm.is_audiovisualizing():
            rgbm.StopAudioVisualize()
        time.sleep(0.2)  # give the main loop time to fetch this item (alternatively, can we push it directly to the SM?)
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioTest_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to test something in the audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
            new_freq_step = int(rgbm.current_audio_thread.freq_step * 0.9)
            logging.info('Setting audio thread freq_step to ' + str(new_freq_step) + ' making max freq ' + str(new_freq_step * 31))
            rgbm.current_audio_thread.freq_step = new_freq_step
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioSetMaxFreq_And_State_JSONP(object):
    def GET(self, freqmax):
        if not freqmax:
            logging.warn('WebService_AudioSetMaxFreq_And_State_JSONP missing freqmax argument')
            return 'WebService_AudioSetMaxFreq_And_State_JSONP missing freqmax argument'
        logging.info('Attempting to change freqmax for audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
            new_freq_step = int(int(freqmax) / 32.0)  # TODO: get this from screen width config value
            logging.info('Setting audio thread freqmax to ' + str(freqmax) + ' making freq_step ' + str(new_freq_step))
            rgbm.current_audio_thread.freq_step = new_freq_step
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioToggleSingleLine_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to toggle singleline in audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
            logging.info('Toggling singleline on audio thread')
            rgbm.current_audio_thread.singleLine = not rgbm.current_audio_thread.singleLine
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioToggleBeat_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to toggle beat in audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
            logging.info('Toggling beat detection on audio thread')
            rgbm.current_audio_thread.beatEnabled = not rgbm.current_audio_thread.beatEnabled
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioPause_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to pause audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
            logging.info('Pausing audio thread')
            rgbm.current_audio_thread.paused = True
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioResume_And_State_JSONP(object):
    def GET(self):
        logging.info('Attempting to resume audio thread')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
            logging.info('Resuming audio thread')
            rgbm.current_audio_thread.paused = False
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_AudioSetColormap_And_State_JSONP(object):
    def GET(self, jsondatab64):
        if not jsondatab64:
            logging.warn('WebService_AudioSetColormap_And_State_JSONP missing jsondatab64 argument')
            return 'WebService_AudioSetColormap_And_State_JSONP missing jsondatab64 argument'
        logging.info('Attempting to set color map from json data')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        if rgbm.current_audio_thread != None and rgbm.current_audio_thread.isAlive():
            jsondata = base64.decodestring(jsondatab64)
            jd = json.loads(jsondata)
            newcolormap = CreateColormap(num_steps=jd['num_steps'],
                                         start_red=jd['start_red'], start_green=jd['start_green'], start_blue=jd['start_blue'],
                                         end_red=jd['end_red'], end_green=jd['end_green'], end_blue=jd['end_blue'])
            logging.info('Changed colormap on audio thread')
            rgbm.current_audio_thread.colormap = newcolormap
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebService_ImageSetBase64Data_And_State_JSONP(object):
    def GET(self, imageb64data):
        if not imageb64data:
            logging.warn('WebService_ImageSetBase64Data_And_State_JSONP missing imageb64data argument')
            return 'WebService_ImageSetBase64Data_And_State_JSONP missing imageb64data argument'  # this will in turn cause an exception in JS.. desired? IDK

        logging.info('Attempting to set image from base64 data')
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        queue.append(SerializableQueueItem(rgbm.SetMatrixFromImgBase64, imageb64data))
        return '%s(%s)' % (callback_name, rgbm.get_json_state())


class WebServiceDefinition:
    def __init__(self, url, cl, jsurl, jsname):
        self.url = url  # path
        self.cl = cl  # class (as str)
        self.jsurl = jsurl  # start URL for JS (arguments will be / separated behind this)
        self.jsname = jsname  # JS bind css class name


class WebServiceDefinitionList(list):
    pass


class LEDMatrixWebService(LEDMatrixBase):
    def __init__(self, name, callback_function, rgbmatrix, g_rgbm, g_queue):
        LEDMatrixBase.__init__(self, name=name, callback_function=None, rgbmatrix=rgbmatrix)

        global WebServiceDefinitions
        WebServiceDefinitions = WebServiceDefinitionList()

        WebServiceDefinitions.append(WebServiceDefinition(
            '/state/', 'WebService_State_JSONP', '/state/', 'wsState'))

        # TODO: iterate over settings module list and load urls from each of those, then append them like this

        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioPlay/(.*)', 'WebService_PlayWav_And_State_JSONP', '/audioPlay/', 'wsAudioPlay'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioStop/', 'WebService_AudioStop_And_State_JSONP', '/audioStop/', 'wsAudioStop'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioTest/', 'WebService_AudioTest_And_State_JSONP', '/audioTest/', 'wsAudioTest'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioToggleSingleLine/', 'WebService_AudioToggleSingleLine_And_State_JSONP', '/audioToggleSingleLine/', 'wsAudioToggleSL'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioToggleBeat/', 'WebService_AudioToggleBeat_And_State_JSONP', '/audioToggleBeat/', 'wsAudioToggleBeat'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioPause/', 'WebService_AudioPause_And_State_JSONP', '/audioPause/', 'wsAudioPause'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioResume/', 'WebService_AudioResume_And_State_JSONP', '/audioResume/', 'wsAudioResume'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioSetColormap/(.*)', 'WebService_AudioSetColormap_And_State_JSONP', '/audioSetColormap/', 'wsAudioSetColormap'))
        WebServiceDefinitions.append(WebServiceDefinition(
            '/audioSetMaxFreq/(.*)', 'WebService_AudioSetMaxFreq_And_State_JSONP', '/audioSetMaxFreq/', 'wsAudioSetMaxFreq'))

        WebServiceDefinitions.append(WebServiceDefinition(
            '/ImageSetBase64Data/(.*)', 'WebService_ImageSetBase64Data_And_State_JSONP', '/ImageSetBase64Data/', 'wsImageSetBase64Data'))

        global rgbm
        rgbm = g_rgbm

        global queue
        queue = g_queue

    def run(self):
        urls = (
            '/definitions/', 'WebService_Definition_JSONP',
        )
        for wsdi in WebServiceDefinitions:
            urls = urls + (wsdi.url, wsdi.cl)
        urls = urls + ('/(.*)', 'WebService_Index')
        app = web.application(urls, globals())
        logging.info('Starting up WebService app')
        app.run()
