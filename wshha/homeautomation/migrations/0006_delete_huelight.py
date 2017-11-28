# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0005_huelight'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HueLight',
        ),
    ]
