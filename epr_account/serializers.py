from rest_framework import serializers
from .models import RecyclerEPR, ProducerEPR, EPRCredit, EPRTarget, CreditOffer,CounterCreditOffer,Transaction
from decouple import config
from users.models import Recycler,Producer
import json
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

    def validate(self, data):
        """
        Check that the EPR certificate file is provided.
        """
        request = self.context.get('request')
        if request and request.method in ['POST', 'PUT']:
            print(request.FILES)
            if 'epr_certificate' not in request.FILES:
                raise serializers.ValidationError({"epr_certificate": "EPR certificate file is required."})
        return data
    def create(self, validated_data): 

        request = self.context['request']
        validated_data['recycler'] = request.user
        
        epr_certificate = request.FILES.get('epr_certificate')
        validated_data['epr_certificate'] = epr_certificate
        
        return super().create(validated_data)
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


class CreditOfferSerializer(serializers.ModelSerializer):
    
    product_image = serializers.SerializerMethodField()

    availability_proof = serializers.SerializerMethodField()
    
    class Meta:
        model = CreditOffer
        fields = '__all__'
        read_only_fields = ['id', 'recycler','erp_account','epr_credit'] 

    def to_internal_value(self, data):
        # Handle case where supporting_doc is a string
        if 'supporting_doc' in data and isinstance(data['supporting_doc'], str):
            try:
                data['supporting_doc'] = json.loads(data['supporting_doc'])
            except json.JSONDecodeError:
                raise serializers.ValidationError({"supporting_doc": "Invalid JSON format"})
        return super().to_internal_value(data)

    
    def get_product_image(self, obj):
        print("entered ProducerEPRSerializer - return erp cetificate =====================> ")
        if obj.product_image:
            if obj.product_image.url.startswith('http'):
                return obj.product_image.url
            else:
                # Only add the domain if it's not already there
                return f'https://res.cloudinary.com/{cloud_name}/{obj.product_image.url}'
                
        return None
    
    def get_availability_proof(self, obj):
        print("entered ProducerEPRSerializer - return erp cetificate =====================> ")
        if obj.availability_proof:
            if obj.availability_proof.url.startswith('http'):
                return obj.availability_proof.url
            else:
                # Only add the domain if it's not already there
                return f'https://res.cloudinary.com/{cloud_name}/{obj.availability_proof.url}'
                
        return None
    
    
    def validate(self, data):
  
        request = self.context.get('request')
        
        if request and request.method in ['POST', 'PUT']:
            # Check for required image files
            if 'product_image' not in request.FILES:
                raise serializers.ValidationError({"error": "Product image file is required."})
            
            if 'availability_proof' not in request.FILES:
                raise serializers.ValidationError({"error": "Availability proof image file is required."})
            
            # Check supporting_doc in data
            if 'supporting_doc' not in data:
                raise serializers.ValidationError({"error": "Supporting documents list is required."})
            
            # Validate supporting_doc contents
            supporting_docs = data.get('supporting_doc', [])
            print(supporting_docs)
            
            # Check minimum length
            if len(supporting_docs) < 5:
                raise serializers.ValidationError({
                    "error": "At least 5 supporting documents are required."
                })
            
            # Valid document choices
            allowed_docs = {
                "Tax Invoice",
                "E-wayBIll",
                "Loading slip",
                "Unloading Slip",
                "Lorry Receipt copy",
                "DL",
                "Recycling Certificate Copy",
                "Co-Processing Certificate",
                "Lorry Photographs",
                "Municipality Endorsement"
            }
            
            # Check for invalid document types
            invalid_docs = [doc for doc in supporting_docs if doc not in allowed_docs]

            if invalid_docs:
                raise serializers.ValidationError({
                    "error": f"Invalid document types found: {', '.join(invalid_docs)}. "
                            f"Must be from: {', '.join(allowed_docs)}"
                })

        return data
    
    def create(self, validated_data): 
        print(validated_data)
        

        request = self.context['request']
        validated_data['recycler'] = request.user
        
        product_image = request.FILES.get('product_image')
        validated_data['product_image'] = product_image

        availability_proof = request.FILES.get('availability_proof')
        validated_data['availability_proof'] = availability_proof
        
        return super().create(validated_data)
    
class CounterCreditOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounterCreditOffer
        fields = '__all__'
        read_only_fields = ['id', 'recycler','erp_account','epr_credit'] 

    def create(self, validated_data): 

        request = self.context['request']
        validated_data['producer'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context["request"]

        if isinstance(request.user,Recycler):  
            if "status" in validated_data and len(validated_data) == 1:
                if request.user == instance.recycler:
                    instance.status = validated_data["status"]
                    if(validated_data['status']=='approved'):
                        instance.is_approved=True
                    instance.save()
                    return instance
                else:
                    raise serializers.ValidationError({"error": "Recycler in counter offer didn't match the current user."})
            else:
                raise serializers.ValidationError({"error": "Recycler can only update the status field."})

        # Producer can update all fields
        return super().update(instance, validated_data)


# TRANSACTION

class TransactionSerializer(serializers.ModelSerializer):
    transaction_proof = serializers.SerializerMethodField()

    def get_transaction_proof(self, obj):
        if obj.transaction_proof:
            if obj.transaction_proof.url.startswith('http'):
                return obj.transaction_proof.url
            else:
                # Only add the domain if it's not already there
                return f'https://res.cloudinary.com/{cloud_name}/{obj.transaction_proof.url}'
                
        return None


    class Meta:
        model = Transaction
        fields = [
            'id', 'order_id', 'recycler', 'producer', 'credit_offer',
            'counter_credit_offer', 'total_price', 'credit_type',
            'price_per_credit', 'product_type', 'producer_type',
            'credit_quantity', 'offered_by', 'work_order_date',
            'is_complete', 'status', 'transaction_proof'
        ]
        read_only_fields = [
            'id'
        ]

    def validate(self, data):
        request = self.context.get('request')
        print(request.data)
        print(request.FILES)
        
        if self.instance:  # Update
            if not isinstance(request.user, Recycler):
                raise serializers.ValidationError("Only recycler can update transaction")
            if any(k not in ['is_complete', 'status', 'transaction_proof'] for k in data.keys()):
                raise serializers.ValidationError("Only is_complete, status, and transaction_proof can be updated")
            if data.get('status') == 'approved' and  'transaction_proof' not in request.FILES:
                raise serializers.ValidationError("Transaction proof required for approval")
            if data.get('status') == 'approved':
                data['is_complete'] = True
        
        else:  # Create
            if not isinstance(request.user, Producer):
                raise serializers.ValidationError("Only producer can create transaction")
        
        return data

       
    def update(self, instance, validated_data):
        request = self.context["request"]

        if isinstance(request.user,Recycler):  
            request = self.context['request']
            
            transaction_proof = request.FILES.get('transaction_proof')
            validated_data['transaction_proof'] = transaction_proof

          
        # Producer can update all fields
        return super().update(instance, validated_data)