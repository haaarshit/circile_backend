# Generated by Django 5.1.6 on 2025-03-18 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('epr_account', '0026_creditoffer_credit_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producerepr',
            name='gst_number',
        ),
        migrations.RemoveField(
            model_name='recyclerepr',
            name='gst_number',
        ),
        migrations.AddField(
            model_name='creditoffer',
            name='product_type',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eprcredit',
            name='state',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
