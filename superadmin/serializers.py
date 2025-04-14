from rest_framework import serializers
from .models import SuperAdmin, TransactionFee,Blog
from users.models import Newsletter
from decouple import config

from django.contrib.auth.hashers import check_password

cloud_name = config('CLOUDINARY_CLOUD_NAME')

class SuperAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperAdmin
        fields = ['id', 'email', 'password', 'created_at', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        superadmin = SuperAdmin(email=validated_data['email'])
        superadmin.set_password(validated_data['password'])
        superadmin.save()
        return superadmin

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
        return super().update(instance, validated_data)

class SuperAdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            superadmin = SuperAdmin.objects.get(email=email)
            if not superadmin.is_active:
                raise serializers.ValidationError("SuperAdmin account is inactive.")
            if not check_password(password, superadmin.password):
                raise serializers.ValidationError("Invalid password.")
        except SuperAdmin.DoesNotExist:
            raise serializers.ValidationError("SuperAdmin with this email does not exist.")
        
        data['superadmin'] = superadmin
        return data

class TransactionFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionFee
        fields = ['id', 'transaction_fee', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

# news letter

class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'content', 'created_at', 'is_sent', 'sent_at']
        read_only_fields = ['created_at', 'is_sent', 'sent_at']

# BLOGS

class BlogSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'image', 'created_at', 'updated_at', 'created_by','sub_title','slug']
        read_only_fields = ['id','created_at', 'updated_at', 'created_by','slug']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT', 'PATCH']:
            if 'image' in request.FILES:
                image_file = request.FILES.get('image')
                if not image_file:
                    raise serializers.ValidationError({"image": "Blog image file is required if provided."})
                if image_file.size > 5 * 1024 * 1024:
                    raise serializers.ValidationError({"image": "Image file size must be under 5MB."})
                allowed_formats = ['image/jpeg', 'image/png']
                if image_file.content_type not in allowed_formats:
                    raise serializers.ValidationError({"image": "Only JPEG and PNG images are allowed."})
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'image' in validated_data:
            instance.image = validated_data.pop('image', instance.image)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            if instance.image.url.startswith('http'):
                representation['image'] = instance.image.url
            else:
                representation['image'] = f'https://res.cloudinary.com/{cloud_name}/{instance.image.url}'
        else:
            representation['image'] = None
        return representation