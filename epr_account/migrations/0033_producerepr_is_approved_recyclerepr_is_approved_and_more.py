# Generated by Django 5.1.6 on 2025-03-22 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('epr_account', '0032_transaction_trail_documents'),
    ]

    operations = [
        migrations.AddField(
            model_name='producerepr',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='recyclerepr',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='creditoffer',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
    ]
