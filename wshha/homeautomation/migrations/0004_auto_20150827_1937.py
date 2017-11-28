# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0003_auto_20150827_1806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lightaction',
            name='activationtime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
