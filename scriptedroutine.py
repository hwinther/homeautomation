#!/usr/bin/python
import time

#self.sharedqueue.append(SerializableQueueItem('HASerialIR', 'write_byte', '1'))
#self.sharedqueue.append(SerializableQueueItem('HASerialIR', 'write_byte', '2'))

from webcli import WebCli
wc1 = WebCli('http://pi.oh.wsh.no:8080')
#wc1.get_request('/HASerialIR/write_byte/1') #turn on
print 'requesting the right audio input'
wc1.get_request('/HASerialIR/write_byte/2') #switch audio input

print 'sleep 5'
time.sleep(5) #let it start up..

wc2 = WebCli('http://rpi2.oh.wsh.no:8080')
print 'requesting awolnation sail music'
wc2.get_request('/audioPlay/awolnation_sail.wav')
