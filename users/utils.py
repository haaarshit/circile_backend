from .models import Recycler, Producer

def validate_unique_email(email):
    """
    Validate that the email is unique across both Recycler and Producer models
    """
    # Check if email exists in either Recycler or Producer models
    existing_user = (
        Recycler.objects.filter(email=email).exists() or 
        Producer.objects.filter(email=email).exists()
    )
    return existing_user
   