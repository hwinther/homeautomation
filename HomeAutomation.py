#!/usr/bin/python
from halogging import InitLogging
from hacore import HACore
# import pyreadline|readline # optional, will allow Up/Down/History in the console
import code

if __name__ == '__main__':
    InitLogging(filepath='/usr/wsh/ha.log')
    hacore = HACore()
    hacore.mainloop()
    # vars1 = globals().copy()
    # vars1.update(locals())
    # shell = code.InteractiveConsole(vars1)
    # shell.interact()
