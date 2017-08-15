#!/usr/bin/python
from ledmatrixbase import LEDMatrixBase
import logging

import socket, select, time, os, sys, threading
from hacommon import QueueList, SerializableQueueItem, SerializableQueueItem

SOCKET_SPLITCHARS = '\x01\x02\x03\x04'  # needs to be set on both client and server side, used to determine the beginning and end of commands
# TODO: the above and below should be fetched from config
SOCKET_UDP_LISTEN_ADDR = ('0.0.0.0', 5111)


class SocketCommand:
    def __init__(self, command, addr):
        self.command = command
        self.addr = addr


class SocketCommandThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.setName('SocketCommand')
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            if len(self.parent.cmdqueue) == 0:
                time.sleep(0.2)
                continue
            for item in self.parent.cmdqueue:
                self.process(item)
                self.parent.cmdqueue.remove(item)

    def process(self, item):
        '''Socket command handler that blocks while perfroming rgbmatrix actions'''
        # set pixel command: 127 X Y R G B
        #				    0   1 2 3 4 5
        cmd = item.command
        addr = item.addr

        if len(cmd) == 0: return  # must be invalid
        datacmd = cmd[0]
        dataarg = ''
        if len(cmd) > 1:
            dataarg = cmd[1:]
        logging.debug('handling cmd ' + str(ord(datacmd)) + ' [' + str(dataarg) + '] for ' + str(addr))
        if ord(datacmd) == 126:
            logging.info('Clearing screen')
            self.parent.queue.append(SerializableQueueItem(self.parent.__class__.__name__, self.parent.rgbm.Clear))
        elif ord(datacmd) == 127 and len(cmd) == 6:
            x, y, r, g, b = ord(dataarg[0]), ord(dataarg[1]), ord(dataarg[2]), ord(dataarg[3]), ord(dataarg[4])
            logging.info('Setting matrix pixel at x=' + str(x) + ' y=' + str(y) + ' to color r=' + str(r) + ',g=' + str(g) + ',b=' + str(b))
            self.parent.queue.append(SerializableQueueItem(self.parent.__class__.__name__, self.parent.rgbm.SetPixel, x, y, r, g, b))
        elif ord(datacmd) == 128:
            logging.info('Displaying image')
            self.parent.queue.append(SerializableQueueItem(self.parent.__class__.__name__, self.parent.rgbm.SetMatrixFromImgBase64, dataarg))
        elif ord(datacmd) == 129:
            filepath = '/home/pi/wav/' + dataarg
            if not os.path.exists(filepath):
                logging.info('(Play wav) File does not exist: ' + filepath)
                return
            logging.info('Playing wav file with audio visualizer:' + filepath)
            self.parent.queue.append(SerializableQueueItem(self.parent.__class__.__name__, self.parent.rgbm.AudioVisualize, filepath))
        elif ord(datacmd) == 130:
            # stop playing wav file
            logging.info('Attempting to stop audio thread')
            # self.queue.append(SerializableQueueItem(self.rgbm.StopAudioVisualize)) #will not work because the queuehandler is waiting for is_idle
            if self.parent.rgbm.is_audiovisualizing():
                self.parent.rgbm.StopAudioVisualize()
        elif ord(datacmd) == 131:
            # remote queue item transfer
            logging.info('Attempting to translate received queue item into a reference')
            open('/tmp/remotecmddata.txt', 'w').write(dataarg)
            queueitem = SerializableQueueItem.__fromstr__(dataarg)
            self.parent.queue.append(queueitem)
        else:
            logging.warn('Unknown command, not doing anything')


class LEDMatrixSocketServiceUDP(LEDMatrixBase):
    def __init__(self, name, callback_function, rgbmatrix, rgbm, queue):
        LEDMatrixBase.__init__(self, name=name, callback_function=callback_function, rgbmatrix=rgbmatrix)
        self.rgbm = rgbm
        self.queue = queue
        self.bufferdict = {}  # dictionary that keeps each clients buffer when the received data becomes segmented
        self.cmdqueue = QueueList()
        self.queuethread = None

    def run(self):  # TODO: wrap most of this in a try with logging and maybe thread shutdown on exceptions
        self.queuethread = SocketCommandThread(self)
        # self.queuethread.daemon = True
        self.queuethread.start()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # for tcp set option to reuse
        self.sock.bind(SOCKET_UDP_LISTEN_ADDR)
        logging.info('SocketServiceUDP listening on ' + str(SOCKET_UDP_LISTEN_ADDR))
        self.sock.setblocking(0)
        while not self.stop_event.is_set():
            ready = select.select([self.sock], [], [], 1)
            if ready[0]:
                data, addr = self.sock.recvfrom(1024 * 16)
                self.bufferhandler(data, addr)

        if self.queuethread != None and self.queuethread.isAlive():
            self.queuethread.stop_event.set()
        LEDMatrixBase.finalize(self)

    def bufferhandler(self, d, a):
        '''Handles your socket buffers and shit, yo'''
        if not a in self.bufferdict.keys(): self.bufferdict[a] = ''
        buff = self.bufferdict[a] + d
        l = buff.split(SOCKET_SPLITCHARS)
        if len(l) == 0: return
        if l[-1] == '':  # complete data
            for x in l:
                if x == '': continue
                self.cmdqueue.append(SocketCommand(x, a))
                self.bufferdict[a] = ''  # clear buffer just to be sure
        else:
            for x in l[:-1]:
                if x == '': continue
                self.cmdqueue.append(SocketCommand(x, a))
            self.bufferdict[a] = l[-1]  # last data added back to buffer
