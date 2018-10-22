PCM_PLAYBACK = 0
PCM_NORMAL = 1
PCM_FORMAT_S16_LE = 2


class PCM(object):
    def __init__(self, readwrite_option, unknown_option):
        pass

    def setchannels(self, channels):
        pass

    def setrate(self, rate):
        pass

    def setformat(self, fmt):
        pass

    def setperiodsize(self, chunk):
        pass

    def write(self, data):
        pass
