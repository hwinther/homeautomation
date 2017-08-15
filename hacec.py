#!/usr/bin/python
import logging, json, time, os
from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add, WebService_Dynamic_Get, WebService_Dynamic_Set, webservice_class_instances_add, WSBinding, WSParam, ws_register_class, ws_register_definition


# region Web methods
class WebService_Cec_Dynamic_Set(WebService_Dynamic_Set):
    def __init__(self, *args, **kwargs):
        # self.currentInstance = CurrentInstance
        super(WebService_Cec_Dynamic_Set, self).__init__(*args, **kwargs)


class WebService_Cec_Dynamic_Get(WebService_Dynamic_Get):
    def __init__(self, *args, **kwargs):
        # self.currentInstance = CurrentInstance
        super(WebService_Cec_Dynamic_Get, self).__init__(*args, **kwargs)


class WebService_CecPowerOn(object):
    @webservice_jsonp
    def GET(self, id):
        _id = 0
        try:
            _id = int(id)
        except ValueError:
            pass
        if 1:
            logging.info('Cec power on: ' + id)
            self.currentInstance.queue.append(SerializableQueueItem(HACec.__name__, self.currentInstance.cec_client_power_on, _id)) #:\
        return self.currentInstance.get_json_status()


class WebService_CecStandby(object):
    @webservice_jsonp
    def GET(self, id):
        _id = 0
        try:
            _id = int(id)
        except ValueError:
            pass
        if 1:
            logging.info('Cec power on: ' + id)
            self.currentInstance.queue.append(SerializableQueueItem(HACec.__name__, self.currentInstance.cec_client_standby, _id))
        return self.currentInstance.get_json_status()


class WebService_CecOsdText(object):
    @webservice_jsonp
    def GET(self, id, text):
        _id = 0
        try:
            _id = int(id)
        except ValueError:
            pass
        logging.info('Cec set osd text on dev ' + id + ': ' + text)
        self.currentInstance.queue.append(SerializableQueueItem(HACec.__name__, self.currentInstance.cec_client_osd, _id, text))
        return self.currentInstance.get_json_status()
# endregion


class HACec(HomeAutomationQueueThread):
    webservice_definitions = [
        WebServiceDefinition(
            '/cec/power_on/(\d+)', 'WebService_CecPowerOn', '/cec/power_on/', 'wsCecPowerOn'),
        WebServiceDefinition(
            '/cec/standby/(\d+)', 'WebService_CecStandby', '/cec/standby/', 'wsCecStandby'),
        WebServiceDefinition(
            '/cec/osdtext/(\d+)/(\w+)', 'WebService_CecOsdText', '/cec/osdtext/', 'wsCecOsdText'),
        ]

    # region Method overrides
    def __init__(self, name, callback_function, queue, threadlist):
        HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

        self.devices = []

        # global CurrentInstance
        # CurrentInstance = self

    def get_json_status(self):
        cecdevices = []
        for x in self.devices:
            powerstatus='Unknown'
            try:
                powerstatus = self.devices[x].is_on()
            except:
                pass
            cecdevices.append( {'Name':self.devices[x].osd_string, 'PowerStatus':powerstatus} )
        return json.dumps({self.get_class_name(): { 'cecdevices': cecdevices } })

    def pre_processqueue(self):
        logging.info('CEC module initialized')
        webservice_state_instances_add(self.get_class_name(), self.get_json_status)
        webservice_class_instances_add(self.get_class_name(), self)
        self.updatedevices()
        self.timecheck = time.time()
        super(HACec, self).pre_processqueue()

    def post_processqueue(self):
        if time.time() - self.timecheck > 30:
            self.timecheck = time.time()
            logging.debug('30s interval')
            self.updatedevices()
        super(HACec, self).post_processqueue()

    def get_class_name(self):
        return self.__class__.__name__
    # endregion

    def cec_client_power_on(self, id):
        logging.debug('Power on: ' + str(id))
        cmd='(echo on ' + str(id) + '; echo q) | cec-client -d 7 -s'
        os.system(cmd)

    def cec_client_standby(self, id):
        logging.debug('Standby: ' + str(id))
        os.system('(echo standby ' + str(id) + '; echo q) | cec-client -d 7 -s')

    def cec_client_osd(self, id, txt):
        rng = range(ord('A'), ord('z')) #only allow a-z and space
        rng.append(ord(' '))
        txt = ''.join([i for i in txt if ord(i) in rng])
        logging.debug('OSD text: ' + txt)
        os.system('(echo osd ' + str(id) + ' ' + txt + '; echo q) | cec-client -d 7 -s')

    def updatedevices(self):
        pass
        #logging.debug('Updating device list')
        #import cec
        #cec.init()
        #self.devices = cec.list_devices()
        #del(cec)
        #d[0].osd_string
