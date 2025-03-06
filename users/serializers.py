from rest_framework import serializers
from .models import Recycler, Producer

class RecyclerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recycler
        fields = ['email', 'full_name', 'mobile_no', 'designation', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Recycler.objects.create_user(**validated_data)
        return user

class ProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producer
        fields = ['email', 'full_name', 'mobile_no', 'designation', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Producer.objects.create_user(**validated_data)
        return user



from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Ensure UUID is stored as a string in the JWT token
        token["user_id"] = str(user.id)

        return token

# class RecyclerUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Recycler
#         fields = ['full_name', 'designation', 'password']
#         extra_kwargs = {'password': {'write_only': True}}
        
#         # Make fields optional
#         extra_kwargs = {
#             'password': {'write_only': True},
#             'full_name': {'required': False},
#             'designation': {'required': False},
#             'password': {'required': False},
#         }
    
# class ProducerUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Producer
#         fields = ['full_name', 'designation', 'password']
        
#         # Make fields optional
#         extra_kwargs = {
#             'password': {'write_only': True},
#             'full_name': {'required': False},
#             'designation': {'required': False},
#             'password': {'required': False},
#         }
    
    