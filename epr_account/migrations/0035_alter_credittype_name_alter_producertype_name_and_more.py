# Generated by Django 5.1.6 on 2025-03-25 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('epr_account', '0034_producerepr_status_recyclerepr_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credittype',
            name='name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='producertype',
            name='name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='producttype',
            name='name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='recyclertype',
            name='name',
            field=models.CharField(),
        ),
    ]
