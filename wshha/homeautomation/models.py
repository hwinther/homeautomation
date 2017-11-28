from django.db import models
from django.utils import timezone


class LightSourceSystem(models.Model):
    name = models.TextField(max_length=64)

    def __str__(self):
        return self.name


class Light(models.Model):
    name = models.TextField(max_length=64)
    source = models.ForeignKey(LightSourceSystem)
    state = models.BooleanField(default=True)

    def __str__(self):
        return 'Light', self.name + ' - ' + str(self.state) + ' (' + self.source.name + ')'

    class Meta:
        ordering = ['name']


class HueLight(Light):
    hue = models.IntegerField(default=0)
    brightness = models.IntegerField(default=0)
    saturation = models.IntegerField(default=0)
    colormode = models.TextField(max_length=10, default='ct')
    colortemp = models.IntegerField(default=0)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)

    def __str__(self):
        return 'name=%s hue=%d brightness=%d saturation=%d colormode=%s colortemp=%d xy=(%f,%f)' % (
            self.name, self.hue, self.brightness, self.saturation, self.colormode, self.colortemp, self.x, self.y)

    def xy(self):
        return [self.x, self.y]


class TV(models.Model):
    name = models.TextField(max_length=64, default='TV')
    state = models.BooleanField(default=False)
    mute = models.BooleanField(default=False)
    volume = models.IntegerField(default=0)
    source = models.TextField(max_length=20, default='unknown')

    def __str__(self):
        return 'TV', self.name


class Action(models.Model):
    ts = models.DateTimeField(auto_now_add=True)
    activationtime = models.DateTimeField(default=timezone.now)

    def __str__(self): return 'Action registered at', self.ts, 'set to run at', self.activationtime

    class Meta:
        ordering = ['ts']


class LightAction(Action):
    light = models.ForeignKey(Light)
    state = models.BooleanField(default=True)
    hue = models.IntegerField(null=True, blank=True)
    brightness = models.IntegerField(null=True, blank=True)
    saturation = models.IntegerField(null=True, blank=True)
    # colormode  = models.TextField(10,default='ct')
    colortemp = models.IntegerField(null=True, blank=True)
    x = models.FloatField(null=True, blank=True)
    y = models.FloatField(null=True, blank=True)

    def get_type_name(self):
        try:
            return self.action_ptr.__str__()
        except:
            return 'LightAction'

    def __str__(self):
        return self.get_type_name(), 'of subtype LightAction by name', self.light.name, 'being set to state', + self.state


class TVAction(Action):
    state = models.NullBooleanField(null=True, blank=True)
    mute = models.NullBooleanField(null=True, blank=True)
    volume = models.IntegerField(null=True, blank=True)
    source = models.TextField(max_length=20, null=True, blank=True)
