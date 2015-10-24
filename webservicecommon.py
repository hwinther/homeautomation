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
            jsenums = {}
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
    """
    This decorator helper method will change the incoming parameters for all modules in an instance and is thus deprecated
    It is not a decorator per se but shares global namespace with it and is thus able to append to its global variable
    :param kwargs:
    :return:
    """
    global webservice_globals
    for key, value in kwargs.iteritems():
        webservice_globals[key] = value

def webservice_state_instances_add(name, inst):
    """
    Module registration for the state decorator (helps webservice thread know which modules are relevant for the overall system state output)
    :param name:
    :param inst:
    :return:
    """
    global webservice_state_instances
    webservice_state_instances[name] = inst

def webservice_class_instances_add(classname, classinstance):
    """
    Module registration to be done by the modules themselves after init
    This is required to use the shared web methods WebService_Dynamic_Set & WebService_Dynamic_Get as callbacks
    At runtime it will be passed on to the decorated GET call
    :param name:
    :param inst:
    :return:
    """
    global webservice_module_class_instances
    webservice_module_class_instances[classname.lower()] = classinstance

def webservice_hawebservice_init(**kwargs):
    """
    Initializer & shorthand helper for webservice class similar to webservice_state_instances_add
    Registers "common" global variables SharedQueue and ThreadList - now deprecated to decopule/unconfuse application flow and variable sharing in general
    :param kwargs:
    :return:
    """
    global webservice_globals # now deprecated
    webservice_globals = {}
    for key, value in kwargs.iteritems():
        webservice_globals[key] = value # perhaps just clone/copy the kwargs dict directly?
    global webservice_state_instances
    webservice_state_instances = {}
    global webservice_module_class_instances
    webservice_module_class_instances = {}

def webservice_state_jsonp(f):
    """
    Decorator for the module overall state (this will be polled by a browser to update all component states in the view)
    :param f:
    :return:
    """
    def decorated(*args, **kwargs):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        for key, value in webservice_state_instances.iteritems():
            kwargs[key] = value
        return '%s(%s)' % (callback_name, f(*args, **kwargs) )
    return decorated

def webservice_json(f):
    """
    decorator for GET methods in webservice classes
    :param f:
    :return: json
    """
    def decorated(*args, **kwargs):
        web.header('Content-Type', 'application/javascript')
        decorator = args[0]
        modulename = decorator.__module__

        if modulename in webservice_module_class_instances.keys():
            decorator.currentInstance = webservice_module_class_instances[modulename]
        else:
            logging.warn('No class instance reference found for ' + modulename)
            decorator.currentInstance = None

        retval = f(*args, **kwargs)
        return '%s' % (retval)
    return decorated

def webservice_jsonp(f):
    """
    decorator for GET methods in webservice classes (jsonp variant - cross site)
    :param f:
    :return: jsonp
    """
    def decorated(*args, **kwargs):
        callback_name = web.input(callback='jsonCallback').callback
        web.header('Content-Type', 'application/javascript')
        # shortcut? call above decorator to get returned data and format it with %s(%s) after.. data = webservice_json(f)
        decorator = args[0]
        modulename = decorator.__module__

        # global webservice_module_class_instances
        if modulename in webservice_module_class_instances.keys():
            decorator.currentInstance = webservice_module_class_instances[modulename]
        else:
            logging.warn('No class instance reference found for ' + modulename)
            decorator.currentInstance = None

        retval = f(*args, **kwargs)
        return '%s(%s)' % (callback_name, retval)
    return decorated

def ws_register_class(cls):
    # logging.info('class register called: ' + cls.webservice_register_class)
    cls._webservice_definitions = []
    for methodname in dir(cls):
        method = getattr(cls, methodname)
        if hasattr(method,'_prop'): # url, cl, jsurl, jsname, methodname=None, argnames
            for wsbinding in method._prop:
                jsenums = {}
                for p in wsbinding.wsparameters:
                    jsenums[p.arg] = p.arg_enums

                wsdi = WebServiceDefinition(
                    url = '/'+cls.__name__+'/'+methodname+'/' + '/'.join([i.arg_regex for i in wsbinding.wsparameters]),
                    cl = wsbinding.webservice_class, # cls.webservice_register_class,
                    jsurl = '/'+cls.__name__+'/'+methodname+'/',
                    jsname = 'WS_' + cls.__name__ + '_' + ''.join([i.capitalize() for i in methodname.split('_')]),
                    jsenums = jsenums, # [{i.arg: i.arg_enums} for i in wsbinding.wsparameters],
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
        path_parts = web.ctx['environ']['PATH_INFO'].split('/') # ['', 'HAJointSpace', 'set_input_key', 'Mute']
        if len(path_parts) >= 3:
            self.parentClass = path_parts[1]
            self.methodname = path_parts[2]
        # logging.info('Dynamic WS Set call - %s %s %s' %(self.parentClass, self.methodname, getattr(self.currentInstance, self.methodname)) )
        # SharedQueue.append(sqi) TODO: this is no longer happening at all
        if hasattr(self.currentInstance, 'queue'):
            logging.info('adding action to queue for ' + self.parentClass)
            sqi = SerializableQueueItem(self.parentClass, getattr(self.currentInstance, self.methodname), *args)
            self.currentInstance.queue.append(sqi)
        else:
            logging.info('exec action directly for ' + self.parentClass)
            getattr(self.currentInstance, self.methodname)(*args)
        return self.currentInstance.get_json_status()
        # return state as it was before action is likely to have taken place.. may not be that useful

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
