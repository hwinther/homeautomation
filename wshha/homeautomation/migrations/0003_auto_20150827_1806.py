# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0002_lightaction'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lightaction',
            options={'ordering': ['ts']},
        ),
        migrations.AddField(
            model_name='lightaction',
            name='activationtime',
            field=models.DateTimeField(default=datetime.datetime(2015, 8, 27, 18, 6, 36, 832030, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
