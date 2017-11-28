# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0007_huelight'),
    ]

    operations = [
        migrations.AddField(
            model_name='lightaction',
            name='brightness',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='lightaction',
            name='colortemp',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='lightaction',
            name='hue',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='lightaction',
            name='saturation',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='lightaction',
            name='x',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='lightaction',
            name='y',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
