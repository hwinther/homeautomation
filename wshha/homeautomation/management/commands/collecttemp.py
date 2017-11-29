from django.core.management import BaseCommand
from homeautomation.models import TemperatureDataPoint, Sensor
import random
import time
import homeautomation.lanot.sensor01client as sensor01client
import homeautomation.lanot.sensor02client as sensor02client
import homeautomation.lanot.nodetestclient as nodetestclient


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #    parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        sen01, created = Sensor.objects.get_or_create(name='sensor01')
        sensor01 = sensor01client.Sensor01UdpClient('sensor01.iot.oh.wsh.no', bind_port=9230)
        sensor01_value = sensor01.dht11.value()
        print('sensor01 dht11 %s' % repr(sensor01_value))
        #
        if sensor01_value is not None and sensor01_value.find('c') != -1:
            t, h = sensor01_value.split('c', 2)
            TemperatureDataPoint(temperature=int(t), humidity=int(h), sensor=sen01).save()
        #
        sen02, created = Sensor.objects.get_or_create(name='sensor02')
        sensor02 = sensor02client.Sensor02UdpClient('sensor02.iot.oh.wsh.no', bind_port=9232)
        sensor02_value = sensor02.dht11.value()
        print('sensor02 dht11 %s' % repr(sensor02_value))
        #
        if sensor02_value is not None and sensor02_value.find('c') != -1:
            t, h = sensor02_value.split('c', 2)
            TemperatureDataPoint(temperature=int(t), humidity=int(h), sensor=sen02).save()
        #
        # nt, created = Sensor.objects.get_or_create(name='nodetest')
        # nodetest = nodetestclient.NodeTestUdpClient('nodetest.iot.oh.wsh.no', bind_port=9231)
        # print(nodetest.red_led.on())
        # nodetest_value = nodetest.dht11.value()
        # print('nodetest dht11 %s' % repr(nodetest_value))
        # print(nodetest.red_led.off())

        # if nodetest_value is not None and nodetest_value.find('c') != -1:
        #     t, h = nodetest_value.split('c', 2)
        #     TemperatureDataPoint(temperature=int(t), humidity=int(h), sensor=nt).save()
