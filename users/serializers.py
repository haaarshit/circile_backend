from rest_framework import serializers
from .models import Recycler, Producer
from decouple import config
cloud_name = config('CLOUDINARY_CLOUD_NAME')

class RecyclerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recycler
        fields = ['email', 'full_name', 'mobile_no', 'designation', 'password','company_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        print(validated_data)
        user = Recycler.objects.create_user(**validated_data)
        return user

class ProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producer
        fields = ['email', 'full_name', 'mobile_no', 'designation', 'password','company_name']
        extra_kwargs = {'password': {'write_only': True}}


    def create(self, validated_data):
        user = Producer.objects.create_user(**validated_data)
        return user

class RecyclerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recycler
        # fields = [
        #     'company_name', 'city', 'state', 'gst_number', 'pcb_number', 'address', 'company_logo', 'pcb_doc'
        # ]
        fields = '__all__'
    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.method in ['PATCH', 'PUT']:
            # For partial updates, only validate fields that are being updated
            if 'company_logo' in request.FILES and not request.FILES.get('company_logo'):
                raise serializers.ValidationError({"company_logo": "Company logo file is required."})
                
            if 'pcb_doc' in request.FILES and not request.FILES.get('pcb_doc'):
                raise serializers.ValidationError({"pcb_doc": "PCB document file is required."})
             
        return data
    
            
    def to_representation(self, instance):
        # This is for GET requests (viewing the data)
        representation = super().to_representation(instance)
        
        # Add the full URLs for company_logo
        if instance.company_logo:
            if instance.company_logo.url.startswith('http'):
                representation['company_logo'] = instance.company_logo.url
            else:
                representation['company_logo'] = f'https://res.cloudinary.com/{cloud_name}/{instance.company_logo.url}'
        
        # Add the full URLs for pcb_doc
        if instance.pcb_doc:
            if instance.pcb_doc.url.startswith('http'):
                representation['pcb_doc'] = instance.pcb_doc.url
            else:
                representation['pcb_doc'] = f'https://res.cloudinary.com/{cloud_name}/{instance.pcb_doc.url}'
        representation.pop('password', None)        
        return representation

class ProducerUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Producer
        fields = '__all__'
    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.method in ['PATCH', 'PUT']:
            # For partial updates, only validate fields that are being updated
            if 'company_logo' in request.FILES and not request.FILES.get('company_logo'):
                raise serializers.ValidationError({"company_logo": "Company logo file is required."})
                
            if 'pcb_doc' in request.FILES and not request.FILES.get('pcb_doc'):
                raise serializers.ValidationError({"pcb_doc": "PCB document file is required."})
            
        return data
    
    def to_representation(self, instance):
        # This is for GET requests (viewing the data)
        representation = super().to_representation(instance)
        
        # Add the full URLs for company_logo
        if instance.company_logo:
            if instance.company_logo.url.startswith('http'):
                representation['company_logo'] = instance.company_logo.url
            else:
                representation['company_logo'] = f'https://res.cloudinary.com/{cloud_name}/{instance.company_logo.url}'
        
        # Add the full URLs for pcb_doc
        if instance.pcb_doc:
            if instance.pcb_doc.url.startswith('http'):
                representation['pcb_doc'] = instance.pcb_doc.url
            else:
                representation['pcb_doc'] = f'https://res.cloudinary.com/{cloud_name}/{instance.pcb_doc.url}'
        representation.pop('password', None)

        return representation
    
class RecyclerDetailSerializer(serializers.ModelSerializer):
    company_logo = serializers.SerializerMethodField()
    pcb_doc = serializers.SerializerMethodField()
    class Meta:
        model = Recycler
        fields = [
            'id', 'email', 'full_name', 'mobile_no', 'designation', 
            'company_name', 'city', 'state', 'gst_number', 'pcb_number', 
            'address', 'company_logo', 'pcb_doc', 'is_active', 'is_verified','unique_id','social_links'
        ]
    def get_company_logo(self, obj):
        """
        Handle company_logo image URL generation
        """
        if obj.company_logo:
            try:
                url = obj.company_logo.url
                if url.startswith('http'):
                    return url
                return f'https://res.cloudinary.com/{cloud_name}/{url}'
            except Exception as e:
                print(f"Error getting company_logo URL: {str(e)}")
                return None
        return None

    def get_pcb_doc(self, obj):
        """
        Handle pcb_doc URL generation
        """
        if obj.pcb_doc:
            try:
                url = obj.pcb_doc.url
                if url.startswith('http'):
                    return url
                return f'https://res.cloudinary.com/{cloud_name}/{url}'
            except Exception as e:
                print(f"Error getting pcb_doc URL: {str(e)}")
                return None
        return None
    
class ProducerDetailSerializer(serializers.ModelSerializer):
    company_logo = serializers.SerializerMethodField()
    pcb_doc = serializers.SerializerMethodField()
    class Meta:
        model = Recycler
        fields = [
            'id', 'email', 'full_name', 'mobile_no', 'designation', 
            'company_name', 'city', 'state', 'gst_number', 'pcb_number', 
            'address', 'company_logo', 'pcb_doc', 'is_active', 'is_verified','unique_id','social_links'
        ]
    def get_company_logo(self, obj):
        """
        Handle company_logo image URL generation
        """
        if obj.company_logo:
            try:
                url = obj.company_logo.url
                if url.startswith('http'):
                    return url
                return f'https://res.cloudinary.com/{cloud_name}/{url}'
            except Exception as e:
                print(f"Error getting company_logo URL: {str(e)}")
                return None
        return None

    def get_pcb_doc(self, obj):
        """
        Handle pcb_doc URL generation
        """
        if obj.pcb_doc:
            try:
                url = obj.pcb_doc.url
                if url.startswith('http'):
                    return url
                return f'https://res.cloudinary.com/{cloud_name}/{url}'
            except Exception as e:
                print(f"Error getting pcb_doc URL: {str(e)}")
                return None
        return None

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=100)
    new_password = serializers.CharField(min_length=8)