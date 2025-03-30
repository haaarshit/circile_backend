from rest_framework import serializers
from .models import SuperAdmin, TransactionFee
from django.contrib.auth.hashers import check_password

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