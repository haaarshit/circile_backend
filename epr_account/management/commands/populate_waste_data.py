from django.core.management.base import BaseCommand
from epr_account.models import WasteType, ProducerType, RecyclerType, ProductType, CreditType

class Command(BaseCommand):
    help = 'Populates the database with waste type data'

   
    WASTE_CHOICES = {
    "Plastic": {
        "producer_types": ["Producer (P)", "Importer (I)", "Brand Owner (BO)"],
        "recycler_types": ["Recycler", "Co-processor (Cement)", "Co-processor (WtE)", "Co-processor (WtO)", "Industrial Composting"],
        "product_types": ["Category I", "Category II", "Category III", "Category IV"],
        "credit_types": [
        "Recycling ",
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


    def handle(self, *args, **options):
        for waste_name, data in self.WASTE_CHOICES.items():
            waste_type, created = WasteType.objects.get_or_create(name=waste_name)
            
            # Producer Types
            for producer in data['producer_types']:
                ProducerType.objects.get_or_create(waste_type=waste_type, name=producer)
            
            # Recycler Types
            for recycler in data['recycler_types']:
                RecyclerType.objects.get_or_create(waste_type=waste_type, name=recycler)
            
            # Product Types
            for product in data['product_types']:
                ProductType.objects.get_or_create(waste_type=waste_type, name=product)
            
            # Credit Types
            for credit in data['credit_types']:
                CreditType.objects.get_or_create(waste_type=waste_type, name=credit)
                
        self.stdout.write(self.style.SUCCESS('Successfully populated waste type data'))