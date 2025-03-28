# Generated by Django 5.1.6 on 2025-03-15 09:55

import epr_account.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('epr_account', '0017_alter_transaction_transaction_proof'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='creditoffer',
            name='supporting_doc',
        ),
        migrations.AddField(
            model_name='creditoffer',
            name='trail_documents',
            field=models.JSONField(default=epr_account.models.get_default_supporting_docs, validators=[epr_account.models.validate_doc_choices]),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='order_id',
            field=models.CharField(editable=False, max_length=8, unique=True),
        ),
    ]
