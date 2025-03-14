# filters.py
from django_filters import rest_framework as filters
from .models import CreditOffer

class CreditOfferFilter(filters.FilterSet):
    waste_type = filters.CharFilter(
        field_name='waste_type',
        lookup_expr='iexact'
    )
    recycler_type = filters.CharFilter(
        field_name='epr_account__recycler_type',
        lookup_expr='iexact'
    )
    state = filters.CharFilter(
        field_name='epr_account__state',
        lookup_expr='iexact'
    )
    credit_type = filters.CharFilter(
        field_name='epr_credit__credit_type',
        lookup_expr='iexact'
    )
    product_type = filters.CharFilter(
        field_name='epr_credit__product_type',
        lookup_expr='iexact'
    )
    price_per_credit = filters.RangeFilter(
        field_name='price_per_credit'  # Range filter for price_per_credit
    )
    price_per_credit_exact = filters.NumberFilter(
        field_name='price_per_credit',  # Exact match for price_per_credit
        lookup_expr='exact'
    )

    # Optional additional filters
    is_approved = filters.BooleanFilter()
    FY = filters.RangeFilter()
    credit_available = filters.RangeFilter()
    minimum_purchase = filters.RangeFilter()
    is_sold = filters.BooleanFilter()

    
    class Meta:
        model = CreditOffer
        fields = [
            'waste_type',
            'recycler_type',
            'state',
            'credit_type',
            'product_type',
            'price_per_credit',       # Range filter
            'price_per_credit_exact', # Exact filter
            'is_approved',
            'FY',
            'credit_available',
            'minimum_purchase',
            'is_sold',
        ]