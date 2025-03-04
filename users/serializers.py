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



