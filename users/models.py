import uuid 
from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, UserManager,PermissionsMixin
from .managers import CustomUserManager  
import re

from cloudinary.models import CloudinaryField

class BaseUserModel(AbstractBaseUser):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID primary key

    email = models.EmailField(unique=True, max_length=255)
    full_name = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    
     # New fields (optional at registration)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    gst_number = models.CharField(max_length=50, null=True, blank=True)
    pcb_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    company_logo = CloudinaryField('image', null=True, blank=True)
    pcb_doc = CloudinaryField('raw', resource_type='raw', null=True, blank=True)

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = []


    is_active = models.BooleanField(default=True)  
    # Email verification fields

    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, null=True, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    def set_password(self, raw_password):
        """
        Hash the password before saving
        """
        self.password = make_password(raw_password)

    def validate_mobile_number(self):
        """
        Validate mobile number format
        """
        # Basic mobile number validation (adjust regex as needed)
        mobile_pattern = re.compile(r'^[6-9]\d{9}$')
        return mobile_pattern.match(self.mobile_no) is not None

    def generate_verification_token(self):
        """
        Generate a unique verification token for email
        """
        self.verification_token = get_random_string(length=50)
        self.token_created_at = timezone.now()
        self.save()

    def send_verification_email(self):
        """
        Send email verification link
        """
        verification_link = f"http://localhost:8000/api/users/verify-email/{self.__class__.__name__.lower()}/{self.verification_token}/"
        
        subject = "Verify Your Email Address"
        message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Verify Your Email</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                background: #ffffff;
                margin: 20px auto;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: #007bff;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 22px;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                padding: 20px;
                font-size: 16px;
                color: #333;
                text-align: center;
            }}
            .verify-btn {{
                display: inline-block;
                background: #28a745;
                color: white;
                text-decoration: none;
                padding: 12px 20px;
                font-size: 18px;
                border-radius: 5px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                font-size: 14px;
                color: #777;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                Verify Your Email
            </div>
            <div class="content">
                <p>Hello <strong>{self.full_name}</strong>,</p>
                <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
                <a href="{verification_link}" class="verify-btn">Verify Email</a>
                <p>If the button doesn't work, copy and paste the link below into your browser:</p>
                <p>{verification_link}</p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
            <div class="footer">
                © {timezone.now().year} CIRCILE. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """
        
        send_mail(
            subject,
            "",
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
            html_message=message
        )

    def verify_email(self, token):
        """
        Verify email with the provided token
        """
        if (self.verification_token == token and 
            self.token_created_at and 
            timezone.now() - self.token_created_at < timedelta(hours=24)):
            self.is_verified = True
            self.verification_token = None
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.full_name} - {self.email}"

    class Meta:
        abstract = True

class Recycler(BaseUserModel):
    """
    Recycler user model
    """
    class Meta:
        verbose_name = 'Recycler'
        verbose_name_plural = 'Recyclers'

class Producer(BaseUserModel):
    """
    Producer user model
    """
    class Meta:
        verbose_name = 'Producer'
        verbose_name_plural = 'Producers'