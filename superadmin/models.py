from django.db import models
from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator,MinValueValidator
import uuid 

class SuperAdmin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        max_length=255,
        validators=[EmailValidator()],
        help_text="SuperAdmin's email address"
    )
    password = models.CharField(
        max_length=255,
        help_text="Hashed password for the SuperAdmin"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


    def set_password(self, raw_password):
        """Hash the password before saving."""
        self.password = make_password(raw_password)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "SuperAdmin"
        verbose_name_plural = "SuperAdmins"


class TransactionFee(models.Model):
    """
    Model to store transaction fee, editable only by SuperAdmins.
    """
    transaction_fee = models.FloatField(blank=False,default=0.0) 
    
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional description of the fee"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Fee: {self.transaction_fee}"

    class Meta:
        verbose_name = "Transaction Fee"
        verbose_name_plural = "Transaction Fees"