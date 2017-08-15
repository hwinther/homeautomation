#!/usr/bin/python
from habase import HomeAutomationThread
import logging, threading


class LEDMatrixBase(HomeAutomationThread):
    def __init__(self, name, callback_function, rgbmatrix):
        HomeAutomationThread.__init__(self, name, callback_function)

        self.rgbmatrix = rgbmatrix
