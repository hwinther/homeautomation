#!/usr/bin/python
import logging, json
from habase import HomeAutomationQueueThread
from webservicecommon import webservice_json, WebServiceDefinition, webservice_class_instances_add

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

# region Web methods
class martin_testws_data(object):
    @webservice_json
    def GET(self, page):
        logging.info('WebService_TestWS reading up to page ' + page)
        _page = 0
        try:
            _page = int(page)
        except:
            pass
        ndataset = []
        for x in dataset:
            if x['id'] <= _page:
                ndataset.append(x)
        return json.dumps(ndataset)
# endregion

class HATestApp(HomeAutomationQueueThread):
    webservice_definitions = [
        WebServiceDefinition(
            url='/martintest/(\d+)', cl='martin_testws_data', jsurl='/WebService_TestWS/', jsname='WebService_TestWS'),
        ]

    # region Method overrides
    def __init__(self, name, callback_function, queue, threadlist):
        HomeAutomationQueueThread.__init__(self, name, callback_function, queue, threadlist)

    def post_processqueue(self):
        webservice_class_instances_add(self.get_class_name(), self)
        # TODO: can this be solved via a decorator?
        # threadmanager (main thread) should also keep this updated.. a good example for signals
        # super(HATestApp, self).pre_processqueue()

    def get_class_name(self):
        return self.__class__.__name__
    # endregion
