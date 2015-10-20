#!/usr/bin/python
import logging, json, time, urllib2, traceback
from habase import HomeAutomationQueueThread
from hacommon import WebCache
from webservicecommon import webservice_state_instances_add, WebService_Dynamic_Set, WebService_Dynamic_Get, WSBinding, WSParam, ws_register_class, ws_register_definition
from hasettings import HA_JOINTSPACE_URI

# region Web methods
class WebService_JointSpace_Dynamic_Set(WebService_Dynamic_Set):
    def __init__(self, *args, **kwargs):
        self.currentInstance = CurrentInstance
        super(WebService_JointSpace_Dynamic_Set, self).__init__(*args, **kwargs)

class WebService_JointSpace_Dynamic_Get(WebService_Dynamic_Get):
    def __init__(self, *args, **kwargs):
        self.currentInstance = CurrentInstance
        super(WebService_JointSpace_Dynamic_Get, self).__init__(*args, **kwargs)
# endregion

@ws_register_class
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
        try:
            return json.dumps({self.get_class_name(): {
                'audio_volume=': self.get_audio_volume(),
                'system': self.get_system(),
                'ambilight_mode': self.get_ambilight_mode(),
                'ambilight_topology': self.get_ambilight_topology(),
                'sources': self.get_sources(),
                'sources_current': self.get_sources_current(),
            }})
        except:
            return json.dumps({self.get_class_name(): {'Error': str(traceback.format_exc())}})

    def pre_processqueue(self):
        logging.info('JointSpace module initialized')
        webservice_state_instances_add(self.get_class_name(), self.get_json_status)
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
    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_topology(self):
        """GET ambilight/topology"""
        return self.get_request_json('/1/ambilight/topology')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_mode(self):
        """GET ambilight/mode"""
        return self.get_request_json('/1/ambilight/mode')

    @ws_register_definition( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('current', '(\w+)')]))
    def set_ambilight_mode(self, current):
        """POST ambilight/mode
        :rtype : bool
        :param current:
        """
        return self.post_request('/1/ambilight/mode', current=current)

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_measured(self):
        """GET ambilight/measured"""
        return self.get_request_json('/1/ambilight/measured')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_processed(self):
        """GET ambilight/processed"""
        return self.get_request_json('/1/ambilight/processed')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_ambilight_cached(self):
        """GET ambilight/cached"""
        return self.get_request_json('/1/ambilight/cached')

    @ws_register_definition( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('r', '(\d+)'), WSParam('g', '(\d+)'), WSParam('b', '(\d+)')]) )
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
    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
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

    @ws_register_definition( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('muted', '(\w+)'), WSParam('current', '(\d+)')]) )
    def set_audio_volume(self, muted, current):
        """POST audio/volume"""
        return self.post_request('/1/audio/volume', muted=muted, current=current)
    # endregion

    # region Channel list methods
    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_channellists(self):
        """GET channellists"""
        return self.get_request_json('/1/channellists')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get', [WSParam('id', '(\w+)')]))
    def get_channellists_id(self, id):
        """GET channellists/id"""
        return self.get_request_json('/1/channellists/' + id)
    # endregion

    # region Channel methods
    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_channels(self):
        """GET channels"""
        return self.get_request_json('/1/channels')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_channels_current(self):
        """GET channels/current"""
        return self.get_request_json('/1/channels/current')

    @ws_register_definition( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('id', '(\w+)')]) )
    def set_channels_current(self, id):
        """POST channels/current"""
        return self.post_request('/1/channels/current', id=id)

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get', [WSParam('id', '(\w+)')]))
    def get_channels_id(self, id):
        """GET channels/id"""
        return self.get_request_json('/1/channels/' + id)
    # endregion

    # region Input methods
    @ws_register_definition( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('key', '(\w+)')]) )
    def set_input_key(self, key):
        """POST input/key"""
        return self.post_request('/1/input/key', key=key)
    # endregion

    # region Source methods
    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_sources(self):
        """GET sources"""
        return self.get_request_json('/1/sources')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_sources_current(self):
        """GET sources/current"""
        return self.get_request_json('/1/sources/current')

    @ws_register_definition( WSBinding('WebService_JointSpace_Dynamic_Set', [WSParam('id', '([\w\d]+)')]) )
    def set_sources_current(self, id):
        """POST sources/current"""
        return self.post_request('/1/sources/current', id=id)
    # endregion

    # region System methods
    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system(self):
        """GET system"""
        return self.get_request_json('/1/system')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_country(self):
        """GET system/country"""
        return self.get_request_json('/1/system/country')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_name(self):
        """GET system/name"""
        return self.get_request_json('/1/system/name')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_menulanguage(self):
        """GET system/menulanguage"""
        return self.get_request_json('/1/system/menulanguage')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_model(self):
        """GET system/model"""
        return self.get_request_json('/1/system/model')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_serialnumber(self):
        """GET system/serialnumber"""
        return self.get_request_json('/1/system/serialnumber')

    @ws_register_definition(WSBinding('WebService_JointSpace_Dynamic_Get'))
    def get_system_softwareversion(self):
        """GET system/softwareversion"""
        return self.get_request_json('/1/system/softwareversion')
    # endregion

