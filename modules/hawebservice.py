#!/usr/bin/python
# coding=utf-8
import logging
import web
import json
import types
import traceback
import copy
from habase import HomeAutomationQueueThread
from webservicecommon import WebServiceDefinition, WebServiceDefinitionList, webservice_hawebservice_init, \
    webservice_state_jsonp


class WebService_State_JSONP(object):
    @webservice_state_jsonp
    def GET(self, **kwargs):
        jsonvalues = {}
        for key in kwargs:
            # jsonvalues.append(value())
            value = kwargs[key]
            jd = json.loads(value())
            # logging.info('jd = ' + `jd`)
            jsonvalues[jd.items()[0][0]] = jd.items()[0][1]  # TODO: a nicer solution for this
        # return '[' + ', '.join(jsonvalues) + ']'
        return json.dumps(jsonvalues)


class WebService_Schema_JSONP(object):
    def GET(self):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        d = dict()
        d['Schema'] = []
        for wsdi in WebServiceDefinitions:
            d['Schema'].append({'Name': wsdi.jsname,
                                     'URL': wsdi.jsurl,
                                     'Args': wsdi.argnames,
                                     'Enums': wsdi.jsenums,
                                     # 'Module': wsdi.cl,
                                     })
        return '%s(%s)' % (callback_name, json.dumps(d))


class HAWebService(HomeAutomationQueueThread):
    webservice_definitions = [
        WebServiceDefinition(
            '/state/', 'WebService_State_JSONP', '/state/', 'wsState'),
    ]
    load_priority = 1

    def __init__(self, name, callback_function, queue, threadlist, modules):
        global SharedQueue  # deprecated?
        SharedQueue = queue

        global ThreadList
        ThreadList = threadlist

        self.modules = modules

        HomeAutomationQueueThread.__init__(self, name=name, callback_function=callback_function,
                                           queue=queue, threadlist=threadlist)

        self.load_ws_definitions()

    def load_ws_definitions(self):
        global WebServiceDefinitions
        WebServiceDefinitions = WebServiceDefinitionList()

        # for x in self.threadlist:
        #     print 'thread name: ' + x.getName()

        for mod in self.modules:
            wsdef = self.modules[mod].cls.webservice_definitions

            if wsdef is not None:
                if type(wsdef) == types.FunctionType:
                    logging.debug('wsdef is function, trying to execute')
                    wsdef_addition = wsdef()  # extend submodules or other dynamic collection
                    if type(wsdef_addition) == types.ListType:
                        wsdef = wsdef_addition
                elif type(wsdef) != types.ListType:
                    wsdef = []

                wsdef = list(wsdef)  # make a copy (as this is really a class constant and we dont want leakage)

                if hasattr(self.modules[mod].cls, '_webservice_definitions'):
                    # automatically created through decorator
                    wsdef_internal = getattr(self.modules[mod].cls, '_webservice_definitions')
                    if len(wsdef_internal) != 0:
                        wsdef.extend(wsdef_internal)
                        logging.info('added decorator definitions')

                if mod.find('.') != -1:
                    modulename, instancename = mod.split('.', 1)

                    # make urls into instance format
                    for wsd in wsdef:
                        logging.warn('wsd.url was: %s' % wsd.url)
                        # wsd.url = '/' + modulename + '/' + instancename + wsd.url

                WebServiceDefinitions.extend(wsdef)
                logging.debug(str(len(wsdef)) + ' definitions loaded from module ' + mod)

                for wsdi in wsdef:
                    try:
                        logging.info('wsdi ' + str(wsdi))
                        _c = getattr(self.modules[mod].module, wsdi.cl)
                        if wsdi.methodname is not None and wsdi.argnames is not None:
                            # make a copy so that the following overwrites aren't inherited on the next iter
                            c = copy.deepcopy(_c)
                            # modify the class instance name reference of our copied class
                            wsdi.cl = wsdi.cl + '_' + wsdi.methodname
                            # logging.info(wsdi.cl + ' - attaching methodname and argnames ' + wsdi.methodname)
                            # c.methodname = wsdi.methodname
                            # c.argnames = wsdi.argnames
                            globals()[wsdi.cl] = c  # just a little hacky
                            logging.info('resolved to: %s' % repr(c))
                        else:
                            globals()[wsdi.cl] = _c  # just a little hacky
                            logging.info('resolved to: %s' % repr(_c))
                    except AttributeError:
                        logging.info('Unexpected exception caught while loading WSD ' + wsdi.cl + ' from module ' +
                                     mod + ' - ' + traceback.format_exc())

        logging.info(str(len(WebServiceDefinitions)) + ' definitions loaded.')

        webservice_hawebservice_init(SharedQueue=self.queue, ThreadList=self.threadlist)

    def run(self):
        urls = (
            '/schema/', 'WebService_Schema_JSONP',
        )
        for wsdi in WebServiceDefinitions:
            urls = urls + (wsdi.url, wsdi.cl)
            logging.info('adding url: %s cl: %s' % (wsdi.url, wsdi.cl))
        # urls = urls + ('/(.*)', 'WebService_Index')
        # logging.info(str(urls))
        # print(globals())
        app = web.application(urls, globals())
        logging.info('Starting up WebService app')
        app.run()
