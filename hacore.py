#!/usr/bin/python
import logging, time, traceback
from hacommon import ThreadList, QueueList, load_modules_from_tuple
from hasettings import INSTALLED_APPS, REMOTE_APPS
from habase import HomeAutomationQueueThread
from hawebservice import HAWebService
from ledmatrixbase import LEDMatrixBase
from cli import LEDMatrixSocketClient


class HACore(object):
    """
    This class puts it all together,
     creating a state machine and a socket thread that calls state changes for received commands
    """

    def __init__(self):
        logging.info('HomeAutomationCore initialized')
        self.threadlist = ThreadList()
        self.sharedqueue = QueueList()

        self.modules = load_modules_from_tuple(INSTALLED_APPS)

        self.modules_key_order = []
        for key in self.modules.keys():
            if self.modules[key].cls.load_priority == 1:
                self.modules_key_order.insert(0, key)
            else:
                self.modules_key_order.append(key)

        logging.info('Loading modules: ' + ', '.join(self.modules_key_order))
        self.load_modules()

    def load_modules(self):
        logging.debug('Thread cleanup before reload')
        for _thread in self.threadlist:
            if not _thread.isAlive():
                self.threadlist.remove(_thread)

        # create threads and so on
        for mod in self.modules_key_order:
            mod_found = False
            for ti in self.threadlist:
                if mod == ti.getName():
                    mod_found = True
                    break

            if mod_found:
                continue  # no need to load it again

            logging.info('Loading module: ' + mod)
            mt = None
            if issubclass(self.modules[mod].cls, HAWebService):  # TODO: too closely coupled
                mt = self.modules[mod].cls(name=mod, callback_function=None, queue=self.sharedqueue,
                                           threadlist=self.threadlist, modules=self.modules)
            elif issubclass(self.modules[mod].cls, HomeAutomationQueueThread):
                mt = self.modules[mod].cls(name=mod, callback_function=None, queue=self.sharedqueue,
                                           threadlist=self.threadlist)
            elif issubclass(self.modules[mod].cls, LEDMatrixBase):
                pass  # leave these to be created within LEDMatrixCore
            else:  # assume its the level below (no queue)
                logging.debug('Instantiating module ' + mod)
                mt = self.modules[mod].cls(name=mod, callback_function=None)

            if mt is not None:
                if issubclass(self.modules[mod].cls, HAWebService):
                    mt.daemon = True
                self.threadlist.append(mt)

        logging.debug('Starting up module threads')
        for _thread in self.threadlist:
            if not _thread.isAlive():
                _thread.start()  # start all threads at this point - unless they are already running (reload)

    def mainloop(self):
        timecheck = time.time()
        while 1:
            # main loop that handles queue and threads, and through executing queue item changes the state
            #  of the statemachine
            try:
                for remote_module in REMOTE_APPS:
                    remote_addr = remote_module['Address']
                    remote_apps = remote_module['INSTALLED_APPS']
                    if 'socketclient' not in remote_module.keys():
                        remote_module['socketclient'] = LEDMatrixSocketClient(remote_addr)  # cache

                    for item in [i for i in self.sharedqueue if i.cls in remote_apps]:
                        logging.info('Sending queue item to remote host: ' + str(remote_module) )
                        remote_module['socketclient'].SendSerializedQueueItem(item.__str__())
                        self.sharedqueue.remove(item)
                time.sleep(0.1)

                if time.time() - timecheck > 10:
                    timecheck = time.time()
                    logging.info('10s mainloop interval, number of threads: %d (%s), queue items: %d' %
                        ( len(self.threadlist), ', '.join([str(i) for i in self.threadlist]), len(self.sharedqueue) ) )
                    for _thread in self.threadlist:
                        if not _thread.isAlive():
                            logging.info('Removing dead thread: ' + _thread.name)
                            self.threadlist.remove(_thread)
                            # TODO: call other module cleanup (e.g. remove instance ref in webservice globals)
                            # webservice_state_instances
                            # and webservice_class_instances

                    logging.info('Loading any missing modules..')
                    self.load_modules()  # reload modules if required (if one has stopped and been cleaned up)

            except KeyboardInterrupt:
                logging.info('Detected ctrl+c, exiting main loop and stopping all threads')
                break
            except:
                logging.critical("Unexpected error in main loop (exiting): " + traceback.format_exc() )
                break

        logging.debug('Stopping all threads')
        for _thread in self.threadlist:
            _thread.stop_event.set()  # telling the threads to stop
