# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homeautomation', '0010_action_lightaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='TV',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(default=b'TV', max_length=64)),
                ('state', models.BooleanField(default=False)),
                ('mute', models.BooleanField(default=False)),
                ('volume', models.IntegerField(default=0)),
                ('source', models.TextField(default=b'unknown', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='TVAction',
            fields=[
                ('action_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='homeautomation.Action')),
                ('state', models.NullBooleanField()),
                ('mute', models.NullBooleanField()),
                ('volume', models.IntegerField(null=True, blank=True)),
                ('source', models.TextField(max_length=20, null=True, blank=True)),
            ],
            bases=('homeautomation.action',),
        ),
        migrations.AlterField(
            model_name='huelight',
            name='colormode',
            field=models.TextField(default=b'ct', max_length=10),
        ),
    ]
