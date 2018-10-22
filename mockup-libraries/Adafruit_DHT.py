class DHT11(object):
    def __init__(self):
        pass


class AM2302(DHT11):
    def __init__(self):
        DHT11.__init__(self)


class DHT22(DHT11):
    def __init__(self):
        DHT11.__init__(self)


def read(typ, pin):
    pass
