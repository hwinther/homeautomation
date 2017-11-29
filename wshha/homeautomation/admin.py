from django.contrib import admin
from homeautomation.models import *


admin.site.register(LightSourceSystem)
admin.site.register(Light)
admin.site.register(HueLight)
admin.site.register(TV)

admin.site.register(Action)
admin.site.register(LightAction)
admin.site.register(TVAction)

admin.site.register(TemperatureDataPoint)
admin.site.register(Sensor)
