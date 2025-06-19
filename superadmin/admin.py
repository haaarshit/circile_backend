from django.contrib import admin
from .models import Blog
from cloudinary.forms import CloudinaryFileField
from django import forms

class BlogAdminForm(forms.ModelForm):
    image = CloudinaryFileField(required=False)
    blog_banner = CloudinaryFileField(required=False)

    class Meta:
        model = Blog
        fields = '__all__'

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    form = BlogAdminForm
    prepopulated_fields = {"slug": ("title",)}

# admin.site.register(Blog)
