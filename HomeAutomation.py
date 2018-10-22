#!/usr/bin/python
# coding=utf-8
from hacore import HACore
from halogging import InitLogging

# import pyreadline|readline # optional, will allow Up/Down/History in the console

if __name__ == '__main__':
    InitLogging(filepath='/usr/wsh/ha.log')
    hacore = HACore()
    hacore.mainloop()
    # vars1 = globals().copy()
    # vars1.update(locals())
    # shell = code.InteractiveConsole(vars1)
    # shell.interact()
