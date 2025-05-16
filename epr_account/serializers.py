from rest_framework import serializers
from .models import RecyclerEPR, ProducerEPR, EPRCredit, EPRTarget, CreditOffer,CounterCreditOffer,Transaction,WasteType, ProducerType, RecyclerType, ProductType, CreditType,PurchasesRequest
from decouple import config
from users.models import Recycler,Producer
from superadmin.models import TransactionFee
import mimetypes

from superadmin.models import SuperAdmin
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
        user = request.user

        if request and request.method in ['POST', 'PUT']:
            print(request.FILES)
            if 'epr_certificate' not in request.FILES:
                raise serializers.ValidationError({"epr_certificate": "EPR certificate file is required."})
        # if 'is_approved' in data or 'status' in data:
        #     if  not isinstance(user, SuperAdmin):
        #         raise serializers.ValidationError("Only SuperAdmin can set is_approved or status fields.")

        if data.get('status') == 'approved' and not data.get('is_approved'):
            raise serializers.ValidationError("is_approved must be True when status is 'approved'.")
        if data.get('status') == 'rejected' and  data.get('is_approved'):
            raise serializers.ValidationError("is_approved must be False when status is 'rejected'.")
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
    targets = serializers.SerializerMethodField()
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
    
    def get_targets(self, obj):
        fy = self.context['request'].query_params.get('FY', None)

        targets = EPRTarget.objects.filter(epr_account=obj)

        if fy:
            targets = targets.filter(FY=fy)
        if targets.exists():
            return EPRTargetSerializer(targets, many=True).data
        else:
            return []
    
    def validate(self, data):
        """
        Check that the EPR certificate file is provided.
        """
        request = self.context.get('request')
        user = request.user

        if request and request.method in ['POST', 'PUT']:
            if 'epr_certificate' not in request.FILES:
                raise serializers.ValidationError({"epr_certificate": "EPR certificate file is required."})

        # if 'is_approved' in data or 'status' in data:
        #       if  not isinstance(user, SuperAdmin):
        #         raise serializers.ValidationError("Only SuperAdmin can set is_approved or status fields.")
        # Ensure is_approved is True if status is approved
        if data.get('status') == 'approved' and not data.get('is_approved'):
            raise serializers.ValidationError("is_approved must be True when status is 'approved'.")
        if data.get('status') == 'rejected' and  data.get('is_approved'):
            raise serializers.ValidationError("is_approved must be False when status is 'rejected'.")

        return data
    def create(self, validated_data): 

        request = self.context['request']
        validated_data['producer'] = request.user
        
        epr_certificate = request.FILES.get('epr_certificate')
        validated_data['epr_certificate'] = epr_certificate
        
        return super().create(validated_data)
    
class EPRCreditSerializer(serializers.ModelSerializer):
    registered_name = serializers.SerializerMethodField()  

    class Meta:
        model = EPRCredit
        fields = '__all__'
        read_only_fields = ['id', 'recycler','erp_account'] 
    def get_registered_name(self, obj):
        if obj.epr_account:
            return obj.epr_account.epr_registered_name   
        return None
    
class EPRTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EPRTarget
        fields = '__all__'
        read_only_fields = ['id', 'producer','erp_account'] 


class CreditOfferSerializer(serializers.ModelSerializer):
    
    product_image = serializers.SerializerMethodField()

    availability_proof = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()  # New field for company
    registered_on = serializers.SerializerMethodField()  # get registered date
    address = serializers.SerializerMethodField()  
    city = serializers.SerializerMethodField()  
    state = serializers.SerializerMethodField()  
    transaction_fee = serializers.SerializerMethodField()  
    gst = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    recycler_type = serializers.SerializerMethodField()
    recycler_id = serializers.SerializerMethodField()



    
    class Meta:
        model = CreditOffer
        fields = '__all__'
        read_only_fields = ['id', 'recycler','erp_account','epr_credit'] 

    def to_internal_value(self, data):
        # Handle case where trail_documents is a string
        if 'trail_documents' in data and isinstance(data['trail_documents'], str):
            try:
                data['trail_documents'] = json.loads(data['trail_documents'])
            except json.JSONDecodeError:
                raise serializers.ValidationError({"trail_documents": "Invalid JSON format"})
        return super().to_internal_value(data)

    
    def get_company_name(self, obj):
        # Fetch the company from the recycler foreign key
        if obj.recycler:
            # Assuming 'company' is a field in the Recycler model
            return obj.recycler.company_name  # Adjust this based on your Recycler model
        return None
    
    def get_registered_on(self, obj):
        if obj.epr_account:
            return obj.epr_account.epr_registration_date   
        return None
    
    def get_address(self, obj):
        if obj.epr_account:
            return obj.epr_account.address   
        return None
    
    def get_city(self, obj):
        if obj.epr_account:
            return obj.epr_account.city   
        return None
    
    def get_state(self, obj):
        if obj.epr_account:
            return obj.epr_account.state   
        return None
    
    def get_recycler_type(self, obj):
        if obj.epr_account:
            return obj.epr_account.recycler_type   
        return None
    
    def get_transaction_fee(self, obj):
        fees =  TransactionFee.objects.first()
        if fees:
            return fees.transaction_fee 
        return 0
    
    def get_gst(self, obj):
        if obj.price_per_credit and obj.minimum_purchase:
            value = obj.price_per_credit*obj.minimum_purchase
            processing_fee = 0.05 * value
            gst = (value+processing_fee)*0.18
            return gst
            # return (obj.price_per_credit*obj.minimum_purchase)*0.18
        return 0
    
    def get_total(self, obj):
        fee = 0
        fees =  TransactionFee.objects.first()
        if fees:
            fee = fees.transaction_fee 
        if obj.price_per_credit and obj.minimum_purchase:
            value = obj.price_per_credit*obj.minimum_purchase
            processing_fee = 0.05 * value
            gst = (value+processing_fee)*0.18
            return  value + processing_fee + gst + fee  
            # return  obj.price_per_credit*obj.minimum_purchase + ( obj.price_per_credit*obj.minimum_purchase)*0.18 +fee
        return 0
    
    def get_product_image(self, obj):
        if obj.product_image:
            if obj.product_image.url.startswith('http'):
                return obj.product_image.url
            else:
                # Only add the domain if it's not already there
                return f'https://res.cloudinary.com/{cloud_name}/{obj.product_image.url}'
                
        return None
    
    def get_availability_proof(self, obj):
        if obj.availability_proof:
            if obj.availability_proof.url.startswith('http'):
                return obj.availability_proof.url
            else:
                # Only add the domain if it's not already there
                return f'https://res.cloudinary.com/{cloud_name}/{obj.availability_proof.url}'
                
        return None
    
    def get_recycler_id(self,obj):
        if obj.recycler:
            if obj.recycler.unique_id:
                return obj.recycler.unique_id
        return None

    def validate(self, data):
  
        request = self.context.get('request')
        allowed_mime_types = [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/webp',
            'image/jpg'
        ]

        for field_name in ['product_image', 'availability_proof']:
            image_field = request.FILES.get(field_name) if request.FILES else None
            if image_field:
                # For CloudinaryField, check the file object

                mime_type, _ = mimetypes.guess_type(image_field.name)
                if mime_type not in allowed_mime_types:
                    raise serializers.ValidationError({
                        field_name: f'Only image files (JPEG, PNG, GIF, BMP, WEBP) are allowed for {field_name.replace("_", " ").title()}.'
                    })
        if request and request.method in ['POST', 'PUT']:
            # Check for required image files
            if 'product_image' not in request.FILES:
                raise serializers.ValidationError({"error": "Product image file is required."})
            
            if 'availability_proof' not in request.FILES:
                raise serializers.ValidationError({"error": "Availability proof image file is required."})
            
            # Check trail_documents in data
            if 'trail_documents' not in data:
                raise serializers.ValidationError({"error": "Supporting documents list is required."})
            
            # Validate trail_documents contents
            trail_documents = data.get('trail_documents', [])
            print(trail_documents)

            
            # Valid document choices
            allowed_docs = {
                "Tax Invoice",
                "E-wayBIll",
                "Loading slip",
                "Unloading Slip",
                "Lorry Receipt copy",
                "Recycling Certificate Copy",
                "Co-Processing Certificate",
                "Lorry Photographs",
                "Credit Transfer Proof",
                "EPR Registration Certificate"
            }
            
            # Check for invalid document types
            invalid_docs = [doc for doc in trail_documents if doc not in allowed_docs]

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

    credit_type = serializers.SerializerMethodField()  
    waste_type = serializers.SerializerMethodField()  
    credit_available = serializers.SerializerMethodField()  
    price_per_credit = serializers.SerializerMethodField()  
    title = serializers.SerializerMethodField() 
    actual_price = serializers.SerializerMethodField()
    order_by = serializers.SerializerMethodField()
    transaction_fee =  serializers.SerializerMethodField()
    gst =  serializers.SerializerMethodField()
    total =  serializers.SerializerMethodField()



    class Meta:
        model = CounterCreditOffer
        fields = '__all__'
        read_only_fields = ['id', 'recycler','erp_account','epr_credit'] 

    def get_credit_type(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.credit_type
        return None
    
    def get_waste_type(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.waste_type 
        return None
    
    def get_credit_available(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.credit_available 
        return None
    
    def get_price_per_credit(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.price_per_credit 
        return None
    
    def get_title(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.offer_title
        return None
    
    def get_actual_price(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.price_per_credit
        return None
    
        
    def get_order_by(self, obj):
        if obj.producer:
            return obj.producer.full_name
        return None
    
    def get_transaction_fee(self, obj):
        price = obj.offer_price 
        quantity = obj.quantity
        if price and quantity:
            value = price*quantity
            processing_fee = 0.05 * value
            return processing_fee
        return 0
    
    def get_gst(self, obj):
        price = obj.offer_price 
        quantity = obj.quantity
        if price and quantity:
            value = price*quantity
            processing_fee = 0.05 * value
            gst = (value+processing_fee)*0.18
            return gst
        return 0
    
    def get_total(self, obj):
        fee = 0
        fees =  TransactionFee.objects.first()
        if fees:
            fee - fees.transaction_fee 
        
        price = obj.offer_price 
        quantity = obj.quantity
        if price and quantity:
            value = price*quantity
            processing_fee = 0.05 * value
            gst = (value+processing_fee)*0.18
            return  value + processing_fee + gst 
            # return (price*quantity) + (price*quantity)*0.18 + fee
        return 0



    def create(self, validated_data): 

        request = self.context['request']
        validated_data['producer'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context["request"]

        if isinstance(request.user,Recycler):  
            if "status" in validated_data and len(validated_data) == 1:
                if instance.status == 'rejected':
                    raise serializers.ValidationError("Counter offer is already rejected")
                if request.user == instance.recycler:
                    instance.status = validated_data["status"]
                    if(validated_data['status']=='approved'):
                        instance.is_approved=True
                    if(validated_data['status']=='rejected'):
                        instance.is_approved=False
                    instance.save()
                    return instance
                else:
                    raise serializers.ValidationError({"error": "Recycler in counter offer didn't match the current user."})
            else:
                raise serializers.ValidationError("Recycler can only update the status field.")

        # Producer can update all fields
        return super().update(instance, validated_data)

# PURCHASE REQUEST
class PurchasesRequestSerializer(serializers.ModelSerializer):

    credit_type = serializers.SerializerMethodField()  
    waste_type = serializers.SerializerMethodField()  
    credit_available = serializers.SerializerMethodField()  
    price_per_credit = serializers.SerializerMethodField()  
    title = serializers.SerializerMethodField()
    order_by = serializers.SerializerMethodField()
    transaction_fee =  serializers.SerializerMethodField()
    gst =  serializers.SerializerMethodField()
    total =  serializers.SerializerMethodField()

    class Meta:
        model = PurchasesRequest
        fields =  '__all__'
        read_only_fields = ['id']  

    def get_credit_type(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.credit_type
        return None
    
    def get_waste_type(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.waste_type 
        return None
    
    def get_credit_available(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.credit_available 
        return None
    
    def get_price_per_credit(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.price_per_credit 
        return None
    
    
    def get_title(self, obj):
        if obj.credit_offer:
            return obj.credit_offer.offer_title
        return None
    
    def get_order_by(self, obj):
        if obj.producer:
            return obj.producer.full_name
        return None
    
    def get_transaction_fee(self, obj):
        price = obj.credit_offer.price_per_credit 
        quantity = obj.quantity
        if price and quantity:
            value = price*quantity
            processing_fee = 0.05 * value
            return processing_fee
        return 0
    
    def get_gst(self, obj):
        price = obj.credit_offer.price_per_credit 
        quantity = obj.quantity
        if price and quantity:
            value = price*quantity
            processing_fee = 0.05 * value
            gst = (value+processing_fee)*0.18
            return gst
            # return (price*quantity)*0.18
        return 0
    
    def get_total(self, obj):
        fee = 0
        fees =  TransactionFee.objects.first()
        if fees:
            fee - fees.transaction_fee 
        
        price = obj.credit_offer.price_per_credit 
        quantity = obj.quantity
        if price and quantity:
            value = price*quantity
            processing_fee = 0.05 * value
            gst = (value+processing_fee)*0.18
            return  value + processing_fee + gst 
            # return (price*quantity) + (price*quantity)*0.18 + fee
        return 0



    def validate(self, data):
        request = self.context.get('request')

        if self.instance:  # Update
            if not isinstance(request.user, Recycler):
                raise serializers.ValidationError("Only Recycler can update PurchasesRequest")
            if self.instance.status == 'rejected':
                raise serializers.ValidationError("Request is already rejected")
            if any(k not in ['status', 'is_approved'] for k in data.keys()):
                raise serializers.ValidationError("Only status and is_approved can be updated by Recycler")
        if data.get('status') == 'rejected':
            data['is_approved'] = False
        if data.get('status') == 'approved':
            data['is_approved'] = True

        return data
    
    def create(self, validated_data):
        validated_data['producer'] = self.context['request'].user  
        return super().create(validated_data)

# TRANSACTION
class TransactionSerializer(serializers.ModelSerializer):
   

    transaction_proof = serializers.SerializerMethodField()
    trail_documents = serializers.SerializerMethodField()
    producer_transfer_proof = serializers.SerializerMethodField()
    recycler_transfer_proof = serializers.SerializerMethodField()
    producer_unique_id = serializers.SerializerMethodField()
    recycler_unique_id = serializers.SerializerMethodField()
    transaction_status = serializers.SerializerMethodField()
    

    def get_transaction_proof(self, obj):
        if obj.transaction_proof:
            return obj.transaction_proof.url if obj.transaction_proof.url.startswith('http') else f'https://res.cloudinary.com/{cloud_name}/{obj.transaction_proof.url}'
        return None
    
    def get_trail_documents(self, obj):
        if obj.trail_documents:
            return obj.trail_documents.url if obj.trail_documents.url.startswith('http') else f'https://res.cloudinary.com/{cloud_name}/{obj.trail_documents.url}'
        return None
    
    def get_producer_transfer_proof(self, obj):
        if obj.producer_transfer_proof:
            return obj.producer_transfer_proof.url if obj.producer_transfer_proof.url.startswith('http') else f'https://res.cloudinary.com/{cloud_name}/{obj.producer_transfer_proof.url}'
        return None
    
    def get_recycler_transfer_proof(self, obj):
        if obj.recycler_transfer_proof:
            return obj.recycler_transfer_proof.url if obj.recycler_transfer_proof.url.startswith('http') else f'https://res.cloudinary.com/{cloud_name}/{obj.recycler_transfer_proof.url}'
        return None
    
    def get_producer_unique_id(self,obj):
        if obj.producer:
            return obj.producer.unique_id
        
        
    def get_recycler_unique_id(self,obj):
        if obj.recycler:
            return obj.recycler.unique_id
        
    def get_transaction_status(self,obj):
        if obj.transaction_proof and not obj.is_approved:
            return "In Process"
        if obj.transaction_proof and  obj.is_approved and obj.trail_documents:
            return "Complete"

        return "Pending"
    
    def to_representation(self, instance):
        # Get the default serialized data
        data = super().to_representation(instance)
        # Replace the 'status' field with the capitalized display value
        data['status'] = instance.get_status_display()
        return data
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id']

    def validate(self, data):
        request = self.context.get('request')
        
        if self.instance:  # Update
            user = request.user
            
            # Superadmin check
            if isinstance(user, SuperAdmin):
                allowed_fields = {'is_approved', 'status'}
                if self.instance.is_approved:
                    raise serializers.ValidationError("Transaction is already approved")
                if any(k not in allowed_fields for k in data.keys()):
                    raise serializers.ValidationError("Superadmin can only update 'is_approved' and 'status'")
                if data.get('status') == 'approved' and not (self.instance.transaction_proof):
                    raise serializers.ValidationError("Cannot approve transaction without Producer Transaction Proof")
            
            # Producer check
            elif isinstance(user, Producer):
                if self.instance.status == 'rejected':
                    raise serializers.ValidationError("Transaction is already rejected")

                allowed_fields = {'transaction_proof', 'producer_transfer_proof'}
                combined_keys = set(data.keys()) | set(request.FILES.keys())
                if any(k not in allowed_fields for k in combined_keys):
                    raise serializers.ValidationError("Producer can only update 'transaction_proof' and 'producer_transfer_proof'")
                if not self.instance.transaction_proof :
                    if 'transaction_proof' not in request.FILES:
                        raise serializers.ValidationError("Producer must provide Transaction Proof document")
                
                if 'producer_transfer_proof' in request.FILES and not self.instance.is_approved and not self.instance.status == 'approved':
                        raise serializers.ValidationError("Producer Transfer Proof can only be uploaded after transaction is approved by Superadmin")
                
                if self.instance.producer_transfer_proof and request.FILES.get('producer_transfer_proof'):
                    raise serializers.ValidationError("Producer Transfer Proof can only be uploaded once")
                if self.instance.transaction_proof and request.FILES.get('transaction_proof'):
                    raise serializers.ValidationError("Transaction Proof can only be uploaded once")
            
            # Recycler check
            elif isinstance(user, Recycler):
                allowed_fields = {'trail_documents', 'recycler_transfer_proof'}
                combined_keys = set(data.keys()) | set(request.FILES.keys())
                if any(k not in allowed_fields for k in combined_keys):
                    raise serializers.ValidationError("Recycler can only update 'trail_documents' and 'recycler_transfer_proof'")
                if not self.instance.is_approved:
                    raise serializers.ValidationError("Transaction must be approved by Superadmin before Recycler can upload documents")
                if 'trail_documents' not in request.FILES or 'recycler_transfer_proof' not in request.FILES:
                    raise serializers.ValidationError("Trail Documents and Transafer Proof both are required from Recycler")
                if self.instance.trail_documents and request.FILES.get('trail_documents'):
                    raise serializers.ValidationError("Trail Documents can only be uploaded once")
                if self.instance.recycler_transfer_proof and request.FILES.get('recycler_transfer_proof'):  
                    raise serializers.ValidationError("Recycler Transfer Proof can only be uploaded once")
            
            else:
                raise serializers.ValidationError("Unauthorized to update transaction")
        
        else:  # Create
            if not isinstance(request.user, Producer):
                raise serializers.ValidationError("Only producer can create transaction")
        
        return data

    def update(self, instance, validated_data):
        request = self.context["request"]
        
        if isinstance(request.user, Producer):
            instance.transaction_proof = request.FILES.get('transaction_proof', instance.transaction_proof)
            instance.producer_transfer_proof = request.FILES.get('producer_transfer_proof', instance.producer_transfer_proof)
        
        elif isinstance(request.user, Recycler):
            instance.trail_documents = request.FILES.get('trail_documents', instance.trail_documents)
            instance.recycler_transfer_proof = request.FILES.get('recycler_transfer_proof', instance.recycler_transfer_proof)
            instance.is_complete = True
        
        elif isinstance(request.user, SuperAdmin):
            instance.is_approved = validated_data.get('is_approved', instance.is_approved)
            instance.status = validated_data.get('status', instance.status)
        
        instance.save()
        return instance
    


# WASTE FILTER 
class ProducerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProducerType
        fields = ['name']

class RecyclerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecyclerType
        fields = ['name']

class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ['name']

class CreditTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditType
        fields = ['name']

class WasteTypeSerializer(serializers.ModelSerializer):
    producer_types = ProducerTypeSerializer(many=True)
    recycler_types = RecyclerTypeSerializer(many=True)
    product_types = ProductTypeSerializer(many=True)
    credit_types = CreditTypeSerializer(many=True)

    class Meta:
        model = WasteType
        fields = ['name', 'producer_types', 'recycler_types', 'product_types', 'credit_types']


class WasteTypeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteType
        fields = ['name']