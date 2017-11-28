# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0008_auto_20150827_2101'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lightaction',
            name='light',
        ),
        migrations.DeleteModel(
            name='LightAction',
        ),
    ]
