#!/usr/bin/python
import logging, web, types, json
from hacommon import SerializableQueueItem

# region Type definitions
class WebServiceDefinition:
    def __init__(self, url, cl, jsurl, jsname, jsenums=None, methodname=None, argnames=None):
        self.url = url # path
        self.cl = cl # class (as str)
        self.jsurl = jsurl # start URL for JS (arguments will be / separated behind this)
        self.jsname = jsname # JS bind css class name
        if jsenums == None:
            jsenums = '{}'
        self.jsenums = jsenums
        self.methodname = methodname
        if argnames == None: argnames = []
        self.argnames = argnames
    def __str__(self):
        return 'WebServiceDefinition(url=%s, cl=%s, jsurl=%s jsname=%s methodname=%s argnames=%s)' %(self.url, self.cl, self.jsurl, self.jsname, self.methodname, self.argnames)
    def __repr__(self):
        return self.__str__()

class WebServiceDefinitionList(list):
    pass

class WSBinding(object):
    def __init__(self, webservice_class, wsparameters=None):
        if type(webservice_class) == types.ClassType:
            webservice_class = webservice_class.__name__ #we only need the string representation
        self.webservice_class = webservice_class
        if wsparameters is None: wsparameters = []
        self.wsparameters = wsparameters

class WSParam(object):
    def __init__(self, arg, arg_regex, arg_enums=None):
        self.arg = arg
        self.arg_regex = arg_regex
        if arg_enums is None: arg_enums = {}
        self.arg_enums = arg_enums
    def __str__(self):
        return 'WSParam(' + self.arg + ', ' + self.arg_regex + ', ' + str(self.arg_enums) + ')'
    def __repr__(self):
        return self.__str__()
# endregion

def webservicedecorator_globals_add(**kwargs):
    global webservice_globals
    for key, value in kwargs.iteritems():
        webservice_globals[key] = value

def webservice_state_instances_add(name, inst):
    global webservice_state_instances
    webservice_state_instances[name] = inst

def webservicedecorator_init(**kwargs):
    global webservice_globals
    webservice_globals = {}
    for key, value in kwargs.iteritems():
        webservice_globals[key] = value # perhaps just clone/copy the kwargs dict directly?
    global webservice_state_instances
    webservice_state_instances = {}

def webservice_state_jsonp(f):
    def decorated(*args, **kwargs):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        for key, value in webservice_state_instances.iteritems():
            kwargs[key] = value
        return '%s(%s)' % (callback_name, f(*args, **kwargs) )
    return decorated

def webservice_json(f):
    def decorated(*args, **kwargs):
        web.header('Content-Type', 'application/javascript')
        #for key, value in webservice_globals.iteritems():
        #    kwargs[key] = value
        logging.info('webservice_state_json2 args: ' + str(args))
        logging.info('webservice_state_json2 kwargs: ' + str(kwargs.keys()))
        logging.info('webservice_state_json2 func: ' + str(dir(args[0])))
        logging.info('webservice_state_json2 class: ' + str(args[0].__class__))
        logging.info('webservice_state_json2 module: ' + str(args[0].__module__))
        return '%s' % (f(*args, **kwargs))
    return decorated

def webservice_jsonp(f):
    def decorated(*args, **kwargs):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        # kwargs['SharedQueue'] = SharedQueue #idk
        for key, value in webservice_globals.iteritems():
            kwargs[key] = value
        # logging.debug('decorated: ' + str(kwargs.keys()))
        retval = f(*args, **kwargs)
        # logging.debug('decorator got retval: ' + retval)
        return '%s(%s)' % (callback_name, retval )
    return decorated

def ws_register_class(cls):
    # logging.info('class register called: ' + cls.webservice_register_class)
    cls._webservice_definitions = []
    for methodname in dir(cls):
        method = getattr(cls, methodname)
        if hasattr(method,'_prop'): # url, cl, jsurl, jsname, methodname=None, argnames
            for wsbinding in method._prop:
                wsdi = WebServiceDefinition(
                    url = '/'+cls.__name__+'/'+methodname+'/' + '/'.join([i.arg_regex for i in wsbinding.wsparameters]),
                    cl = wsbinding.webservice_class, # cls.webservice_register_class,
                    jsurl = '/'+cls.__name__+'/'+methodname+'/',
                    jsname = 'WS_' + cls.__name__ + '_' + ''.join([i.capitalize() for i in methodname.split('_')]),
                    jsenums = [{i.arg: i.arg_enums} for i in wsbinding.wsparameters],
                    methodname = methodname,
                    argnames = [i.arg for i in wsbinding.wsparameters]
                    )
                # logging.info(wsdi)
                cls._webservice_definitions.append(wsdi)
    return cls

def ws_register_definition(*args):
    def wrapper(func):
        func._prop=args
        return func
    return wrapper

class WebService_Dynamic_Set(object):
    currentInstance = None

    @webservice_jsonp
    def GET(self, *args, **kwargs):
        if not 'SharedQueue' in kwargs.keys() or not 'ThreadList' in kwargs.keys():
            raise Exception('Missing SharedQueue and/or ThreadList in kwargs')
        SharedQueue = kwargs['SharedQueue']
        # ThreadList = kwargs['ThreadList']
        # passed_kwargs = {}
        # i = 0
        # for arg in args:
        #     if i > len(self.argnames):
        #         break # no more matching arg names
        #     # TODO: raise exception when theres an argument mismatch?
        #     logging.info('argnames: ' + str(self.argnames))
        #     argname = self.argnames[i]
        #     passed_kwargs[argname] = arg
        #     i += 1
        # from pprint import pformat
        # logging.info(pformat(web.ctx))
        # logging.info('PATH_INFO - ' + web.ctx['environ']['PATH_INFO'])
        path_parts = web.ctx['environ']['PATH_INFO'].split('/') # ['', 'HAJointSpace', 'set_input_key', 'Mute']
        if len(path_parts) >= 3:
            self.parentClass = path_parts[1]
            self.methodname = path_parts[2]
        # logging.info('Dynamic WS Set call - %s %s %s' %(self.parentClass, self.methodname, getattr(self.currentInstance, self.methodname)) )
        sqi = SerializableQueueItem(self.parentClass, getattr(self.currentInstance, self.methodname), *args)
        # logging.info('sqi args: ' + str(sqi.args) )
        SharedQueue.append(sqi) # **passed_kwargs
        return self.currentInstance.get_json_status()

class WebService_Dynamic_Get(object):
    currentInstance = None

    @webservice_jsonp
    def GET(self, *args, **kwargs):
        path_parts = web.ctx['environ']['PATH_INFO'].split('/') # ['', 'HAJointSpace', 'set_input_key', 'Mute']
        if len(path_parts) >= 3:
            self.parentClass = path_parts[1]
            self.methodname = path_parts[2]
        # logging.info('Dynamic WS Get call - %s %s %s' %(self.parentClass, self.methodname, getattr(self.currentInstance, self.methodname)) )
        return getattr(self.currentInstance, self.methodname)(*args)
