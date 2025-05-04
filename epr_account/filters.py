# # filters.py
# from django_filters import rest_framework as filters
# from django.db.models import Q
# from django.db import models  # Import models explicitly for JSONField
# from .models import CreditOffer  # Ensure CreditOffer is imported
# from .models import CreditOffer, WasteType, RecyclerType, CreditType, ProductType

# allowed_docs = [
#         "Tax Invoice",
#         "E-wayBIll",
#         "Loading slip",
#         "Unloading Slip",
#         "Lorry Receipt copy",
#         "Recycling Certificate Copy",
#         "Co-Processing Certificate",
#         "Lorry Photographs",
#         "Credit Transfer Proof",
#         "EPR Registration Certificate"
# ]

# class CreditOfferFilter(filters.FilterSet):
#     waste_type = filters.CharFilter(field_name='waste_type', lookup_expr='iexact')
#     recycler_type = filters.CharFilter(field_name='epr_account__recycler_type', lookup_expr='iexact')
#     state = filters.CharFilter(field_name='epr_account__state', lookup_expr='iexact')
#     city = filters.CharFilter(field_name='epr_account__city', lookup_expr='iexact')
#     status = filters.CharFilter(field_name='epr_account__status', lookup_expr='iexact')
#     credit_type = filters.CharFilter(field_name='epr_credit__credit_type', lookup_expr='iexact')
#     product_type = filters.CharFilter(field_name='epr_credit__product_type', lookup_expr='iexact')
#     price_per_credit = filters.RangeFilter(field_name='price_per_credit')
#     price_per_credit_exact = filters.NumberFilter(field_name='price_per_credit', lookup_expr='exact')
    
#     # Filter for trail_documents
#     trail_documents = filters.MultipleChoiceFilter(
#         choices=[(doc, doc) for doc in allowed_docs],
#         method='filter_trail_documents',
#         label='Supporting Documents'
#     )

#     # Optional additional filters
#     is_approved = filters.BooleanFilter()
#     FY = filters.RangeFilter()
#     credit_available = filters.RangeFilter()
#     minimum_purchase = filters.RangeFilter()
#     is_sold = filters.BooleanFilter()

#     has_availability_proof = filters.BooleanFilter(
#         method='filter_has_availability_proof',
#         label='Has Availability Proof'
#     )
    
#     def filter_has_availability_proof(self, queryset, name, value):

#         if value is True:
#             return queryset.exclude(availability_proof__exact="").filter(availability_proof__isnull=False)
#         elif value is False:
#             return queryset.filter(Q(availability_proof__exact="") | Q(availability_proof__isnull=True))
#         return queryset

#     def filter_trail_documents(self, queryset, name, value):
#         """
#         Custom filter method to filter CreditOffers where trail_documents contains any of the selected values.
#         """
#         if value:  # Only apply filter if values are provided
#             query = Q()
#             for doc in value:
#                 query |= Q(trail_documents__contains=[doc])  # Check if doc is in the JSON list
#             return queryset.filter(query)
#         return queryset

#     class Meta:
#         model = CreditOffer
#         fields = [
#             'waste_type',
#             'recycler_type',
#             'state',
#             'city',
#             'credit_type',
#             'product_type',
#             'price_per_credit',
#             'status',
#             'price_per_credit_exact',
#             'trail_documents',
#             'is_approved',
#             'FY',
#             'credit_available',
#             'minimum_purchase',
#             'is_sold',
#             'has_availability_proof',
#         ]
#         # Override JSONField handling to avoid AssertionError
#         filter_overrides = {
#             models.JSONField: {  # Use fully qualified models.JSONField
#                 'filter_class': filters.MultipleChoiceFilter,
#                 'extra': lambda f: {
#                     'choices': [(doc, doc) for doc in allowed_docs],
#                     'method': 'filter_trail_documents',  # Link to custom method
#                 },
#             },
#         }

from django_filters import rest_framework as filters
from django.db.models import Q
from django.db import models
from .models import CreditOffer, WasteType, RecyclerType, CreditType, ProductType

# Define allowed documents (unchanged)
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
indian_states =  [
    "Andaman and Nicobar Islands",
    "Haryana",
    "Tamil Nadu",
    "Madhya Pradesh",
    "Jharkhand",
    "Mizoram",
    "Nagaland",
    "Himachal Pradesh",
    "Tripura",
    "Andhra Pradesh",
    "Punjab",
    "Chandigarh",
    "Rajasthan",
    "Assam",
    "Odisha",
    "Chhattisgarh",
    "Jammu and Kashmir",
    "Karnataka",
    "Manipur",
    "Kerala",
    "Delhi",
    "Dadra and Nagar Haveli",
    "Puducherry",
    "Uttarakhand",
    "Uttar Pradesh",
    "Bihar",
    "Gujarat",
    "Telangana",
    "Meghalaya",
    "Himachal Praddesh",
    "Arunachal Pradesh",
    "Maharashtra",
    "Goa",
    "West Bengal"
]
class CreditOfferFilter(filters.FilterSet):
    # Dynamic choices for waste_type
    waste_type = filters.MultipleChoiceFilter(
        choices=[(wt.name, wt.name) for wt in WasteType.objects.all()],
        field_name='waste_type',
        lookup_expr='iexact',
        method='filter_waste_type',
        label='Waste Type'
    )
    # Dynamic choices for recycler_type
    recycler_type = filters.MultipleChoiceFilter(
        choices=[(rt.name, f"{rt.name} ({rt.waste_type.name})") for rt in RecyclerType.objects.all()],
        field_name='epr_account__recycler_type',
        lookup_expr='iexact',
        method='filter_recycler_type',
        label='Recycler Type'
    )
    # Dynamic choices for credit_type
    credit_type = filters.MultipleChoiceFilter(
        choices=[(ct.name, f"{ct.name} ({ct.waste_type.name})") for ct in CreditType.objects.all()],
        field_name='epr_credit__credit_type',
        lookup_expr='iexact',
        method='filter_credit_type',
        label='Credit Type'
    )
    # Dynamic choices for product_type
    product_type = filters.MultipleChoiceFilter(
        choices=[(pt.name, f"{pt.name} ({pt.waste_type.name})") for pt in ProductType.objects.all()],
        field_name='epr_credit__product_type',
        lookup_expr='iexact',
        method='filter_product_type',
        label='Product Type'
    )
    # state = filters.CharFilter(field_name='epr_account__state', lookup_expr='iexact')
    state = filters.MultipleChoiceFilter(
        choices=[(state, state) for state in indian_states],
        field_name='epr_account__state',
        lookup_expr='iexact',
        method='filter_state',
        label='State'
    )
    city = filters.CharFilter(field_name='epr_account__city', lookup_expr='iexact')
    status = filters.CharFilter(field_name='epr_account__status', lookup_expr='iexact')
    price_per_credit = filters.RangeFilter(field_name='price_per_credit')
    price_per_credit_exact = filters.NumberFilter(field_name='price_per_credit', lookup_expr='exact')
    
    # Filter for trail_documents (unchanged)
    trail_documents = filters.MultipleChoiceFilter(
        choices=[(doc, doc) for doc in allowed_docs],
        method='filter_trail_documents',
        label='Supporting Documents'
    )

    # Optional additional filters (unchanged)
    is_approved = filters.BooleanFilter()
    FY = filters.RangeFilter()
    credit_available = filters.RangeFilter()
    minimum_purchase = filters.RangeFilter()
    is_sold = filters.BooleanFilter()

    has_availability_proof = filters.BooleanFilter(
        method='filter_has_availability_proof',
        label='Has Availability Proof'
    )

    def filter_waste_type(self, queryset, name, value):
        """
        Filter CreditOffers where waste_type is any of the selected values.
        """
        if value:
            query = Q()
            for wt in value:
                query |= Q(waste_type__iexact=wt)
            return queryset.filter(query)
        return queryset

    def filter_recycler_type(self, queryset, name, value):
        """
        Filter CreditOffers where epr_account__recycler_type is any of the selected values.
        """
        if value:
            query = Q()
            for rt in value:
                query |= Q(epr_account__recycler_type__iexact=rt)
            return queryset.filter(query)
        return queryset

    def filter_credit_type(self, queryset, name, value):
        """
        Filter CreditOffers where epr_credit__credit_type is any of the selected values.
        """
        if value:
            query = Q()
            for ct in value:
                query |= Q(epr_credit__credit_type__iexact=ct)
            return queryset.filter(query)
        return queryset

    def filter_product_type(self, queryset, name, value):
        """
        Filter CreditOffers where epr_credit__product_type is any of the selected values.
        """
        if value:
            query = Q()
            for pt in value:
                query |= Q(epr_credit__product_type__iexact=pt)
            return queryset.filter(query)
        return queryset

    def filter_has_availability_proof(self, queryset, name, value):
        if value is True:
            return queryset.exclude(availability_proof__exact="").filter(availability_proof__isnull=False)
        elif value is False:
            return queryset.filter(Q(availability_proof__exact="") | Q(availability_proof__isnull=True))
        return queryset

    def filter_trail_documents(self, queryset, name, value):
        """
        Filter CreditOffers where trail_documents contains any of the selected values.
        """
        if value:
            query = Q()
            for doc in value:
                query |= Q(trail_documents__contains=[doc])
            return queryset.filter(query)
        return queryset
    def filter_state(self, queryset, name, value):
        """
        Filter CreditOffers where epr_account__state is any of the selected Indian states.
        """
        if value:
            query = Q()
            for state in value:
                query |= Q(epr_account__state__iexact=state)
            return queryset.filter(query)
        return queryset

    class Meta:
        model = CreditOffer
        fields = [
            'waste_type',
            'recycler_type',
            'state',
            'city',
            'credit_type',
            'product_type',
            'price_per_credit',
            'status',
            'price_per_credit_exact',
            'trail_documents',
            'is_approved',
            'FY',
            'credit_available',
            'minimum_purchase',
            'is_sold',
            'has_availability_proof',
        ]
        filter_overrides = {
            models.JSONField: {
                'filter_class': filters.MultipleChoiceFilter,
                'extra': lambda f: {
                    'choices': [(doc, doc) for doc in allowed_docs],
                    'method': 'filter_trail_documents',
                },
            },
        }