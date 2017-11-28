# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0004_auto_20150827_1937'),
    ]

    operations = [
        migrations.CreateModel(
            name='HueLight',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hue', models.IntegerField(default=0)),
                ('brightness', models.IntegerField(default=0)),
                ('saturation', models.IntegerField(default=0)),
                ('colormode', models.TextField(default=b'ct', verbose_name=10)),
                ('colortemp', models.IntegerField(default=0)),
                ('x', models.FloatField(default=0)),
                ('y', models.FloatField(default=0)),
            ],
        ),
    ]
