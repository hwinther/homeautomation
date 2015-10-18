#!/usr/bin/python
from habase import HomeAutomationQueueThread
from hacommon import WebCache
from webservicecommon import webservice_state_instances_add, WebService_Dynamic_Set, WebService_Dynamic_Get, WSBinding, WSParam, WS_class_register, WS_register
from hasettings import HA_JOINTSPACE_URI
import logging, json

import time, urllib2

# region Web methods
# class WS_JS_set_input_key(object):
#     @webservice_jsonp
#     def GET(self, key, SharedQueue, ThreadList):
#         SharedQueue.append(SerializableQueueItem(HAJointSpace.__name__, CurrentInstance.set_input_key, key))
#         return CurrentInstance.get_json_status()
#

class WebService_JointSpace_Dynamic_Set(WebService_Dynamic_Set):
    def __init__(self, *args, **kwargs):
        self.currentInstance = CurrentInstance
        super(WebService_JointSpace_Dynamic_Set, self).__init__(*args, **kwargs)

class WebService_JointSpace_Dynamic_Get(WebService_Dynamic_Get):
    def __init__(self, *args, **kwargs):
        self.currentInstance = CurrentInstance
        super(WebService_JointSpace_Dynamic_Get, self).__init__(*args, **kwargs)

# class WS_JS_dyn(object):
#     methodname = None
#     argnames = None
#
#     @webservice_jsonp
#     def GET(self, *args, **kwargs):
#         if self.argnames is None: self.argnames = []
#         if not 'SharedQueue' in kwargs.keys() or not 'ThreadList' in kwargs.keys():
#             raise Exception('Missing SharedQueue and/or ThreadList in kwargs')
#         SharedQueue = kwargs['SharedQueue']
#         # ThreadList = kwargs['ThreadList']
#         passed_kwargs = {}
#         i = 0
#         for arg in args:
#             if i > len(self.argnames):
#                 break #no more matching arg names
#             # TODO: raise exception when theres an argument mismatch?
#             argname = self.argnames[i]
#             passed_kwargs[argname] = arg
#             i += 1
#         SharedQueue.append(SerializableQueueItem(HAJointSpace.__name__, getattr(CurrentInstance, self.methodname), **passed_kwargs))
#         return CurrentInstance.get_json_status()
# endregion

@WS_class_register
class HAJointSpace(HomeAutomationQueueThread):
    # region Webservice definitions
    webservice_definitions = [
    #     WebServiceDefinition(
    #         '/jointspace/remote/(\w+)', 'WS_JS_set_input_key', '/jointspace/remote/', 'wsJSRemoteKey'),
    #     WebServiceDefinition(
    #         '/jointspace/remote/(\w+)', 'WebService_JointSpace_Dynamic_Set', '/jointspace/remote/', 'wsJSRemoteKey', 'set_input_key', ['key']),
    ]
    # webservice_register_class = 'WebService_JointSpace_Dynamic_Set'
    # endregion

    # region Method overrides
    def __init__(self, name, callback_function, queue, threadlist, baseurl=None):
        HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

        if baseurl == None:
            baseurl = HA_JOINTSPACE_URI
        self.baseurl = baseurl

        self.webcache = {}

        global CurrentInstance
        CurrentInstance = self

    def get_json_status(self):
        # TODO: add cached values for volume and other relevant things
        return json.dumps({self.get_class_name(): {
            'audio_volume=': self.get_audio_volume(),
            'system': self.get_system(),
            'ambilight_mode': self.get_ambilight_mode(),
            'ambilight_topology': self.get_ambilight_topology(),
            'sources': self.get_sources(),
            'sources_current': self.get_sources_current(),
        }})

    def pre_processqueue(self):
        logging.info('JointSpace module initialized')
        webservice_state_instances_add(self.__class__.__name__, self.get_json_status)
        self.timecheck = time.time()
        super(HAJointSpace, self).pre_processqueue()

    def post_processqueue(self):
        if time.time() - self.timecheck > 30:
            self.timecheck = time.time()
            logging.debug('30s interval')
        super(HAJointSpace, self).post_processqueue()

    def get_class_name(self):
        return self.__class__.__name__
    # endregion

    # region Generic/shared methods
    def post_request(self, method_uri, **args):
        url = self.baseurl + method_uri  # '/1/input/key'
        data = json.dumps(args)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)  # response.headers.type #'text/html'  'application/json'
        # content = response.read()  # response.getcode() #int
        return response.code == 200  # TODO: throw exception in other cases, and include errormessage from content

    def get_request(self, method_uri):
        url = self.baseurl + method_uri
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        content = response.read()
        if response.headers.type == 'application/json':
            content = json.loads(content)
        return response.code == 200, content

    def get_request_json(self, method_uri):
        url = self.baseurl + method_uri
        if url in self.webcache.keys():
            webcache = self.webcache[url]
            if (time.time() - webcache.timestamp) < (60*5):
                logging.info('returning cached data')
                return webcache.content

        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        content = response.read()
        if response.headers.type != 'application/json':
            content = '{}'
        self.webcache[url] = WebCache(url, content)
        return content
    # endregion

    # region Ambilight_methods
    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_topology(self):
        """GET ambilight/topology"""
        return self.get_request_json('/1/ambilight/topology')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_mode(self):
        """GET ambilight/mode"""
        return self.get_request_json('/1/ambilight/mode')

    @WS_register( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('current', '(\w+)')]))
    def set_ambilight_mode(self, current):
        """POST ambilight/mode
        :rtype : bool
        :param current:
        """
        return self.post_request('/1/ambilight/mode', current=current)

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_measured(self):
        """GET ambilight/measured"""
        return self.get_request_json('/1/ambilight/measured')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_processed(self):
        """GET ambilight/processed"""
        return self.get_request_json('/1/ambilight/processed')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_cached(self):
        """GET ambilight/cached"""
        return self.get_request_json('/1/ambilight/cached')

    @WS_register( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('r', '(\d+)'), WSParam('g', '(\d+)'), WSParam('b', '(\d+)')]) )
    def set_ambilight_cached(self, **kwargs):
        """POST ambilight/cached
        {
            "r": 100,
            "g": 210,
            "b": 30
        }"""
        return self.post_request('/1/ambilight/cached', **kwargs)
    # endregion

    # region Audio methods
    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_audio_volume(self):
        """GET audio/volume
        returns
        {
            "muted": false,
            "current": 18,
            "min": 0,
            "max": 60
        }"""
        return self.get_request_json('/1/audio/volume')

    @WS_register( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('muted', '(\w+)'), WSParam('current', '(\d+)')]) )
    def set_audio_volume(self, muted, current):
        """POST audio/volume"""
        return self.post_request('/1/audio/volume', muted=muted, current=current)
    # endregion

    # region Channel list methods
    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_channellists(self):
        """GET channellists"""
        return self.get_request_json('/1/channellists')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get', [WSParam('id', '(\w+)')]))
    def get_channellists_id(self, id):
        """GET channellists/id"""
        return self.get_request_json('/1/channellists/' + id)
    # endregion

    # region Channel methods
    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_channels(self):
        """GET channels"""
        return self.get_request_json('/1/channels')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_channels_current(self):
        """GET channels/current"""
        return self.get_request_json('/1/channels/current')

    @WS_register( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('id', '(\w+)')]) )
    def set_channels_current(self, id):
        """POST channels/current"""
        return self.post_request('/1/channels/current', id=id)

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get', [WSParam('id', '(\w+)')]))
    def get_channels_id(self, id):
        """GET channels/id"""
        return self.get_request_json('/1/channels/' + id)
    # endregion

    # region Input methods
    @WS_register( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('key', '(\w+)')]) )
    def set_input_key(self, key):
        """POST input/key"""
        return self.post_request('/1/input/key', key=key)
    # endregion

    # region Source methods
    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_sources(self):
        """GET sources"""
        return self.get_request_json('/1/sources')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_sources_current(self):
        """GET sources/current"""
        return self.get_request_json('/1/sources/current')

    @WS_register( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('id', '([\w\d]+)')]) )
    def set_sources_current(self, id):
        """POST sources/current"""
        return self.post_request('/1/sources/current', id=id)
    # endregion

    # region System methods
    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system(self):
        """GET system"""
        return self.get_request_json('/1/system')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_country(self):
        """GET system/country"""
        return self.get_request_json('/1/system/country')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_name(self):
        """GET system/name"""
        return self.get_request_json('/1/system/name')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_menulanguage(self):
        """GET system/menulanguage"""
        return self.get_request_json('/1/system/menulanguage')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_model(self):
        """GET system/model"""
        return self.get_request_json('/1/system/model')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_serialnumber(self):
        """GET system/serialnumber"""
        return self.get_request_json('/1/system/serialnumber')

    @WS_register(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_softwareversion(self):
        """GET system/softwareversion"""
        return self.get_request_json('/1/system/softwareversion')
    # endregion

