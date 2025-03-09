from rest_framework import serializers
from .models import RecyclerEPR, ProducerEPR, EPRCredit, EPRTarget
from decouple import config
cloud_name = config('CLOUDINARY_CLOUD_NAME')

class RecyclerEPRSerializer(serializers.ModelSerializer):
    # Define the field explicitly as a SerializerMethodField
    epr_certificate = serializers.SerializerMethodField()

    class Meta:
        model = RecyclerEPR
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'recycler']
    
    def get_epr_certificate(self, obj):
        print("entered RecyclerEPRSerializer - return erp cetificate =====================> ")
        if obj.epr_certificate:
            if obj.epr_certificate.url.startswith('http'):
                return obj.epr_certificate.url
            else:
                # Only add the domain if it's not already there
                return f'https://res.cloudinary.com/{cloud_name}/{obj.epr_certificate.url}'
                
        return None

    # def create(self, validated_data):
    
    #     request = self.context['request']
    #     validated_data['recycler'] = request.user
    #     # Handle file uploads explicitly
    #     epr_certificate = request.FILES.get('epr_certificate')
    #     if epr_certificate:
    #         validated_data['epr_certificate'] = epr_certificate
    #     else:
    #         validated_data['epr_certificate'] = None  

    #     return super().create(validated_data)
    def validate(self, data):
        """
        Check that the EPR certificate file is provided.
        """
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT']:
            if 'epr_certificate' not in request.FILES:
                raise serializers.ValidationError({"epr_certificate": "EPR certificate file is required."})
        return data
    def create(self, validated_data): 

        request = self.context['request']
        validated_data['producer'] = request.user
        
        epr_certificate = request.FILES.get('epr_certificate')
        validated_data['epr_certificate'] = epr_certificate
        
        return super().create(validated_data)

class ProducerEPRSerializer(serializers.ModelSerializer):
    epr_certificate = serializers.SerializerMethodField()
    class Meta:
        model = ProducerEPR
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'producer']
               

    def get_epr_certificate(self, obj):
        print("entered ProducerEPRSerializer - return erp cetificate =====================> ")
        if obj.epr_certificate:
            if obj.epr_certificate.url.startswith('http'):
                return obj.epr_certificate.url
            else:
                # Only add the domain if it's not already there
                return f'https://res.cloudinary.com/{cloud_name}/{obj.epr_certificate.url}'
                
        return None
    
    def validate(self, data):
        """
        Check that the EPR certificate file is provided.
        """
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT']:
            if 'epr_certificate' not in request.FILES:
                raise serializers.ValidationError({"epr_certificate": "EPR certificate file is required."})
        return data
    def create(self, validated_data): 

        request = self.context['request']
        validated_data['producer'] = request.user
        
        epr_certificate = request.FILES.get('epr_certificate')
        validated_data['epr_certificate'] = epr_certificate
        
        return super().create(validated_data)
    
class EPRCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = EPRCredit
        fields = '__all__'
        read_only_fields = ['id', 'recycler','erp_account'] 

class EPRTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EPRTarget
        fields = '__all__'
        read_only_fields = ['id', 'producer','erp_account'] 