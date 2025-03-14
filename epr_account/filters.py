# filters.py
from django_filters import rest_framework as filters
from django.db.models import Q
from django.db import models  # Import models explicitly for JSONField
from .models import CreditOffer  # Ensure CreditOffer is imported

allowed_docs = [
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
]

class CreditOfferFilter(filters.FilterSet):
    waste_type = filters.CharFilter(field_name='waste_type', lookup_expr='iexact')
    recycler_type = filters.CharFilter(field_name='epr_account__recycler_type', lookup_expr='iexact')
    state = filters.CharFilter(field_name='epr_account__state', lookup_expr='iexact')
    credit_type = filters.CharFilter(field_name='epr_credit__credit_type', lookup_expr='iexact')
    product_type = filters.CharFilter(field_name='epr_credit__product_type', lookup_expr='iexact')
    price_per_credit = filters.RangeFilter(field_name='price_per_credit')
    price_per_credit_exact = filters.NumberFilter(field_name='price_per_credit', lookup_expr='exact')
    
    # Filter for supporting_doc
    supporting_doc = filters.MultipleChoiceFilter(
        choices=[(doc, doc) for doc in allowed_docs],
        method='filter_supporting_doc',
        label='Supporting Documents'
    )

    # Optional additional filters
    is_approved = filters.BooleanFilter()
    FY = filters.RangeFilter()
    credit_available = filters.RangeFilter()
    minimum_purchase = filters.RangeFilter()
    is_sold = filters.BooleanFilter()

    def filter_supporting_doc(self, queryset, name, value):
        """
        Custom filter method to filter CreditOffers where supporting_doc contains any of the selected values.
        """
        if value:  # Only apply filter if values are provided
            query = Q()
            for doc in value:
                query |= Q(supporting_doc__contains=[doc])  # Check if doc is in the JSON list
            return queryset.filter(query)
        return queryset

    class Meta:
        model = CreditOffer
        fields = [
            'waste_type',
            'recycler_type',
            'state',
            'credit_type',
            'product_type',
            'price_per_credit',
            'price_per_credit_exact',
            'supporting_doc',
            'is_approved',
            'FY',
            'credit_available',
            'minimum_purchase',
            'is_sold',
        ]
        # Override JSONField handling to avoid AssertionError
        filter_overrides = {
            models.JSONField: {  # Use fully qualified models.JSONField
                'filter_class': filters.MultipleChoiceFilter,
                'extra': lambda f: {
                    'choices': [(doc, doc) for doc in allowed_docs],
                    'method': 'filter_supporting_doc',  # Link to custom method
                },
            },
        }