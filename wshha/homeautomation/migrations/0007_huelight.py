# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0006_delete_huelight'),
    ]

    operations = [
        migrations.CreateModel(
            name='HueLight',
            fields=[
                ('light_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='homeautomation.Light')),
                ('hue', models.IntegerField(default=0)),
                ('brightness', models.IntegerField(default=0)),
                ('saturation', models.IntegerField(default=0)),
                ('colormode', models.TextField(default=b'ct', verbose_name=10)),
                ('colortemp', models.IntegerField(default=0)),
                ('x', models.FloatField(default=0)),
                ('y', models.FloatField(default=0)),
            ],
            bases=('homeautomation.light',),
        ),
    ]
