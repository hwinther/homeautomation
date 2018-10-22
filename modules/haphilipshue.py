#!/usr/bin/python
# coding=utf-8
from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add, \
    webservice_class_instances_add
from hasettings import HA_PHILIPS_HUE_BRIDGE
import logging
import json
import time
import threading
from phue import Bridge


class WebService_SetLightState(object):
    @webservice_jsonp
    def GET(self, id, state):
        _state = state.lower() == 'true'
        logging.info('WebService_SetLightState id ' + id + ' state ' + str(_state))
        self.currentInstance.queue.append(SerializableQueueItem(HAPhilipsHue.__name__,
                                                                self.currentInstance.set_light_state, id, _state))
        # time.sleep(0.5) #let the state get updated.. or just set it in cache directly?
        return '{}'  # no update.. self.currentInstance.get_json_status() #TODO: return cache + this change?


class HAPhilipsHue(HomeAutomationQueueThread):
    webservice_definitions = [
        WebServiceDefinition(
            '/philipshue/setState/([a-zA-Z0-9 ]+)/(\w+)', 'WebService_SetLightState', '/philipshue/setState/',
            'wsHueSetState'),
        ]

    # region Method overrides
    def __init__(self, name, callback_function, queue, threadlist, bridgeip=None):
        HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

        if bridgeip is None:
            bridgeip = HA_PHILIPS_HUE_BRIDGE
        self.bridgeip = bridgeip
        self.bridge = None
        self.lights = {}
        self.relevant_light_attrs = ('name', 'on', 'saturation', 'hue', 'brightness')
        self.cache = []
        self.lock = threading.Lock()
        self.timecheck = None
        self.cachetime = None

    def pre_processqueue(self):
        logging.info('Philips Hue module initialized')
        self.bridge = Bridge(self.bridgeip)
        webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
        webservice_class_instances_add(self.get_class_name(), self)
        self.update_light_instances()
        self.timecheck = time.time()
        self.update_light_cache()
        self.cachetime = time.time()
        logging.info('PhilipsHue module ready')

        super(HAPhilipsHue, self).pre_processqueue()

    def post_processqueue(self):
        if time.time() - self.timecheck > 3600:  # every hour
            self.timecheck = time.time()
            logging.info('30s interval')
            self.update_light_instances()

        if time.time() - self.cachetime > 30:  # every 30 seconds
            self.cachetime = time.time()
            self.update_light_cache()

        super(HAPhilipsHue, self).post_processqueue()

    def get_class_name(self):
        return self.__class__.__name__

    def get_json_status(self):
        return json.dumps({self.__class__.__name__: {'lights': self.cache}})
    # endregion

    def set_light_state(self, id, state):
        with self.lock:
            if id in self.lights.keys():
                light = self.lights[id]
                light.on = state
                # update cache value also
                for light in self.cache:
                    if light['name'] == id:
                        light['on'] = state
            return True

    def update_light_cache(self):
        with self.lock:
            logging.info('++ updating light status cache')
            cache = []
            for key in self.lights.keys():
                # self.cache[key] = {}
                value = self.lights[key]
                d = {}
                for attr in self.relevant_light_attrs:
                    # self.cache[key][attr] = getattr(value, attr)
                    d[attr] = getattr(value, attr)
                cache.append(d)
        self.cache = cache
        logging.info('-- updating light status cache')

    def update_light_instances(self):
        with self.lock:
            logging.info('++ updating light instances')
            namesfound = []
            added, removed = 0, 0
            for l in self.bridge.lights:
                if l.name not in namesfound:
                    namesfound.append(l.name)
                if l.name not in self.lights.keys():
                    self.lights[l.name] = l
                    added += 1
            for name in self.lights.keys():
                if name not in namesfound:
                    self.lights.pop(name, None)
                    removed += 1
            if added != 0 or removed != 0:
                logging.info('Added ' + str(added) + ' lights and removed ' + str(removed))
            logging.info('-- updating light instances')
