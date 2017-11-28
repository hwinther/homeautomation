# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0009_auto_20150828_1806'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ts', models.DateTimeField(auto_now_add=True)),
                ('activationtime', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['ts'],
            },
        ),
        migrations.CreateModel(
            name='LightAction',
            fields=[
                ('action_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='homeautomation.Action')),
                ('state', models.BooleanField(default=True)),
                ('hue', models.IntegerField(null=True, blank=True)),
                ('brightness', models.IntegerField(null=True, blank=True)),
                ('saturation', models.IntegerField(null=True, blank=True)),
                ('colortemp', models.IntegerField(null=True, blank=True)),
                ('x', models.FloatField(null=True, blank=True)),
                ('y', models.FloatField(null=True, blank=True)),
                ('light', models.ForeignKey(to='homeautomation.Light')),
            ],
            bases=('homeautomation.action',),
        ),
    ]
