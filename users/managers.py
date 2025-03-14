from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, mobile_no, designation, password=None, **extra_fields):
        """
        Create and return a user with an email, full_name, mobile_no, designation, and optional password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            mobile_no=mobile_no,
            designation=designation,
            **extra_fields  
        )
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, mobile_no, designation, password=None, **extra_fields):
        """
        Create and return a superuser with all permissions.
        """
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        user = self.create_user(
            email,
            full_name,
            mobile_no,
            designation,
            password,
            **extra_fields
        )
        user.save(using=self._db)
        return user