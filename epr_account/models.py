from django.db import models,transaction
import uuid
from django.core.exceptions import ValidationError
from django.db.models import Max

from cloudinary.models import CloudinaryField
from django.core.validators import MinLengthValidator
from django.utils import timezone
import datetime


class CustomCloudinaryField(CloudinaryField):
     pass


WASTE_CHOICES = {
  "Plastic": {
    "producer_types": ["Producer (P)", "Importer (I)", "Brand Owner (BO)"],
    "recycler_types": ["Recycler", "Co-processor (Cement)", "Co-processor (WtE)", "Co-processor (WtO)", "Industrial Composting"],
    "product_types": ["Category I", "Category II", "Category III", "Category IV"],
    "credit_types": [
      "Recycling",
      "EoL",
      "EoL"
    ]
  },
  "E-waste": {
    "producer_types": ["Producer (PEW)", "Manufacturer"],
    "recycler_types": ["Recycler (REW)", "Refurbisher (RfEW)"],
    "product_types": [
      "Information technology and telecommunication equipment (ITEW)",
      "Consumer electrical and electronics and Photovoltaic Panels (CEEW)",
      "Large and Small Electrical and Electronic Equipment (LSEEW)",
      "Electrical and Electronic Tools (EETW)",
      "Toys, Leisure and Sports Equipment (TLSEW)",
      "Medical Devices (MDW)",
      "Laboratory Instruments (LIW)"
    ],
    "credit_types": [
      "Aluminium (Al)",
      "Iron (Fe)",
      "Copper (Cu)",
      "Gold (Au)",
      "EEE code-wise"
    ]
  },
  "Battery": {
    "producer_types": ["Producer (PBW)"],
    "recycler_types": ["Recycler (R)", "Refurbisher (Refurb)"],
    "product_types": ["Portable Battery", "Automotive Battery", "Industrial Battery", "EV Battery"],
    "credit_types": [
      "Lead (Pb)",
      "Lithium (Li)",
      "Cobalt (Co)",
      "Nickel (Ni)",
      "Manganese (Mn)",
      "Zinc (Zn)",
      "Copper (Cu)",
      "Cadmium (Cd)",
      "Aluminium (Al)",
      "Iron (Fe)"
    ]
  },
  "Tyre": {
    "producer_types": ["Producer (PWT)"],
    "recycler_types": ["Recycler (RWT)", "Retreader (RtWT)"],
    "product_types": ["Domestic New Tyre", "Imported New Tyre", "Imported Waste Tyre"],
    "credit_types": [
      "Reclaimed Rubber (ReR)",
      "Recovered Carbon Black-(RCB)",
      "Crumb Rubber Modified Bitumen (CRMB)",
      "Crumb Rubber (CR)",
      "Pyrolysis Oil and Char-(PO&C)",
      "Retreading Certificate"
    ]
  },
  "Oil": {
    "producer_types": ["P1: Manufactures and sells base oil", "P2"],
    "recycler_types": ["Recyclers", "Co-processors (Energy Recovery)", "Co-processors (Resource Recovery)"],
    "product_types": [
      "Virgin base oil",
      "White Oil",
      "Hydraulic Oil",
      "Transformer Oil",
      "Cutting Oil",
      "Rubber Processing Oil",
      "Thermal Fluids"
    ],
    "credit_types": [
      "Recycling",
      "Co-processing (ER)",
      "Co-processing (RR)"
    ]
  }
}

def get_current_year_start():
    return datetime.date.today().replace(month=1, day=1)

class RecyclerEPR(models.Model):
   
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='epr_accounts')

    epr_registration_number = models.CharField(max_length=50, unique=True)
    epr_registration_date = models.DateField()
    epr_registered_name = models.CharField(max_length=50)

    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    recycler_type = models.CharField(max_length=100)
    epr_certificate = CustomCloudinaryField('file')
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if self.waste_type in WASTE_CHOICES:
            valid_recycler_types = WASTE_CHOICES[self.waste_type]['recycler_types']
            if self.recycler_type not in valid_recycler_types:
                raise ValidationError(f"Invalid Recycler Type '{self.recycler_type}' for Waste Type '{self.waste_type}'")
            pass
        else:
            raise ValidationError(f"Waste TYpe can be only tyoe type of {WASTE_CHOICES}")
            

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class ProducerEPR(models.Model):
    PRODUCER_CHOICES = {
    'Plastic': ['Producer (P)', 'Importer (I)', 'Brand Owner (BO)'],
    'E-waste': ['Producer (PEW)', 'Manufacturer', 'Importer', 'Bulk Consumer'],
    'Battery': ['Battery Manufacturer', 'Battery Importer', 'Battery Assembler'],
    'Tyre': ['Tyre Manufacturer', 'Tyre Importer', 'Tyre Brand Owner'],
    'Oil': ['Oil Producer', 'Oil Importer', 'Oil Refiner'],
    }
    
    producer = models.ForeignKey('users.Producer', on_delete=models.CASCADE, related_name='epr_accounts')
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    
    epr_registration_number = models.CharField(max_length=50, unique=True)
    epr_registration_date = models.DateField()
    epr_registered_name = models.CharField(max_length=50)

    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in PRODUCER_CHOICES.keys()])
    producer_type = models.CharField(max_length=100)
    epr_certificate = CustomCloudinaryField('file')
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.waste_type in self.PRODUCER_CHOICES:
            valid_producer_types = self.PRODUCER_CHOICES[self.waste_type]
            if self.producer_type not in valid_producer_types:
                raise ValidationError(f"Invalid Producer Type '{self.producer_type}' for Waste Type '{self.waste_type}'")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)    

# ONLY FOR REDUCER
class EPRCredit(models.Model):

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='recycler_epr_credits')
    epr_account = models.ForeignKey(RecyclerEPR, on_delete=models.CASCADE, related_name='epr_account_credits')
    epr_registration_number = models.CharField(max_length=50)
    
    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    product_type = models.CharField(max_length=100)
    credit_type = models.CharField(max_length=100)
    year = models.DateTimeField()
    processing_capacity =models.DecimalField(max_digits=10, decimal_places=2)
    comulative_certificate_potential = models.FloatField()
    available_certificate_value = models.FloatField()
    state = models.CharField(max_length=100)

    def clean(self):
        if self.waste_type in WASTE_CHOICES:
            valid_product_types = WASTE_CHOICES[self.waste_type]['product_types']
            valid_credit_types = WASTE_CHOICES[self.waste_type]['credit_types']


            if self.product_type not in valid_product_types:
                raise ValidationError(f"Invalid Product Type '{self.product_type}' for Waste Type '{self.waste_type}'")

            if self.credit_type not in valid_credit_types:
                raise ValidationError(f"Invalid Credit Type '{self.credit_type}' for Waste Type '{self.waste_type}'")
            

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# ONLY FOR PRODUCER
class EPRTarget(models.Model):

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    producer = models.ForeignKey('users.Producer', on_delete=models.CASCADE, related_name='producer_epr_targets')
    epr_account = models.ForeignKey(ProducerEPR, on_delete=models.CASCADE, related_name='epr_account_targets')
    epr_registration_number = models.CharField(max_length=50)
    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])

    product_type = models.CharField(max_length=100)
    credit_type = models.CharField(max_length=100)
    FY =  models.IntegerField()
    target_quantity = models.IntegerField() # in kgs
    achieved_quantity = models.IntegerField(default=0)  # New field
    is_achieved = models.BooleanField(default=False)  # New field
    state = models.CharField(max_length=100)

    
    def clean(self):
        if self.waste_type in WASTE_CHOICES:
            valid_product_types = WASTE_CHOICES[self.waste_type]['product_types']
            valid_credit_types = WASTE_CHOICES[self.waste_type]['credit_types']


            if self.product_type not in valid_product_types:
                raise ValidationError(f"Invalid Product Type '{self.product_type}' for Waste Type '{self.waste_type}'")

            if self.credit_type not in valid_credit_types:
                raise ValidationError(f"Invalid Credit Type '{self.credit_type}' for Waste Type '{self.waste_type}'")
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

def validate_doc_choices(value):
    allowed_docs = [
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
    ]
    
    # Check if all values are in allowed_docs
    invalid_docs = [doc for doc in value if doc not in allowed_docs]
    if invalid_docs:
        raise ValidationError(
            f"Invalid document types: {', '.join(invalid_docs)}. "
            f"Must be from: {', '.join(allowed_docs)}"
        )

def get_default_supporting_docs():
    return [
        "Tax Invoice",
        "Recycling Certificate Copy",
        "Co-Processing Certificate",
        "Credit Transfer Proof",
        "EPR Registration Certificate"
    ]

def get_default_year():
    return timezone.now().year

# CREDIT OFFER BY RECYLER
class CreditOffer(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='recycler_credit_offers')
    epr_account = models.ForeignKey(RecyclerEPR, on_delete=models.CASCADE, related_name='epr_account_credit_offers')
    epr_credit = models.ForeignKey(EPRCredit, on_delete=models.CASCADE, related_name='epr_credit_offers')
    # populate from credit record
    epr_registration_number = models.CharField(max_length=50)
    # approved super admin
    is_approved = models.BooleanField(default=False)  
    

    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    FY = models.IntegerField(default=get_default_year)
    offer_title = models.CharField(max_length=255, default="Default Offer")
    credit_available = models.FloatField(default=0.0)  
    minimum_purchase = models.FloatField(default=0.0)
    price_per_credit = models.FloatField(default=0.0)
    product_image = CloudinaryField('image', resource_type='image', default="")
    availability_proof = CloudinaryField('image', resource_type='image', default="")
    credit_type = models.CharField(max_length=100)
    product_type = models.CharField(max_length=100)
    is_sold = models.BooleanField(default=False)


    # TODO -> TRAIL DOCUMENT
    trail_documents = models.JSONField(
        default=get_default_supporting_docs,
        validators=[
            validate_doc_choices
        ]
    )

    def clean(self):
        if self.waste_type in WASTE_CHOICES:
            valid_product_types = WASTE_CHOICES[self.waste_type]['product_types']
            valid_credit_types = WASTE_CHOICES[self.waste_type]['credit_types']


            if self.product_type not in valid_product_types:
                raise ValidationError(f"Invalid Product Type '{self.product_type}' for Waste Type '{self.waste_type}'")

            if self.credit_type not in valid_credit_types:
                raise ValidationError(f"Invalid Credit Type '{self.credit_type}' for Waste Type '{self.waste_type}'")
            
    def save(self, *args, **kwargs):
        # if self.epr_credit and not self.credit_type:
        #     self.credit_type = self.epr_credit.credit_type
        super().save(*args, **kwargs)

# COUNTER CREDIT OFFER BY PRODUCER
class CounterCreditOffer(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    producer = models.ForeignKey('users.Producer', on_delete=models.CASCADE, related_name='producer_counter_credit_offer')
    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='recycler_counter_credit_offers')
    credit_offer = models.ForeignKey(CreditOffer, on_delete=models.CASCADE, related_name='counter_credit_offers')
    
    # hard entry from user
    producer_epr = models.ForeignKey(ProducerEPR,on_delete=models.CASCADE,related_name="counter_credit_offers")
    quantity = models.FloatField(blank=False) 
    offer_price = models.FloatField(blank=False)

    is_approved = models.BooleanField(default=False)  
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")  
    def clean(self):
        pass
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    order_id = models.CharField(
        max_length=8,  
        unique=True,
        editable=False,
        null=False,
        blank=False
    )
    
    recycler = models.ForeignKey(
        'users.Recycler', 
        on_delete=models.CASCADE, 
        related_name='recycler_transactions'
    )
    producer = models.ForeignKey(
        'users.Producer', 
        on_delete=models.CASCADE, 
        related_name='producer_transactions'
    )
    
    producer_epr = models.ForeignKey(
        ProducerEPR, 
        on_delete=models.CASCADE, 
        related_name='epr_transactions',
         null=True,  # Uncomment this temporarily for debugging if needed
         blank=True  # Uncomment this temporarily for debugging if needed
    )

    credit_offer = models.ForeignKey(
        CreditOffer,  
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    counter_credit_offer = models.ForeignKey(
        CounterCreditOffer,  
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )

    total_price = models.FloatField()
    credit_type = models.CharField(max_length=100)
    waste_type = models.CharField(max_length=20)
    recycler_type = models.CharField(max_length=50)
    price_per_credit = models.FloatField()
    product_type = models.CharField(max_length=100)
    producer_type = models.CharField(max_length=100)
    credit_quantity = models.FloatField()
    offered_by = models.CharField(max_length=20)
    
    work_order_date = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_proof = CloudinaryField(
        'transaction_proof',
        resource_type='raw',  
        blank=True,
        null=True
    )

    def generate_order_id(self):
        # Get the highest existing order_id with 'O' prefix
        last_transaction = Transaction.objects.aggregate(Max('order_id'))['order_id__max']
        if last_transaction:
            # Extract the numeric part (e.g., 'O0000012' -> '0000012')
            last_number = int(last_transaction[1:])  # Skip the 'O' prefix
            new_number = last_number + 1
        else:
            new_number = 1  # Start at 1 if no 
        
        return f'O{new_number:07d}'  # e.g., O0000001, O0000002, etc.

    def save(self, *args, **kwargs):
        if not self.order_id:
            with transaction.atomic():
                # Lock the table to ensure uniqueness in concurrent scenarios
                locked_transactions = Transaction.objects.select_for_update().all()
                self.order_id = self.generate_order_id()
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        if (not self.credit_offer and self.counter_credit_offer) or (not self.credit_offer and not self.counter_credit_offer):
            raise ValidationError("Transaction must be linked to either a CreditOffer or CounterCreditOffer")
        
        if self.credit_quantity > self.credit_offer.credit_available:
            raise ValidationError(
                f"Credit quantity ({self.credit_quantity}) exceeds available credits ({self.credit_offer.credit_available})"
            )
        
        if self.counter_credit_offer and self.credit_quantity != self.counter_credit_offer.quantity:
            raise ValidationError(
                f"Credit quantity ({self.credit_quantity}) must equal counter credit offer quantity ({self.counter_credit_offer.quantity})"
            )
        

# WASTE FILTER API

class WasteType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Plastic, E-waste, Battery, etc.

    def __str__(self):
        return self.name

class ProducerType(models.Model):
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name='producer_types')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"

class RecyclerType(models.Model):
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name='recycler_types')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"

class ProductType(models.Model):
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name='product_types')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"

class CreditType(models.Model):
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name='credit_types')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"