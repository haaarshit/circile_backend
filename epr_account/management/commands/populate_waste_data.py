from django.core.management.base import BaseCommand
from epr_account.models import WasteType, ProducerType, RecyclerType, ProductType, CreditType

class Command(BaseCommand):
    help = 'Populates the database with waste type data'

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


    def handle(self, *args, **options):
          # Delete all existing records
        WasteType.objects.all().delete()
        ProducerType.objects.all().delete()
        RecyclerType.objects.all().delete()
        ProductType.objects.all().delete()
        CreditType.objects.all().delete()

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