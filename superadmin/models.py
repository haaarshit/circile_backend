from django.db import models
from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator
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