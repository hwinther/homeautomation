# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-28 22:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0015_auto_20171128_2311'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='temperaturedatapoint',
            options={'ordering': ['created']},
        ),
        migrations.AlterField(
            model_name='temperaturedatapoint',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]