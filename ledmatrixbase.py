#!/usr/bin/python
# coding=utf-8
from habase import HomeAutomationThread


class LEDMatrixBase(HomeAutomationThread):
    def __init__(self, name, callback_function, rgbmatrix):
        HomeAutomationThread.__init__(self, name, callback_function)

        self.rgbmatrix = rgbmatrix
