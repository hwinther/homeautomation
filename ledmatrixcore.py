#!/usr/bin/python
from habase import HomeAutomationQueueThread
from webservicecommon import webservicedecorator_globals_add, webservice_state_instances_add, webservice_class_instances_add
from rgbmatrix import Adafruit_RGBmatrix
import logging, time, sys, os, json
from transitions import Machine  # state machine
from transitions.core import MachineError
from ledmatriximage import LEDMatrixImage  # modules
from ledmatrixaudio import LEDMatrixAudio
from ledmatrixsocketservice import LEDMatrixSocketServiceUDP
from ledmatrixanimations import SplashScreen  # , ScreensaverA, CylonScan

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
        try:
            from webcli import WebCli
            wc1 = WebCli('http://pi.oh.wsh.no:8080')
            #wc1.get_request('/serialir/byte/1') #turn on
            logging.info('requesting the right audio input (via pi.oh.wsh.no)')
            # TODO: this is hardcoded..
            wc1.get_request('/HASerialIR/write_byte/2') # switch audio input
        except:
            pass
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
    # @staticmethod
    # def webservice_definitions():
    #     WebServiceDefinitions = []
    #     modules = LoadModulesFromTuple(LEDMATRIXCORE_APPS)
    #     for mod in modules:
    #         if modules[mod].cls.webservice_definitions != None:
    #             WebServiceDefinitions.extend(modules[mod].cls.webservice_definitions)
    #     return WebServiceDefinitions

    def __init__(self, name, callback_function, queue, threadlist):
        """
        This class puts it all together, creating a state machine and a socket thread that calls state changes for received commands
        """
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
        webservice_class_instances_add(self.get_class_name(), self) # might be redundant
        webservice_class_instances_add('ledmatrixaudio', self) # TODO: iterate over modules from parent and find + add those that inherit matrix
        webservice_class_instances_add('ledmatriximage', self)
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
