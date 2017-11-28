# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Light',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(max_length=64)),
                ('state', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='LightSourceSystem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(max_length=64)),
            ],
        ),
        migrations.AddField(
            model_name='light',
            name='source',
            field=models.ForeignKey(to='homeautomation.LightSourceSystem'),
        ),
    ]
