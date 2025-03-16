import uuid 
from django.db import models, transaction
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Max

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, UserManager,PermissionsMixin
from .managers import CustomUserManager  
import re
import os
from cloudinary.models import CloudinaryField

class BaseUserModel(AbstractBaseUser):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID primary key

    email = models.EmailField(unique=True, max_length=255)
    full_name = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    
     # New fields (optional at registration)
    social_links = models.JSONField(default=dict, blank=True) 

    registration_date = models.DateTimeField(null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    gst_number = models.CharField(max_length=50, null=True, blank=True)
    pcb_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    company_logo = CloudinaryField('image', null=True, blank=True)
    pcb_doc = CloudinaryField('raw', resource_type='raw', null=True, blank=True)

    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    reset_token_created_at = models.DateTimeField(null=True, blank=True)

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
        base_url = os.getenv('BASE_URL')
        verification_link = f"{base_url}/api/users/verify-email/{self.__class__.__name__.lower()}/{self.verification_token}/"
        
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


    def generate_password_reset_token(self):
        """
        Generate a unique password reset token
        """
        self.password_reset_token = get_random_string(length=50)
        self.reset_token_created_at = timezone.now()
        self.save()
        return self.password_reset_token

    def send_password_reset_email(self):
        """
        Send password reset email with a reset link
        """
        base_url = os.getenv('FRONTEND_URL')  # Ensure this is set in your environment
        reset_link = f"{base_url}/reset-password/{self.__class__.__name__.lower()}/{self.password_reset_token}/" # frontend

        subject = "Reset Your Password"
        message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Reset Your Password</title>
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
                        background: #dc3545;
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
                    .reset-btn {{
                        display: inline-block;
                        background: #007bff;
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
                        Password Reset Request
                    </div>
                    <div class="content">
                        <p>Hello <strong>{self.full_name}</strong>,</p>
                        <p>We received a request to reset your password. Click the button below to reset it:</p>
                        <a href="{reset_link}" class="reset-btn">Reset Password</a>
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p>{reset_link}</p>
                        <p>This link will expire in 24 hours. If you didn’t request this, please ignore this email.</p>
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

    def reset_password(self, token, new_password):
        """
        Reset the password if the token is valid
        """
        if (self.password_reset_token == token and 
            self.reset_token_created_at and 
            timezone.now() - self.reset_token_created_at < timedelta(hours=24)):
            self.set_password(new_password)
            self.password_reset_token = None
            self.reset_token_created_at = None
            self.save()
            return True
        return False
    class Meta:
        abstract = True

class Recycler(BaseUserModel):
    """
    Recycler user model
    """
    unique_id = models.CharField(
        max_length=8,  
        unique=True, 
        editable=False,
        null=False,  
        blank=False
    )

    def generate_unique_id(self):
        # Get the highest existing ID with 'R' prefix
        last_recycler = Recycler.objects.aggregate(Max('unique_id'))['unique_id__max']
        if last_recycler:
            # Extract the numeric part (e.g., 'R0000012' -> '0000012')
            last_number = int(last_recycler[1:])  # Skip the 'R' prefix
            new_number = last_number + 1
        else:
            new_number = 1  # Start at 1 if no records exist
        
        # Format the new ID with 'R' prefix and padded zeros
        return f'R{new_number:07d}'  # e.g., R0000001, R0000002, etc.

    def save(self, *args, **kwargs):
        if not self.unique_id:
            # Use a transaction to avoid race conditions
            with transaction.atomic():
                # Lock the table to ensure uniqueness in concurrent scenarios
                locked_recyclers = Recycler.objects.select_for_update().all()
                self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Recycler'
        verbose_name_plural = 'Recyclers'


class Producer(BaseUserModel):
    """
    Producer user model
    """
    unique_id = models.CharField(
        max_length=8,  
        unique=True, 
        editable=False,
        null=False,  
        blank=False
    )

    def generate_unique_id(self):
        # Get the highest existing ID with 'P' prefix
        last_producer = Producer.objects.aggregate(Max('unique_id'))['unique_id__max']
        if last_producer:
            # Extract the numeric part (e.g., 'P0000012' -> '0000012')
            last_number = int(last_producer[1:])  # Skip the 'P' prefix
            new_number = last_number + 1
        else:
            new_number = 1  # Start at 1 if no records exist
        
        return f'P{new_number:07d}' 

    def save(self, *args, **kwargs):
        if not self.unique_id:
            # Use a transaction to avoid race conditions
            with transaction.atomic():
                locked_producers = Producer.objects.select_for_update().all()
                self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Producer'
        verbose_name_plural = 'Producers'