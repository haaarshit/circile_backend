from django.db import models
import uuid
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField

class CustomCloudinaryField(CloudinaryField):
     pass


WASTE_CHOICES = {
  "Plastic": {
    "producer_types": ["Producer (P)", "Importer (I)", "Brand Owner (BO)"],
    "recycler_types": ["Recycler", "Co-processor (Cement)", "Co-processor (WtE)", "Co-processor (WtO)", "Industrial Composting"],
    "product_types": ["Category I", "Category II", "Category III", "Category IV"],
    "credit_types": [
      "Recycling (Cat I, II, III)",
      "EoL (Cat I, II, III, IV)",
      "EoL (Cat IV)"
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

class RecyclerEPR(models.Model):
    # WASTE_CHOICES = {
    # 'Plastic': {
    #     'recycler_types': ['Plastic Recycler A', 'Plastic Recycler B', 'Shredder', 'Pelletizer'],
    # },
    # 'E-waste': {
    #     'recycler_types': ['E-waste Processor', 'Refurbisher', 'Dismantler'],
    # },
    # 'Battery': {
    #     'recycler_types': ['Battery Recycler', 'Battery Smelter', 'Lead Acid Processor'],
    # },
    # 'Tyre': {
    #     'recycler_types': ['Tyre Shredder', 'Crumb Rubber Processor', 'Tyre Pyrolysis Unit'],
    # },
    # 'Oil': {
    #     'recycler_types': ['Waste Oil Collector', 'Oil Refinery', 'Oil Re-processor'],
    # }
    # }
    # WASTE_CHOICES = ('Plastic','E-waste','Battery','Tyre','Oil')

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='epr_accounts')

    epr_registration_number = models.CharField(max_length=50, unique=True)
    epr_registration_date = models.DateField()

    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    recycler_type = models.CharField(max_length=100)
    epr_certificate = CustomCloudinaryField('file')
    company_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    
    def clean(self):
        if self.waste_type in self.WASTE_CHOICES:
            valid_recycler_types = self.WASTE_CHOICES[self.waste_type]['recycler_types']

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
    company_name = models.CharField(max_length=255)
    epr_registration_date = models.DateField()

    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in PRODUCER_CHOICES.keys()])
    producer_type = models.CharField(max_length=100)
    epr_certificate = CustomCloudinaryField('file')
    gst_number = models.CharField(max_length=15)
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
    # WASTE_CHOICES = {   
    #     'Plastic': {
    #         'product_types': ['Category I','Category II','Category III','Category IV',],
    #         'credit_types': ['Recycled Plastic Credit', 'Processed Plastic Credit']
    #     },
    # 'E-waste': {
    #     'product_types': ['Motherboards', 'Hard Drives', 'Laptops', 'Mobile Phones'],
    #     'credit_types': ['E-waste Recycling Credit', 'E-waste Processing Credit']
    # },
    # 'Battery': {
    #     'product_types': ['Lithium-Ion Battery', 'Lead-Acid Battery', 'Nickel-Cadmium Battery'],
    #     'credit_types': ['Battery Recycling Credit', 'Battery Collection Credit']
    # },
    # 'Tyre': {
    #     'product_types': ['Rubber Powder', 'Crumb Rubber', 'Tyre Derived Fuel (TDF)'],
    #     'credit_types': ['Tyre Recycling Credit', 'Rubber Recovery Credit']
    # },
    # 'Oil': {
    #     'product_types': ['Used Engine Oil', 'Lubricating Oil', 'Transformer Oil'],
    #     'credit_types': ['Oil Recycling Credit', 'Oil Collection Credit']
    # }
    # }
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='recyler')
    epr_account = models.ForeignKey(RecyclerEPR, on_delete=models.CASCADE, related_name='epr_accounts')
    epr_registration_number = models.CharField(max_length=50)
    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])

    product_type = models.CharField(max_length=100)
    credit_type = models.CharField(max_length=100)
    year = models.DateTimeField()
    processing_capacity =models.DecimalField(max_digits=10, decimal_places=2)
    comulative_certificate_potential = models.CharField(max_length=250)
    available_certificate_value = models.CharField(max_length=250)

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
    producer = models.ForeignKey('users.Producer', on_delete=models.CASCADE, related_name='producer')
    epr_account = models.ForeignKey(ProducerEPR, on_delete=models.CASCADE, related_name='epr_accounts')
    epr_registration_number = models.CharField(max_length=50)
    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])

    product_type = models.CharField(max_length=100)
    credit_type = models.CharField(max_length=100)
    FY = models.IntegerField()
    target_quantity = models.IntegerField() # in kgs
    
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

# CREDIT OFFER BY RECYLER
class CreditOffer(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    recycler = models.ForeignKey('users.Recycler', on_delete=models.CASCADE, related_name='recyler')
    epr_account = models.ForeignKey(ProducerEPR, on_delete=models.CASCADE, related_name='epr_accounts')
    epr_credit = models.ForeignKey(EPRCredit, on_delete=models.CASCADE, related_name='epr_credit')
    epr_registration_number = models.CharField(max_length=50)
    FY = models.IntegerField()
    waste_type = models.CharField(max_length=20, choices=[(wt, wt) for wt in WASTE_CHOICES.keys()])
    
    

    product_type = models.CharField(max_length=100)
    credit_type = models.CharField(max_length=100)
    target_quantity = models.IntegerField() # in kgs