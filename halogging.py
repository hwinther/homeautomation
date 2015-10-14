#!/usr/bin/python
from hasettings import BASE_DIR
import logging, os

def InitLogging(filepath=None):
	if filepath == None:
		filepath = BASE_DIR + os.sep + 'ha.log'
	
	logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
	rootLogger = logging.getLogger()
	rootLogger.setLevel(logging.DEBUG)
	
	fileHandler = logging.FileHandler(filepath)
	fileHandler.setFormatter(logFormatter)
	rootLogger.addHandler(fileHandler)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(logFormatter)
	rootLogger.addHandler(consoleHandler)

def LogConcat(*args):
	sl = []
	for x in args:
		sl.append(str(x))
	return ' '.join(sl)
