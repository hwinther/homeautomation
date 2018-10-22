#!/usr/bin/python
# coding=utf-8
import importlib
import logging
import pickle
import time
import types


class SerializableQueueItem:
    def __init__(self, cls, func, *args, **kwargs):
        self.cls = cls  # class
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        # logging.debug('SerializableQueueItem func type: ' + str(type(self.func)) + ' callable? ' +\
        #  str(callable(self.func)))
        if type(self.func) == types.FunctionType or callable(self.func):
            self.func(*self.args, **self.kwargs)
        elif type(self.func) == types.StringType:
            logging.debug('this call needs to be processed in the main thread context before being called')
            return False

    def __str__(self):
        return pickle.dumps(self)

    @staticmethod
    def __fromstr__(data):
        return pickle.loads(data)


class ThreadList(list):
    pass


class QueueList(list):
    """
    Yes, this strictly isnt necessary due to the nature of lists in python (thread safety),
     but it still feels better being explicit like this
    """
    pass  # could potentially override the append method to only allow SerializableQueueItems


class ModuleDefinition:
    def __init__(self, mod, cls):
        self.module = mod
        self.cls = cls  # class

    def __str__(self):
        return str(self.module) + ' - ' + str(self.cls)

    def __repr__(self):
        return self.__str__()


def load_modules_from_tuple(modules):
    module_dict = {}
    for module in modules:
        modulename = module
        package = ''
        if modulename.find('.') != -1:
            package, modulename = modulename.split('.', 1)
        # print('module=%s modulenname=%s' % (module, modulename))
        mod = importlib.import_module(module.lower())
        # print('Module: %s' % repr(mod))

        # cls = getattr(mod, modulename.lower())
        cls = None
        for property_name in dir(mod):
            if property_name.lower() == modulename:
                cls = getattr(mod, property_name)
                break
        if cls is None:
            raise Exception('Could not find %s in %s' % (modulename, repr(mod)))

        logging.info('adding module=%s cls=%s' % (module, repr(cls)))
        module_dict[module] = ModuleDefinition(mod, cls)
    return module_dict


class WebCache(object):
    def __init__(self, url, content):
        self.url = url
        self.content = content
        self.timestamp = time.time()


# Borrowed from http://stackoverflow.com/questions/2262333/is-there-a-built-in-or-more-
# pythonic-way-to-try-to-parse-a-string-to-an-integer
def ignore_exception(exception=Exception, default_val=None):
    """Returns a decorator that ignores an exception raised by the function it
    decorates.

    Using it as a decorator:

      @ignore_exception(ValueError)
      def my_function():
        pass

    Using it as a function wrapper:

      int_try_parse = ignore_exception(ValueError)(int)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception:
                return default_val

        return wrapper

    return decorator


int_try_parse = ignore_exception(ValueError)(int)
