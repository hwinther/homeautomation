#!/usr/bin/python
import os, sys, time, socket, base64

SPLITCHARS = '\x01\x02\x03\x04'  # default value


class LEDMatrixSocketClient:
    def __init__(self, srv_addr, splitchars=None):
        self.srv_addr = srv_addr
        if splitchars == None:
            self.splitchars = SPLITCHARS
        else:
            self.splitchars = splitchars
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def Clear(self):
        self.sock.sendto(self.splitchars + chr(126) + self.splitchars, self.srv_addr)

    def SetPixel(self, x, y, r, g, b):
        self.sock.sendto(self.splitchars + chr(127) + chr(x) + chr(y) + chr(r) + chr(g) + chr(b) + self.splitchars, self.srv_addr)

    def SetImageB64(self, imageb64data):
        self.sock.sendto(self.splitchars + chr(128) + imageb64data + self.splitchars, self.srv_addr)

    def PlayWav(self, filename):
        self.sock.sendto(self.splitchars + chr(129) + filename + self.splitchars, self.srv_addr)

    def StopWav(self):
        self.sock.sendto(self.splitchars + chr(130) + self.splitchars, self.srv_addr)

    def SendSerializedQueueItem(self, itemstr):
        self.sock.sendto(self.splitchars + chr(131) + itemstr + self.splitchars, self.srv_addr)


"""
print 'sending 0,0,255,255,255'
s.sendto(SPLITCHARS+chr(127)+chr(0)+chr(0)+chr(255)+chr(255)+chr(255)+SPLITCHARS, srv_addr)

#print 'sending jpeg file', sys.argv[1]
#jpegdata = open(sys.argv[1], 'rb').read()
#jpegb64 = base64.encodestring(jpegdata)
jpegb64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABT0lEQVR4nO2XMY6DMBBFTZRij5Ay'+\
'JXQuOUaOwRG23DJH4Bh7DEo6KLfcI6QjBf6W/GdHNpGicbGvQbbHFv/j8Zhm2zZXQtd1ZYGBdV2b'+\
'krjTkUXfwVkbYMXzPCfj08clafeP36TtvU/ma46YO9DwHoDycd0VsbLINXXA/fwdB6eGdn+yE/U4'+\
'IJRDICtj5YwSP4VudsLcAZEF8ZtDKSseMisqDsV1vU/6zR1o2rbdnJN5HoEiKP9UsgLcQ/wY2kp2'+\
'+OCEuQPqSSjIKee4MZMtAXMH/l9A3wO5E68UrKNkQz0OoGqhBkz8whjXqiOtw/RUE1yoCfU4ALhq'+\
'CegsFyjzUGUZcwfEfYCZx1vS9sP3S/3Msix13AfUO2FU0n8l46hiXD21fjft8+EElANzB8qrYUC7'+\
'N6j3iQzmDog9AMReeBHt24N6HQBH/4oZTTkwd+AJOCiLlC/o6gAAAAAASUVORK5CYII='
data = SPLITCHARS+chr(128)+jpegb64+SPLITCHARS
print 'packet length', len(data)
s.sendto(data, srv_addr)

time.sleep(2)

for x in range(0,32):
	s.sendto(SPLITCHARS+chr(127)+chr(x)+chr(0)+chr(255)+chr(255)+chr(0)+SPLITCHARS, srv_addr)
	time.sleep(0.2)

s.sendto(SPLITCHARS+chr(129)+'pegboard_nerds_coffins.wav'+SPLITCHARS, srv_addr)
"""

if __name__ == '__main__':
    print 'running test routines..'
    imgb64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABT0lEQVR4nO2XMY6DMBBFTZRij5Ay' + \
             'JXQuOUaOwRG23DJH4Bh7DEo6KLfcI6QjBf6W/GdHNpGicbGvQbbHFv/j8Zhm2zZXQtd1ZYGBdV2b' + \
             'krjTkUXfwVkbYMXzPCfj08clafeP36TtvU/ma46YO9DwHoDycd0VsbLINXXA/fwdB6eGdn+yE/U4' + \
             'IJRDICtj5YwSP4VudsLcAZEF8ZtDKSseMisqDsV1vU/6zR1o2rbdnJN5HoEiKP9UsgLcQ/wY2kp2' + \
             '+OCEuQPqSSjIKee4MZMtAXMH/l9A3wO5E68UrKNkQz0OoGqhBkz8whjXqiOtw/RUE1yoCfU4ALhq' + \
             'CegsFyjzUGUZcwfEfYCZx1vS9sP3S/3Msix13AfUO2FU0n8l46hiXD21fjft8+EElANzB8qrYUC7' + \
             'N6j3iQzmDog9AMReeBHt24N6HQBH/4oZTTkwd+AJOCiLlC/o6gAAAAAASUVORK5CYII='

    srv_addr = ('127.0.0.1', 5111)
    c = LEDMatrixSocketClient(srv_addr)
    c.SetPixel(0, 0, 255, 255, 255)
    time.sleep(2)
    c.Clear()
    time.sleep(2)
    c.SetImageB64(imgb64)
    time.sleep(2)
    c.PlayWav('pegboard_nerds_coffins.wav')
