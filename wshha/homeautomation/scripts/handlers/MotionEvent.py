from django.utils import timezone

#wemo switches++
from ouimeaux.environment import Environment
from ouimeaux.utils import matcher
from ouimeaux.signals import receiver, statechange, devicefound

class Sensor:
	def __init__(self, m, t, s):
		self.Matcher = m
		self.Trigger = t
		self.state = s

def Handler(triggers, running):
	print 'MotionEvent] handler thread started'
	sensors=[]
	for trigger in triggers:
		sensor=Sensor(matcher(trigger.source),trigger,False)
		sensors.append(sensor)
	
	@receiver(devicefound)
	def found(sender, **kwargs):
		for sensor in sensors:
			if sensor.Matcher(sender.name):
				print "MotionEvent] Found device:", sender.name
				break

	@receiver(statechange)
	def motion(sender, **kwargs):
		for sensor in sensors:
			if sensor.Matcher(sender.name):
				#print "{} state is {state}".format(
				#	sender.name, state="on" if kwargs.get('state') else "off")
				if kwargs.get('state'):
					if sensor.state == False:
						sensor.state = True
						#trigger onActivation events
						for action in sensor.Trigger.onActivation:
							action.run()
					else:
						pass #repeat activation
				else: #state false
					if sensor.state == True:
						sensor.state = False
						#trigger onDeactivation events
						for action in sensor.Trigger.onDeactivation:
							action.run()
					else:
						#repeat off state
						pass
				break #stop iterating through matchers for this event

	#start up wemo env, mainloop until thread aborted		
	env = Environment()
	#try:
	env.start()
	env.discover(5)
	env.wait()
	#except:
	#	pass
