from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, mobile_no, designation, password=None):
        """
        Create and return a user with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, mobile_no=mobile_no, designation=designation)
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, mobile_no, designation, password):
        """
        Create and return a superuser with all permissions.
        """
        user = self.create_user(email, full_name, mobile_no, designation, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user
