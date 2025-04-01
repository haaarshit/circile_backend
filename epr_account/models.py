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



product_credit_type_for_e_waste = ["EEE Code wise","ITEW1 - Centralized Data Processing: Mainframe and Minicomputers",
                                        "ITEW2 - Personal Computing: Personal Computers (Central Processing Unit with input and output devices)",
                                        "ITEW3 - Personal Computing: Laptop Computers (Central Processing Unit with input and output devices)",
                                        "ITEW4 - Personal Computing: Notebook Computers",
                                        "ITEW5 - Personal Computing: Notepad Computers",
                                        "ITEW6 - Printers including Cartridges",
                                        "ITEW7 - Copying Equipment",
                                        "ITEW8 - Electrical and Electronic Typewriters",
                                        "ITEW9 - User Terminals and Systems",
                                        "ITEW10 - Facsimile",
                                        "ITEW11 - Telex",
                                        "ITEW12 - Telephones",
                                        "ITEW13 - Pay Telephones",
                                        "ITEW14 - Cordless Telephones",
                                        "ITEW15 - Cellular Telephones: Feature Phones and Smartphones",
                                        "ITEW16 - Answering Systems",
                                        "ITEW17 - Products or equipment of Transmitting sound, images or other information by Telecommunications and Bluetooth enabled devices",
                                        "ITEW18 - BTS (all components excluding structure of tower)",
                                        "ITEW19 - Tablets, I-PAD",
                                        "ITEW20 - Phablets",
                                        "ITEW21 - Scanners",
                                        "ITEW22 - Routers - Routers, Access Point and Controller, LAN Switches, SDWAN, IoT Gateway, etc.",
                                        "ITEW23 - GPS",
                                        "ITEW24 - UPS - up to 2 KVA and greater than 2 KVA",
                                        "ITEW25 - INVERTER - up to 2 KVA and greater than 2 KVA",
                                        "ITEW26 - Modems",
                                        "ITEW27 - ELECTRONIC DATA STORAGE DEVICES FOR FLASH DRIVE (SMALL DEVICES) and large drive like server",
                                        "CEEW1 - Television sets (including sets based on Liquid Crystal Display and Light Emitting Diode technology)",
                                        "CEEW2 - Refrigerator",
                                        "CEEW3 - Washing Machine",
                                        "CEEW4 - Air-conditioners excluding Centralized Air Conditioning Plants",
                                        "CEEW5 - Fluorescent and other Mercury containing lamps",
                                        "CEEW6 - Screen, Electronic Photo Frames, Electronic Display Panel, Monitors",
                                        "CEEW7 - Radio Sets",
                                        "CEEW8 - Set Top Boxes",
                                        "CEEW9 - Video Cameras",
                                        "CEEW10 - Video Recorders",
                                        "CEEW11 - Hi-Fi Recorders",
                                        "CEEW12 - Audio Amplifiers - Speakers, Multi Media Speaker, Home Theatre, Sound Bar, Wireless Speaker, etc.",
                                        "CEEW13 - Other Products or Equipment for the purpose of recording or reproducing sound or images including signals and other technologies for the distribution of sound and image by telecommunications",
                                        "CEEW14 - Solar Panels/Cells, Solar Photovoltaic Panels/Cells/Modules",
                                        "CEEW15 - Luminaires for fluorescent lamps with the exception of luminaires in households",
                                        "CEEW16 - High intensity discharge lamps, including Pressure Sodium Lamps and Metal Halide Lamps",
                                        "CEEW17 - Low pressure Sodium Lamps",
                                        "CEEW18 - Other lighting or equipment for the purpose of spreading or controlling light excluding Filament Bulbs - LED Bulbs/Tubes/Consumer Luminaries & Consumer LED Drives, Professionals Luminaries & Drives",
                                        "CEEW19 - Digital Camera",
                                        "LSEEW1 - Large cooling appliances",
                                        "LSEEW2 - Freezers",
                                        "LSEEW3 - Other large appliances used for refrigeration, conservation and storage of food",
                                        "LSEEW4 - Clothes Dryers",
                                        "LSEEW5 - Dish Washing Machines",
                                        "LSEEW6 - Electric Cookers",
                                        "LSEEW7 - Electric Stoves",
                                        "LSEEW8 - Electric Hot Plates",
                                        "LSEEW9 - Microwaves, Microwave Oven",
                                        "LSEEW10 - Other large appliances used for cooking and other processing of food",
                                        "LSEEW11 - Electric Heating Appliances",
                                        "LSEEW12 - Electric Radiators",
                                        "LSEEW13 - Other large appliances for heating Rooms, Beds, Seating Furniture",
                                        "LSEEW14 - Electric Fans",
                                        "LSEEW15 - Other Fanning, Exhaust Ventilation and Conditioning Equipment",
                                        "LSEEW16 - Vacuum Cleaners",
                                        "LSEEW17 - Carpet Sweepers",
                                        "LSEEW18 - Other appliances for cleaning",
                                        "LSEEW19 - Appliances used for sewing, knitting, weaving and other processing for textiles",
                                        "LSEEW20 - Iron and other appliances for ironing, mangling and other care of clothing - Dry Iron, Steam Iron/Garment Steamer",
                                        "LSEEW21 - Grinders, Coffee Machines and equipment for opening or sealing containers or packages",
                                        "LSEEW22 - Smoke Detector",
                                        "LSEEW23 - Heating Regulators",
                                        "LSEEW24 - Thermostats",
                                        "LSEEW25 - Automatic Dispensers for hot drinks",
                                        "LSEEW26 - Automatic Dispensers for hot or cold bottles or cans",
                                        "LSEEW27 - Automatic Dispensers for solid products",
                                        "LSEEW28 - Automatic Dispensers for money",
                                        "LSEEW29 - All appliances which deliver automatically all kinds of products",
                                        "LSEEW30 - Indoor Air Purifier",
                                        "LSEEW31 - Hair Dryer",
                                        "LSEEW32 - Electric Shaver",
                                        "LSEEW33 - Electric Kettle",
                                        "LSEEW34 - Electronic Display Panels/Board/Visual Display Unit",
                                        "EETW1 - Drills",
                                        "EETW2 - Saws",
                                        "EETW3 - Sewing Machines",
                                        "EETW4 - Equipment for turning, milling, sanding, grinding, sawing, cutting, shearing, drilling, making holes, punching, folding, bending or similar processing of wood, metal and other materials",
                                        "EETW5 - Tools for riveting, nailing or screwing or removing rivets, nails, screws or similar uses",
                                        "EETW6 - Tools for welding, soldering, or similar use",
                                        "EETW7 - Equipment for spraying, spreading, dispersing or other treatment of liquid or gaseous substance by other means",
                                        "EETW8 - Tools for mowing or other gardening activities",
                                        "TLSEW1 - Electrical Trains or Car Racing Sets",
                                        "TLSEW2 - Hand-held Video Games Consoles",
                                        "TLSEW3 - Video Games",
                                        "TLSEW4 - Computers for biking, diving, running, rowing, etc.",
                                        "TLSEW5 - Sports Equipment with Electric or Electronic Components",
                                        "TLSEW6 - Coin Slot Machines",
                                        "MDW1 - Radiotherapy Equipment and Accessories",
                                        "MDW2 - Cardiology Equipment and Accessories",
                                        "MDW3 - Dialysis Equipment and Accessories",
                                        "MDW4 - Pulmonary Ventilators and Accessories - Diagnostic Cardiology, Anaesthesia & Respiratory",
                                        "MDW5 - Nuclear Medicine Equipment and Accessories",
                                        "MDW6 - Laboratory Equipment for in Vitro Diagnosis and Accessories",
                                        "MDW7 - Analysers and Accessories",
                                        "MDW8 - MRI, PET, CT Scanner, & Ultrasound Equipment along with accessories",
                                        "MDW9 - Fertilization Tests Equipment and Accessories",
                                        "MDW10 - Other Electric Appliances/Equipment/Kits used for preventing, screening, detecting, monitoring, evaluating, treating illnesses and conditions",
                                        "LIW1 - Gas Analyser",
                                        "LIW2 - Equipment having Electrical and Electronic Components"
]

producer_types_for_oil = [
    "P1 - Manufactures and Sells Base Oil",
    "P2 - Importer of Base Oil",
    "P3 - Manufactures Base Oil & Sells Lubrication Oil under its brand/Co-brand",
    "P4 - Importer of Lubrication Oil",
    "P5 - Procures Base Oil domestically and sells Base Oil & its products under its brand /Co-brand",
    "P6 - Procures Lubrication Oil domestically and sells under its brand/Co-brand",
    "P7 - Procures Base Oil domestically and sells Lubrication Oil under its brand/ Co-brand",
    "P8 - Procures Rerefined/Recycled Base Oil domestically and sells Lubrication Oil under its brand/ Co-brand",
    "P9 - Manufactures and sells Re-refined /Recycled Base Oil under its brand/ Co-brand"
    ]

WASTE_CHOICES = {
  "Plastic": {
    "producer_types": ["Producer (P)", "Importer (I)", "Brand Owner (BO)"],
    "recycler_types": ["Recycler", "Co-processor (Cement)", "Co-processor (WtE)", "Co-processor (WtO)", "Industrial Composting"],
    "product_types": ["Category I", "Category II", "Category III", "Category IV"],
    "credit_types": [
      "Recycling",
      "EoL",
    ]
  },
  "E-waste": {
    "producer_types": ["Producer (PEW)", "Manufacturer"],
    "recycler_types": ["Recycler (REW)", "Refurbisher (RfEW)"],
    "product_types":product_credit_type_for_e_waste,
    "credit_types": [
        "Aluminium (Al)",
        "Iron (Fe)",
        "Copper (Cu)",
        "Gold (Au)",
        ]+ product_credit_type_for_e_waste
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
    "producer_types": producer_types_for_oil,
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
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
   
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='epr_accounts')


    epr_registration_number = models.CharField(max_length=50, unique=True)
    epr_registration_date = models.DateField()
    epr_registered_name = models.CharField()

    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    recycler_type = models.CharField()
    epr_certificate = CustomCloudinaryField('file')
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)  
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    
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
      
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
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
    epr_registered_name = models.CharField(max_length=100)

    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    producer_type = models.CharField()
    epr_certificate = CustomCloudinaryField('file')
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False) 
     


    def clean(self):
        if self.waste_type in WASTE_CHOICES:
            valid_producer_types = WASTE_CHOICES[self.waste_type]['producer_types']
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
    product_type = models.CharField()
    credit_type = models.CharField()
    year = models.DateTimeField()
    processing_capacity =models.DecimalField(max_digits=10, decimal_places=2)
    comulative_certificate_potential = models.FloatField()
    available_certificate_value = models.FloatField()
    state = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

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

    product_type = models.CharField()
    credit_type = models.CharField()
    FY =  models.IntegerField()
    target_quantity = models.IntegerField() # in kgs
    state = models.CharField(max_length=100)

    achieved_quantity = models.IntegerField(default=0)  # New field
    is_achieved = models.BooleanField(default=False) 

    created_at = models.DateTimeField(default=timezone.now)

    
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
    is_approved = models.BooleanField(default=True)  
    
    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    FY = models.IntegerField(default=get_default_year)
    offer_title = models.CharField(max_length=255, default="Default Offer")
    credit_available = models.FloatField(default=0.0)  
    minimum_purchase = models.FloatField(default=0.0)
    price_per_credit = models.FloatField(default=0.0)
    product_image = CloudinaryField('image', resource_type='image', default="")
    availability_proof = CloudinaryField('image', resource_type='image', default="")
    credit_type = models.CharField()
    product_type = models.CharField()
    is_sold = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)



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
    FY = models.IntegerField(default=get_default_year)
    is_approved = models.BooleanField(default=False)  
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")  

    is_complete = models.BooleanField(default=False)  # New field added



    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        pass
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class PurchasesRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    
    recycler = models.ForeignKey(
        'users.Recycler', 
        on_delete=models.CASCADE, 
        related_name='purchase_request_recycler_transactions'
    )
    producer = models.ForeignKey(
        'users.Producer', 
        on_delete=models.CASCADE, 
        related_name='purchase_request_producer_transactions'
    )
    
    
    credit_offer = models.ForeignKey(
        CreditOffer,  
        on_delete=models.CASCADE,
        related_name='purchase_request',
        null=True,
        blank=True
    )

    producer_epr = models.ForeignKey(
        ProducerEPR, 
        on_delete=models.CASCADE, 
        related_name='purchase_request_epr_transactions',
         null=True,  
         blank=True  
    )
    FY = models.IntegerField(default=get_default_year)
    quantity = models.FloatField(default=0.0) 


    is_approved = models.BooleanField(default=False) 
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_complete = models.BooleanField(default=False)  # New field added

    created_at = models.DateTimeField(default=timezone.now)





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
    credit_type = models.CharField()
    waste_type = models.CharField(max_length=20)
    recycler_type = models.CharField()
    price_per_credit = models.FloatField()
    product_type = models.CharField()
    producer_type = models.CharField()
    credit_quantity = models.FloatField()
    offered_by = models.CharField(max_length=20)
    
    work_order_date = models.DateTimeField(auto_now_add=True)
  
    is_complete = models.BooleanField(default=False)

    # approved by superadmin
    is_approved = models.BooleanField(default=False) 
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )


    # producer
    transaction_proof = CloudinaryField(
        'transaction_proof',
        resource_type='raw',  
        blank=True,
        null=True
    )

    producer_transfer_proof = CloudinaryField(
        'producer_transfer_proof',
        resource_type='raw',  
        blank=True,
        null=True
    )

    # recycler
    trail_documents = CloudinaryField(
        'trail_documents',
        resource_type='raw',  
        blank=True,
        null=True
    )

    recycler_transfer_proof = CloudinaryField(
        'recycler_transfer_proof',
        resource_type='raw',  
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(default=timezone.now)


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
        
        if not self.is_approved:

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
    name = models.CharField()

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"

class RecyclerType(models.Model):
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name='recycler_types')
    name = models.CharField()

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"

class ProductType(models.Model):
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name='product_types')
    name = models.CharField()

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"

class CreditType(models.Model):
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name='credit_types')
    name = models.CharField()

    def __str__(self):
        return f"{self.name} ({self.waste_type.name})"