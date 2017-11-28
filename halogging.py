#!/usr/bin/python
from hasettings import BASE_DIR, LOGLEVEL
import logging, os


def InitLogging(filepath=None, loglevel=None):
    if filepath is None:
        print('Logging to: ' + BASE_DIR + os.sep + 'ha.log')
        filepath = BASE_DIR + os.sep + 'ha.log'
    if loglevel is None:
        loglevel = LOGLEVEL

    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(loglevel)

    file_handler = logging.FileHandler(filepath)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def LogConcat(*args):
    sl = []
    for x in args:
        sl.append(str(x))
    return ' '.join(sl)
