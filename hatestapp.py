#!/usr/bin/python
import logging
import json
import time
from habase import HomeAutomationQueueThread
from webservicecommon import webservice_json, WebServiceDefinition, webservice_class_instances_add,\
    ws_register_class, ws_register_definition, WSBinding, WSParam, WebService_Dynamic_Set
from hacommon import int_try_parse

dataset = [
    {'id': 1,
     'matvare': 'testmat',
     'produsent': 'tine',
     'kalorier': 10,
     'proteiner': 11,
     'karbo': 12,
     'fett': 13,
     'fiber': 14,
     'salt': 15},
    {'id': 2,
     'matvare': 'testmat 2',
     'produsent': 'tine',
     'kalorier': 10,
     'proteiner': 11,
     'karbo': 12,
     'fett': 13,
     'fiber': 14,
     'salt': 15},
    {'id': 3,
     'matvare': 'testmat 3',
     'produsent': 'tine',
     'kalorier': 10,
     'proteiner': 11,
     'karbo': 12,
     'fett': 13,
     'fiber': 14,
     'salt': 15},
    {'id': 4,
     'matvare': 'testmat 4',
     'produsent': 'tine',
     'kalorier': 10,
     'proteiner': 11,
     'karbo': 12,
     'fett': 13,
     'fiber': 14,
     'salt': 15},
    {'id': 5,
     'matvare': 'testmat 5',
     'produsent': 'tine',
     'kalorier': 10,
     'proteiner': 11,
     'karbo': 12,
     'fett': 13,
     'fiber': 14,
     'salt': 15},
]


class WebService_TestWS_SetValue(WebService_Dynamic_Set):
    def __init__(self, *args, **kwargs):
        # self.currentInstance = CurrentInstance
        super(WebService_TestWS_SetValue, self).__init__(*args, **kwargs)


# region Web methods
class martin_testws_data(object):
    @webservice_json
    def GET(self, page):
        logging.info('WebService_TestWS reading up to page ' + page)
        _page = 0
        _page = int_try_parse(page)
        ndataset = []
        for x in dataset:
            if x['id'] <= _page:
                ndataset.append(x)
        return json.dumps(ndataset)


class martin_testws_reverse_data(object):
    @webservice_json
    def GET(self, page):
        logging.info('WebService_TestWS pages past ' + page)
        _page = 0
        _page = int_try_parse(page)
        ndataset = []
        for x in dataset:
            if x['id'] >= _page:
                ndataset.append(x)
        return json.dumps(ndataset)
# endregion


@ws_register_class
class HATestApp(HomeAutomationQueueThread):
    webservice_definitions = [
        WebServiceDefinition(
            url='/martintest/(\d+)', cl='martin_testws_data', jsurl='/WebService_TestWS/', jsname='WebService_TestWS'),
        WebServiceDefinition(
            url='/martintest/reverse/(\d+)', cl='martin_testws_reverse_data', jsurl='/WebService_TestWSRev/',
            jsname='WebService_TestWSRev'),
    ]

    # region Method overrides
    def __init__(self, name, callback_function, queue, threadlist):
        webservice_class_instances_add(self.get_class_name(), self)
        self.timestopcheck = time.time()
        HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

    def pre_processqueue(self):
        super(HATestApp, self).pre_processqueue()

    def post_processqueue(self):
        # webservice_class_instances_add(self.get_class_name(), self)
        # TODO: can this be solved via a decorator?
        # threadmanager (main thread) should also keep this updated.. a good example for signals
        #if time.time() - self.timestopcheck > 15:
        #    logging.debug('crashing module for testing purposes')
        #    raise IOError('test exception')
        super(HATestApp, self).pre_processqueue()

    def get_class_name(self):
        return self.__class__.__name__
    # endregion

    """
    @ws_register_definition( WSBinding('WebService_TestWS_SetValue',
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
    def set_value(self, value):
        logging.info('Value set to: ' + value)
        return json.dumps({self.get_class_name(): {'status': 'OK'}})
    """
