#!/usr/bin/python
import pickle, importlib, types, logging, time


class SerializableQueueItem:
    def __init__(self, cls, func, *args, **kwargs):
        self.cls = cls  # class
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        # logging.debug('SerializableQueueItem func type: ' + str(type(self.func)) + ' callable? ' + str(callable(self.func)))
        if type(self.func) == types.FunctionType or callable(self.func):
            self.func(*self.args, **self.kwargs)
        elif type(self.func) == types.StringType:
            logging.debug('this call needs to be processed in the main thread context before being called')
            return False

    def __str__(self):
        return pickle.dumps(self)

    @staticmethod
    def __fromstr__(str):
        return pickle.loads(str)


class ThreadList(list):
    pass


class QueueList(list):
    '''Yes, this strictly isnt necessary due to the nature of lists in python (thread safety), but it still feels better being explicit like this'''
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
        instancename = ''
        if modulename.find('.') != -1:
            modulename, instancename = modulename.split('.', 1)
        mod = importlib.import_module(modulename.lower())
        cls = getattr(mod, modulename)
        modulekey = modulename
        if instancename is not '':
            modulekey += '.' + instancename
        module_dict[modulekey] = ModuleDefinition(mod, cls)
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

    def decorator(function):
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except exception:
                return default_val

        return wrapper

    return decorator

int_try_parse = ignore_exception(ValueError)(int)
