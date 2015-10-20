#!/usr/bin/python
from habase import HomeAutomationQueueThread
from webservicecommon import webservice_state_instances_add, WebService_Dynamic_Set, WebService_Dynamic_Get, WSBinding, WSParam, ws_register_class, ws_register_definition, webservice_class_instances_add
import logging, json
import time, serial

# region Web methods
# class WebService_SerialIRSendByte(object):
#     @webservice_jsonp
#     def GET(self, byte, SharedQueue, ThreadList):
#         logging.info('WebService_SerialIRSendByte: ' + byte)
#         SharedQueue.append(SerializableQueueItem(HASerialIR.__name__, CurrentInstance.write_byte, byte))
#         return CurrentInstance.get_json_status()
class WebService_SerialIR_Dynamic_Set(WebService_Dynamic_Set):
    def __init__(self, *args, **kwargs):
        # self.currentInstance = CurrentInstance
        super(WebService_SerialIR_Dynamic_Set, self).__init__(*args, **kwargs)

class WebService_SerialIR_Dynamic_Get(WebService_Dynamic_Get):
    def __init__(self, *args, **kwargs):
        # self.currentInstance = CurrentInstance
        super(WebService_SerialIR_Dynamic_Get, self).__init__(*args, **kwargs)
# endregion

@ws_register_class
class HASerialIR(HomeAutomationQueueThread):
    webservice_definitions = [
        ]

    # region Method overrides
    def __init__(self, name, callback_function, queue, threadlist, baseurl=None):
        HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

        #if baseurl == None:
        #	baseurl = HA_JOINTSPACE_URI
        #self.baseurl = baseurl

        self.Serial = serial.Serial('/dev/ttyACM1', 9600, timeout=2)

        # global CurrentInstance
        # CurrentInstance = self

    #def run(self):
    #	super(HASerialIR, self).run()

    #def get_json_status(self):
    #	return super(HASerialIR, self).get_json_status()

    def pre_processqueue(self):
        logging.info('Serial IR module initialized: ' + self.Serial.readline() )
        webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
        webservice_class_instances_add(self.get_class_name(), self)
        self.timecheck = time.time()
        super(HASerialIR, self).pre_processqueue()

    def post_processqueue(self):
        if time.time() - self.timecheck > 30:
            self.timecheck = time.time()
            logging.debug('30s interval')
        super(HASerialIR, self).post_processqueue()

    def get_class_name(self):
        return self.__class__.__name__
    # endregion

    @ws_register_definition( WSBinding('WebService_SerialIR_Dynamic_Set',
        [WSParam('id', '(\d+)', {
                1: 'Power',
                2: 'Audio in',
                3: 'Coax',
                4: 'Aux',
                5: 'Optical',
                6: 'BT',
                7: 'Arc',
                8: 'USB',
                9: 'Bass up',
                10: 'Bass down',
    })]) )
    def write_byte(self, byte):
        b = int(byte)
        logging.info('Writing byte: ' + `chr(b)`)
        self.Serial.write(chr(b))
        readdata = str(self.Serial.readline())
        logging.info('Read: ' + readdata)
        return json.dumps({self.get_class_name(): {'read': readdata}})

    '''
      1 = 100C = power button
      2 = 1086 = audio in
      3 = 1039 = coax
      4 = 1038 = aux
      5 = 106C = optical
      6 = 1069 = BT
      7 = 1087 = arc
      8 = 107E = usb
      
      9 = 1016 = bass up
     10 = 1017 = bass down
    '''
