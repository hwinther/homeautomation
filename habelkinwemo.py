#!/usr/bin/python
# coding=utf-8
import json
import logging
import threading
import time

from ouimeaux.environment import Environment

from habase import HomeAutomationQueueThread
from hacommon import SerializableQueueItem
from webservicecommon import WebServiceDefinition, webservice_jsonp, webservice_state_instances_add, \
    webservice_class_instances_add

__author__ = 'Hans Christian'
__version__ = '0.1'


class WebService_HABelkinWemoSetLightState(object):
    @webservice_jsonp
    def GET(self, id, state):
        _state = state.lower() == 'true'
        logging.info('WebService_SetLightState id ' + id + ' state ' + str(_state))
        self.currentInstance.queue.append(SerializableQueueItem(HABelkinWemo.__name__,
                                                                self.currentInstance.set_light_state, id, _state))
        # time.sleep(0.5) #let the state get updated.. or just set it in cache directly?
        return '{}'  # no update.. self.currentInstance.get_json_status() #TODO: return cache + this change?


class HABelkinWemo(HomeAutomationQueueThread):
    webservice_definitions = [
        WebServiceDefinition(
            '/HABelkinWemo/setState/([a-zA-Z0-9 ]+)/(\w+)', 'WebService_HABelkinWemoSetLightState',
            '/HABelkinWemo/setState/', 'wsHueSetState'),
    ]

    # region Method overrides
    def __init__(self, name, callback_function, queue, threadlist):
        HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

        self.env = Environment()
        self.lights = {}
        self.relevant_light_attrs = ('name', 'on', 'saturation', 'hue', 'brightness')
        self.cache = []
        self.lock = threading.Lock()
        self.timecheck = None
        self.cachetime = None

    def pre_processqueue(self):
        logging.info('Belkin Wemo module initialized')
        self.env.start()
        self.env.discover(10)
        webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
        webservice_class_instances_add(self.get_class_name(), self)
        self.update_light_instances()
        self.timecheck = time.time()
        self.update_light_cache()
        self.cachetime = time.time()
        logging.info('Belkin Wemo module ready')

        super(HABelkinWemo, self).pre_processqueue()

    def post_processqueue(self):
        if time.time() - self.timecheck > 3600:  # every hour
            self.timecheck = time.time()
            logging.info('30s interval')
            self.update_light_instances()

        if time.time() - self.cachetime > 30:  # every 30 seconds
            self.cachetime = time.time()
            self.update_light_cache()

        super(HABelkinWemo, self).post_processqueue()

    def get_class_name(self):
        return self.__class__.__name__

    def get_json_status(self):
        return json.dumps({self.__class__.__name__: {'lights': self.cache}})

    # endregion

    def set_light_state(self, id, state):
        with self.lock:
            if id in self.lights.keys():
                l = self.lights[id]
                l.set_state(state)
                # update cache value also
                for l in self.cache:
                    if l['Name'] == id:
                        l['State'] = state
            return True

    def update_light_cache(self):
        with self.lock:
            logging.info('++ updating light status cache')
            cache = []
            for key, value in self.lights.iteritems():
                # self.cache[key] = {}
                d = dict()
                d['Name'] = key
                d['State'] = value.get_state()
                # for attr in self.relevant_light_attrs:
                #    #self.cache[key][attr] = getattr(value, attr)
                #    d[attr] = getattr(value, attr)
                cache.append(d)
        self.cache = cache
        logging.info('-- updating light status cache')

    def update_light_instances(self):
        with self.lock:
            logging.info('++ updating light instances')
            namesfound = []
            added, removed = 0, 0
            for switchname in self.env.list_switches():
                logging.info('found switch with name: ' + switchname)
                if switchname not in namesfound:
                    namesfound.append(switchname)
                if switchname not in self.lights.keys():
                    self.lights[switchname] = self.env.get_switch(switchname)
                    added += 1
            for name in self.lights.keys():
                if name not in namesfound:
                    self.lights.pop(name, None)
                    removed += 1
            if added != 0 or removed != 0:
                logging.info('Added ' + str(added) + ' lights and removed ' + str(removed))
            logging.info('-- updating light instances')
