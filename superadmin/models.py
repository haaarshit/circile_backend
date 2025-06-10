from django.db import models
from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator,MinValueValidator
import uuid 
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
from decouple import config 

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


class Blog(models.Model):

    blog_id =  models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)  
    sub_title = models.CharField(max_length=255)
    content = models.TextField()
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # Added fields from JSON
    blog_date = models.DateTimeField(blank=True, null=True)  
    blog_banner = CloudinaryField('image', blank=True, null=True, folder='blogBanner')  
    blog_banner_alt_text = models.CharField(max_length=255, blank=True, null=True)  
    name = models.CharField(max_length=255, blank=True, null=True)  
    url = models.CharField(max_length=255, blank=True, null=True)  
    page_title = models.CharField(max_length=255, blank=True, null=True)  
    meta_title = models.CharField(max_length=255, blank=True, null=True)  
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)  
    meta_description = models.TextField(blank=True, null=True)  
    
    image = CloudinaryField('image', blank=True, null=True, folder='blogs')  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        SuperAdmin,
        on_delete=models.CASCADE, related_name='blogs',null=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique by appending a counter if necessary
            original_slug = self.slug
            counter = 1
            while Blog.objects.filter(slug=self.slug).exclude(blog_id=self.blog_id).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        domain = config('BASE_URL', default='https://circle8.in/backend')  # Fallback to example.com if not set
        self.url = f"{domain}/api/users/{self.slug}/"

        if self.image and not self.blog_banner:
            self.blog_banner = self.image
        
        super().save(*args, **kwargs)