from django.core.management.base import BaseCommand, CommandError
from homeautomation.models import *
import time, random, datetime
from django.utils import timezone

# wemo switches++
from ouimeaux.environment import Environment
from ouimeaux.utils import matcher
from ouimeaux.signals import receiver, statechange, devicefound

lingertime = 30


def TurnOnLights(lights):
    print '!! turning on lights..'
    for light in lights:
        LightAction(light=Light.objects.get(name=light), state=True).save()


def SetOrExtendTurnOff(lights):
    print '!! updating light off timers'
    futuretime = timezone.now() + datetime.timedelta(0, lingertime)
    print futuretime, timezone.now()
    for light in lights:
        qs = LightAction.objects.filter(light=Light.objects.get(name=light), state=False)
        if len(qs) == 0:
            # create a new timed action one minute from now
            la = LightAction(light=Light.objects.get(name=light), state=False)
            la.activationtime = futuretime
            la.save()
        elif len(qs) == 1:
            print 'extending timer..'
            # update the existing timed action
            qs[0].activationtime = futuretime
            qs[0].save()
        else:
            # nuke all but one?
            for q in qs:
                q.delete()
            LightAction(light=Light.objects.get(name=light), state=False, activationtime=futuretime).save()


def mainloop():
    matchers = [matcher('anteroom sensor'), matcher('kitchen sensor'), matcher('bedroom sensor')]
    states = [False, False, False]

    @receiver(devicefound)
    def found(sender, **kwargs):
        for matcher in matchers:
            if matcher(sender.name):
                print "Found device:", sender.name

    @receiver(statechange)
    def motion(sender, **kwargs):
        for matcher in matchers:
            if matcher(sender.name):
                # print "{} state is {state}".format(
                #      sender.name, state="on" if kwargs.get('state') else "off")
                if kwargs.get('state'):
                    if sender.name == 'anteroom sensor':
                        if states[0] == False:
                            # first detection, turn on lights and time turn off one minute from now
                            TurnOnLights(['Anteroom', 'Extended color light 1'])
                            SetOrExtendTurnOff(['Anteroom', 'Extended color light 1'])
                            states[0] = True
                        else:
                            # later detections, extend turn off timer
                            SetOrExtendTurnOff(['Anteroom', 'Extended color light 1'])
                    elif sender.name == 'kitchen sensor':
                        if states[1] == False:
                            # first detection, turn on lights and time turn off one minute from now
                            TurnOnLights(['Kitchen 1', 'Kitchen 2'])
                            SetOrExtendTurnOff(['Kitchen 1', 'Kitchen 2'])
                            states[1] = True
                        else:
                            # later detections, extend turn off timer
                            SetOrExtendTurnOff(['Kitchen 1', 'Kitchen 2'])
                    elif sender.name == 'bedroom sensor':
                        if states[2] == False:
                            # first detection, turn on lights and time turn off one minute from now
                            TurnOnLights(['Bedroom spot 1', 'Bedroom spot 2', 'Bedroom spot 3', 'Bedroom spot 4'])
                            SetOrExtendTurnOff(['Bedroom spot 1', 'Bedroom spot 2', 'Bedroom spot 3', 'Bedroom spot 4'])
                            states[2] = True
                        else:
                            # later detections, extend turn off timer
                            SetOrExtendTurnOff(['Bedroom spot 1', 'Bedroom spot 2', 'Bedroom spot 3', 'Bedroom spot 4'])
                else:  # sensor-off
                    if sender.name == 'anteroom sensor':
                        states[0] = False
                    elif sender.name == 'kitchen sensor':
                        states[1] = False
                    elif sender.name == 'bedroom sensor':
                        states[2] = False

    env = Environment()
    try:
        env.start()
        env.discover(5)
        env.wait()
    except (KeyboardInterrupt, SystemExit):
        print "Goodbye!"


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #    parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        print '\nstarting up wemo environment..'
        mainloop()
