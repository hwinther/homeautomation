# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0011_auto_20150829_2009'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='light',
            options={'ordering': ['name']},
        ),
    ]
