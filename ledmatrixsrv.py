#!/usr/bin/python
# coding=utf-8
from ledmatrixlib import InitLogging, Adafruit_RGBmatrix, StateSocket

InitLogging()
mtx = Adafruit_RGBmatrix(32, 1)
StateSocket(mtx)
