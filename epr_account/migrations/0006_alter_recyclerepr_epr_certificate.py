# Generated by Django 5.1.6 on 2025-03-08 05:23

import epr_account.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('epr_account', '0005_alter_recyclerepr_epr_certificate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recyclerepr',
            name='epr_certificate',
            field=epr_account.models.CustomCloudinaryField(max_length=255, verbose_name='file'),
        ),
    ]
