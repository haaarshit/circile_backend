# users/migrations/0008_populate_unique_ids.py
from django.db import migrations
import uuid

def populate_unique_ids(apps, schema_editor):
    Recycler = apps.get_model('users', 'Recycler')
    Producer = apps.get_model('users', 'Producer')
    
    # Update Recyclers
    for recycler in Recycler.objects.all():
        while True:
            new_id = f'R{str(uuid.uuid4().int)[:7]}'
            if not Recycler.objects.filter(unique_id=new_id).exists():
                recycler.unique_id = new_id
                recycler.save()
                break
    
    # Update Producers
    for producer in Producer.objects.all():
        while True:
            new_id = f'P{str(uuid.uuid4().int)[:7]}'
            if not Producer.objects.filter(unique_id=new_id).exists():
                producer.unique_id = new_id
                producer.save()
                break

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0007_producer_social_links_producer_unique_id_and_more'),  # Replace with your actual 0007 migration name
    ]

    operations = [
        migrations.RunPython(populate_unique_ids),
    ]