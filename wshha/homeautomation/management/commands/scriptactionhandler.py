from django.core.management.base import BaseCommand, CommandError
from homeautomation.models import *

import time, random, datetime, os, threading, re
from django.utils import timezone
from xml.dom import minidom


class ScriptAction:
    def __init__(self, n, d):
        self.name = n
        self.description = d
        self.Triggers = []
        self.Actions = []

    def __str__(self):
        return 'ScriptAction ' + self.name + ' with ' + str(len(self.Triggers)) + ' triggers and ' + str(len(self.Actions)) + ' actions.'


class Trigger:
    def __init__(self, t, s, oa, od):
        self.type = t
        self.source = s
        self.onActivation = oa
        self.onDeactivation = od


class Action:
    def __init__(self, n, ss, s, st, w, m):
        self.name = n
        self.sourcesystem = ss
        self.source = s
        self.state = st
        self.when = w
        self.modifier = m

    def run(self):
        print 'Activating action', str(self)
        for s in self.source:
            when_time = timezone.now()  # + datetime.timedelta(0,0)
            if self.when == 'now':
                pass
            elif self.when[0] == '+':
                when_time = timezone.now() + parse_time(self.when[1:])
            elif self.when[0] == '-':
                when_time = timezone.now() - parse_time(self.when[1:])
            elif self.when.lower() == 'any':
                pass
            else:
                raise IOError('When value not valid ' + str(self.when) + ' (this really should\'ve been handled earlier in the process)')

            if self.modifier == None or self.modifier == '' or self.modifier == 'none' or self.modifier == 'add':
                LightAction(light=s, state=self.state, activationtime=when_time).save()
                print 'Creating lightaction with state', self.state
            elif self.modifier.lower() == 'delete':
                qs = LightAction.objects.filter(light=s, state=self.state)
                for q in qs:
                    q.delete()
                    print 'Deleting record'

    def __str__(self):
        sources = ''
        for s in self.source:
            sources += str(s) + ', '
        return 'Action name=%s sourcesystem=%s source=%s state=%s when=%s modifier=%s' % (
        self.name, self.sourcesystem, sources, self.state, self.when, self.modifier)


def ParseAndValidateTriggerActions(value, Actions):
    resultset = []
    for act_str in value.split(', '):
        found = False
        for act in Actions:
            if act.name == act_str:
                resultset.append(act)
                print 'found and attached Action: ' + act_str
                found = True
                break
        if found == False:
            print 'could not find Action ' + act_str
    return resultset


def ParseAllScriptActions():
    ScriptActions = []
    scriptpath = '/usr/wsh/pi.oh.wsh.no_websites/pi.oh.wsh.no/wshha/homeautomation/scripts'
    for xmlfilename in os.listdir(scriptpath):
        if not xmlfilename.endswith('.xml'): continue

        xmlfilepath = scriptpath + '/' + xmlfilename
        print 'parsing ' + xmlfilename
        xmldoc = minidom.parse(xmlfilepath)
        for scriptaction in xmldoc.getElementsByTagName('ScriptAction'):
            name = ''
            description = ''
            if 'name' in scriptaction.attributes.keys(): name = scriptaction.attributes['name'].value
            if 'description' in scriptaction.attributes.keys(): description = scriptaction.attributes['description'].value
            _scriptaction = ScriptAction(name, description)
            ScriptActions.append(_scriptaction)

            for action in scriptaction.getElementsByTagName('Action'):
                # <Action name="clearBedroomLightsDeactivation" sourcesystem="hue" source="Bedroom spot 1, Bedroom spot 2, Bedroom spot3, Bedroom spot 4" state="False" when="any" modifier="delete" />
                name = ''
                sourcesystem = None
                source = None
                state = None
                when = None
                modifier = None
                if 'name' in action.attributes.keys(): name = action.attributes['name'].value
                if 'sourcesystem' in action.attributes.keys():
                    # sourcesystem = action.attributes['sourcesystem'].value
                    try:
                        sourcesystem = LightSourceSystem.objects.get(name=action.attributes['sourcesystem'].value)
                    except:
                        raise IOError('LightSourceSystem with the name ' + action.attributes['sourcesystem'].value + ' does not exist.')
                    # print sourcesystem
                if 'source' in action.attributes.keys():
                    # source = action.attributes['source'].value
                    source = []
                    for _source in action.attributes['source'].value.split(', '):
                        try:
                            if sourcesystem.name == 'hue':
                                source.append(HueLight.objects.get(name=_source))
                            elif sourcesystem.name == 'wemo':
                                source.append(Light.objects.get(name=_source))
                            else:
                                raise IOError('Unhandled sourcesystem: ' + sourcesystem.name)
                        except IOError as e:
                            raise
                        except:
                            raise IOError('Source ' + _source + ' was not found.')
                        # print source
                if 'state' in action.attributes.keys():
                    # state = action.attributes['state'].value
                    if action.attributes['state'].value.lower() == 'true':
                        state = True
                    else:
                        state = False
                if 'when' in action.attributes.keys(): when = action.attributes['when'].value
                if 'modifier' in action.attributes.keys(): modifier = action.attributes['modifier'].value
                _action = Action(name, sourcesystem, source, state, when, modifier)
                _scriptaction.Actions.append(_action)

            for trigger in scriptaction.getElementsByTagName('Trigger'):
                # type="MotionEvent" source="bedroom sensor" onActivation="turnOnBedroomLights, clearBedroomLightsDeactivation" onDeactivation="setBedroomLightsDeactivationTimer"
                type = None
                source = None
                onActivation = []
                onDeactivation = []
                if 'type' in trigger.attributes.keys(): type = trigger.attributes['type'].value
                if 'source' in trigger.attributes.keys(): source = trigger.attributes['source'].value
                if 'onActivation' in trigger.attributes.keys():
                    # onActivation = trigger.attributes['onActivation'].value
                    onActivation = ParseAndValidateTriggerActions(trigger.attributes['onActivation'].value, _scriptaction.Actions)
                if 'onDeactivation' in trigger.attributes.keys():
                    # onDeactivation = trigger.attributes['onDeactivation'].value
                    onDeactivation = ParseAndValidateTriggerActions(trigger.attributes['onDeactivation'].value, _scriptaction.Actions)
                _trigger = Trigger(type, source, onActivation, onDeactivation)
                _scriptaction.Triggers.append(_trigger)

    return ScriptActions


def loadModules():
    res = {}
    handlerPath = '/usr/wsh/pi.oh.wsh.no_websites/pi.oh.wsh.no/wshha/homeautomation/scripts/handlers'
    # check subfolders
    lst = os.listdir(handlerPath)
    dir = []
    for d in lst:
        s = handlerPath + os.sep + d
        # print s
        if d.endswith('.py') and not d.endswith('__init__.py') and os.path.exists(s):
            dir.append(d)
    # load the modules
    for d in dir:
        d = d.replace('.py', '')
        # print 'importing module', d
        res[d] = __import__("homeautomation.scripts.handlers." + d, fromlist=["*"])
    return res


regex = re.compile(r'((?P<hours>\d+?)hr)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')


def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)
    return datetime.timedelta(**time_params)


class ThreadRunning:
    def __init__(self):
        self.running = True


class WorkerThread:
    def __init__(self, name, threadrunning, thread):
        self.name = name
        self.threadrunning = threadrunning
        self.thread = thread


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    # def add_arguments(self, parser):
    #    parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        # print '\nstarting up wemo environment..'
        sa_set = ParseAllScriptActions()
        _triggersByType = {}
        for sa in sa_set:
            for trigger in sa.Triggers:
                if not trigger.type in _triggersByType.keys(): _triggersByType[trigger.type] = []
                _triggersByType[trigger.type].append(trigger)

        mods = loadModules()
        print 'Modules loaded:', mods.keys()

        workerthreads = []

        for triggerType in _triggersByType.keys():
            if triggerType in mods.keys():
                # start new worker thread with the available triggers
                tr = ThreadRunning()
                t = threading.Thread(target=mods[triggerType].Handler, args=(_triggersByType[triggerType], tr,))
                workerthreads.append(WorkerThread(triggerType, tr, t))
                print 'starting up thread of type', triggerType, 'with', len(_triggersByType[triggerType]), 'triggers attached.'
                t.start()  # start the thread

        print 'presumably do other things in main thread after this..'
        x = raw_input('\nCtrl+C to stop app')
