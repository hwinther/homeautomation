#!/usr/bin/python
import logging, web, json, types, traceback, copy
from habase import HomeAutomationQueueThread
from webservicecommon import WebServiceDefinition, WebServiceDefinitionList, webservice_hawebservice_init, webservice_state_jsonp

class WebService_State_JSONP(object):
    @webservice_state_jsonp
    def GET(self, **kwargs):
        jsonvalues = {}
        for key, value in kwargs.iteritems():
            # jsonvalues.append(value())
            jd = json.loads(value())
            # logging.info('jd = ' + `jd`)
            jsonvalues[jd.items()[0][0]] = jd.items()[0][1] # TODO: a nicer solution for this
        # return '[' + ', '.join(jsonvalues) + ']'
        return json.dumps(jsonvalues)

class WebService_Definition_JSONP(object):
    def GET(self):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        d = {}
        d['Definitions'] = []
        for wsdi in WebServiceDefinitions:
            d['Definitions'].append({'Name': wsdi.jsname,
                                     'URL': wsdi.jsurl,
                                     'Args': wsdi.argnames,
                                     'Enums': wsdi.jsenums,
                                     # 'Module': wsdi.cl,
                                     })
        return '%s(%s)' % (callback_name, json.dumps(d) )

class HAWebService(HomeAutomationQueueThread):
    webservice_definitions = [
            WebServiceDefinition(
                '/state/', 'WebService_State_JSONP', '/state/', 'wsState'),
                            ]

    def __init__(self, name, callback_function, queue, threadlist, modules):
        HomeAutomationQueueThread.__init__(self, name = name, callback_function = callback_function,
                                            queue = queue, threadlist = threadlist)

        global WebServiceDefinitions
        WebServiceDefinitions = WebServiceDefinitionList()

        for mod in modules:
            wsdef = modules[mod].cls.webservice_definitions

            if wsdef is not None:
                if type(wsdef) == types.FunctionType:
                    logging.debug('wsdef is function, trying to execute')
                    wsdef_addition = wsdef() # extend submodules or other dynamic collection
                    if type(wsdef_addition) == types.ListType:
                        wsdef = wsdef_addition
                elif type(wsdef) != types.ListType:
                    wsdef = []

                if hasattr(modules[mod].cls, '_webservice_definitions'):
                    # automatically created through decorator
                    wsdef_internal = getattr(modules[mod].cls, '_webservice_definitions')
                    wsdef.extend(wsdef_internal)
                    logging.info('added decorator definitions')

                WebServiceDefinitions.extend(wsdef)
                logging.debug(str(len(wsdef)) + ' definitions loaded from module ' + mod)

                for wsdi in wsdef:
                    try:
                        logging.info('wsdi ' + str(wsdi))
                        _c = getattr(modules[mod].module, wsdi.cl)
                        if wsdi.methodname is not None and wsdi.argnames is not None:
                            c = copy.deepcopy(_c) # make a copy so that the following overwrites aren't inherited on the next iter
                            wsdi.cl = wsdi.cl + '_' + wsdi.methodname # modify the class instance name reference of our copied class
                            # logging.info(wsdi.cl + ' - attaching methodname and argnames ' + wsdi.methodname)
                            # c.methodname = wsdi.methodname
                            # c.argnames = wsdi.argnames
                            globals()[wsdi.cl] = c # just a little hacky
                            # logging.info('resolved to: ' + `c`)
                        else:
                            globals()[wsdi.cl] = _c # just a little hacky
                            # logging.info('resolved to: ' + `_c`)
                    except AttributeError:
                        logging.info('Unexpected exception caught while loading WSD ' + wsdi.cl + ' from module ' + mod + ' - ' + traceback.format_exc() )

        logging.info(str(len(WebServiceDefinitions)) + ' definitions loaded.')

        global SharedQueue # deprecated?
        SharedQueue = queue

        global ThreadList
        ThreadList = threadlist

        webservice_hawebservice_init(SharedQueue=SharedQueue, ThreadList=ThreadList)

    def run(self):
        urls = (
                '/definitions/', 'WebService_Definition_JSONP',
                )
        for wsdi in WebServiceDefinitions:
            urls = urls + (wsdi.url, wsdi.cl)
            logging.info('adding url: ' + wsdi.url)
        # urls = urls + ('/(.*)', 'WebService_Index')
        # logging.info(str(urls))
        app = web.application(urls, globals())
        logging.info('Starting up WebService app')
        app.run()
