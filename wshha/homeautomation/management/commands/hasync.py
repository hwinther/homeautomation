from django.core.management.base import BaseCommand, CommandError
from homeautomation.models import *
import time, random, datetime, threading, os, sys
from django.utils import timezone

# wemo switches++
import ouimeaux
from ouimeaux.environment import Environment

# philips hue
from phue import Bridge


def LightStatusUpdate(b):
    lights = b.get_light_objects('name')
    for _light in lights:
        x = lights[_light]
        # print x.name
        try:
            l = Light.objects.get(name=x.name)
        except:
            l = None
        if l == None:
            print 'creating new hue db obj', x.name
            l = HueLight(name=x.name, source=LightSourceSystem.objects.get(name='hue'), state=x.on, hue=x.hue, brightness=x.brightness, x=x.xy[0], y=x.xy[1])
            # colormode=x.colormode
            # colortemp=x.colortemp
            l.save()
        else:
            # print 'updating hue db obj', x.name
            l.state = x.on
            l.hue = x.hue
            l.brightness = x.brightness
            # l.colormode=x.colormode
            # l.colortemp=x.colortemp
            l.x = x.xy[0]
            l.y = x.xy[1]
            l.save()

    return lights


def createWemoSwitches(env):
    for dev in env.list_switches():
        try:
            l = Light.objects.get(name=dev)
            print 'Found known wemo switch: ' + dev
        except:
            l = None
            print 'Creating missing switch: ' + dev
        if l == None:
            l = Light(name=dev, source=LightSourceSystem.objects.get(name='wemo'), state=False)
            l.save()


def wemo_updatelight(la, env):
    try:
        sw = env.get_switch(la.light.name)
    except:
        sw = None
    if sw != None:
        sw.set_state(la.state)
        print timezone.now(), 'set ' + la.light.name + ' to state', la.state
        la.light.state = la.state
        la.light.save()


def hue_updatelight(la, lights):
    if la.light.name in lights.keys():
        light = lights[la.light.name]
        light.on = la.state

        if la.hue != None and la.saturation != None and la.brightness != None:
            light.hue = la.hue
            light.saturation = la.saturation
            light.brightness = la.brightness
            print timezone.now(), 'set ' + la.light.name + ' to state', la.state, 'hue', la.hue, 'saturation', la.saturation, 'brightness', la.brightness
        elif la.x != None and la.y != None:
            light.xy = (la.x, la.y)
            print timezone.now(), 'set ' + la.light.name + ' to state', la.state, 'x', la.x, 'y', la.y
        else:
            print timezone.now(), 'set ' + la.light.name + ' to state', la.state
        la.light.state = la.state
        la.light.save()


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #    parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        print 'init start'
        b, lights, env = self.init()
        print 'init end, mainloop'
        while 1:
            try:
                self.mainloop(b, lights, env)
            except:
                print "Unexpected error:", sys.exc_info()[0]
            time.sleep(5)

    def init(self):
        print '\nstarting up hue environment..'
        b = Bridge('192.168.1.2')
        print 'detected hue devices:'
        lights = LightStatusUpdate(b)
        print '\nstarting up wemo environment..'
        env = Environment()
        env.start()
        env.discover(5)
        print 'detected wemo devices:'
        createWemoSwitches(env)
        i = 0
        for x in LightAction.objects.all():
            x.delete()
            i += 1
        print 'deleted %d old LightAction object' % (i)
        return [b, lights, env]

    def mainloop(self, b, lights, env):
        threads = []
        lastruntime = timezone.now()
        while 1:
            for la in LightAction.objects.filter(activationtime__lte=timezone.now()):
                if la.light.source.name == 'wemo':
                    # print 'starting wemo thread'
                    t = threading.Thread(target=wemo_updatelight, args=(la, env,))
                    t.start()
                    threads.append(t)
                elif la.light.source.name == 'hue':
                    # print 'starting hue thread'
                    t = threading.Thread(target=hue_updatelight, args=(la, lights,))
                    t.start()
                    threads.append(t)
                la.delete()
            if (timezone.now() - lastruntime).seconds > 30:
                # time for status update on lights
                # print 'refreshing light status..',
                lights = LightStatusUpdate(b)
                # print 'done'
                lastruntime = timezone.now()
            time.sleep(0.2)
