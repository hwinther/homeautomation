# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LightAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ts', models.DateTimeField(auto_now_add=True)),
                ('state', models.BooleanField(default=True)),
                ('light', models.ForeignKey(to='homeautomation.Light')),
            ],
        ),
    ]
