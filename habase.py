#!/usr/bin/python
import logging, threading, time, json
from hacommon import QueueList, ThreadList

class HomeAutomationThread(threading.Thread):
    webservice_definitions = None

    def __init__(self, name, callback_function):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.setName(name)
        self.callback_function = callback_function

    def finalize(self):
        if self.callback_function != None:
            self.callback_function()

    def get_json_status(self):
        return json.dumps({self.get_class_name(): []})

    def get_class_name(self):
        return self.__class__.__name__

class HomeAutomationQueueThread(HomeAutomationThread):
    def __init__(self, name, callback_function, queue, threadlist):
        HomeAutomationThread.__init__(self, name, callback_function)
        if queue == None: queue = QueueList()
        self.queue = queue
        if threadlist == None: threadlist = ThreadList()
        self.threadlist = threadlist

    def pre_processqueue(self): #Have the subclasses override processqueue and call super afterwards to get the same effect
        pass #bad naming, before processing queue items at all
 
    def processqueue(self):
        self.pre_processqueue()
        clsname = self.get_class_name()
        while not self.stop_event.is_set():
            for item in [i for i in self.queue if i.cls == clsname]:
                #TODO: should really be True.. but this will be used until the modules return the right default value via decorator
                #logging.debug('Exec queue item: ' + `item`)
                item_return_value = self.exec_item(item)
                #logging.debug('Exec queue item ret: ' + `item_return_value`)
                if item_return_value == None or item_return_value == True:
                    self.queue.remove(item)
                elif item_return_value == False:
                    pass #handle this again later
                else:
                    #try to translate the str in item into a function call within this context
                    logging.debug('attempting to translate function call in deserialized queue item: ' + item.func)
                    res = self
                    for x in item.func.split('.'):
                        res = getattr(res, x)
                    logging.debug('res = ' + str(res))
                    item.func = res #let it be handled on the next iteration..
            self.post_processqueue()

            time.sleep(0.1)
        self.finalize()

    def run(self):
        self.processqueue()

    def post_processqueue(self):
        pass

    def get_class_name(self):
        return self.__class__.__name__

    def exec_item(self, item):
        return item()
