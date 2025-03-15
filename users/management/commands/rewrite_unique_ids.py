from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import Recycler, Producer  # Replace 'your_app' with your actual app name

class Command(BaseCommand):
    help = 'Rewrites unique_id fields in Recycler and Producer tables with sequential IDs based on creation order.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting unique_id rewrite...")

        # Rewrite Recycler table
        self.rewrite_table(Recycler, 'R')
        self.stdout.write(self.style.SUCCESS("Successfully rewrote Recycler unique_ids."))

        # Rewrite Producer table
        self.rewrite_table(Producer, 'P')
        self.stdout.write(self.style.SUCCESS("Successfully rewrote Producer unique_ids."))

    def rewrite_table(self, model_class, prefix):
        # Fetch all records ordered by creation (assuming 'id' reflects order)
        # Replace 'id' with 'created_at' if you have a timestamp field
        records = model_class.objects.all().order_by('id')

        if not records.exists():
            self.stdout.write(f"No records found in {model_class.__name__} table.")
            return

        # Use a transaction to ensure atomicity
        with transaction.atomic():
            for index, record in enumerate(records, start=1):
                # Generate new sequential ID (e.g., R0000001, P0000001)
                new_id = f'{prefix}{index:07d}'
                
                # Update the record's unique_id
                record.unique_id = new_id
                record.save(update_fields=['unique_id'])

        self.stdout.write(f"Updated {records.count()} records in {model_class.__name__}.")