# superadmin/filters.py
from django_filters import rest_framework as filters
from superadmin.models import Blog
from django.db.models import Q
import datetime


class BlogFilter(filters.FilterSet):
    created_at = filters.CharFilter(method='filter_created_at')
    created_at__gte = filters.CharFilter(method='filter_created_at_gte')
    created_at__lte = filters.CharFilter(method='filter_created_at_lte')

    class Meta:
        model = Blog
        fields = {
            'title': ['exact', 'icontains'],
            'sub_title': ['exact', 'icontains'],
            'slug': ['exact'],
            'content': ['exact', 'icontains'],
            'updated_at': ['exact', 'gte', 'lte'],
        }

    def filter_created_at(self, queryset, name, value):
        try:
            if len(value) == 4:  # YYYY
                year = int(value)
                return queryset.filter(created_at__year=year)
            elif len(value) == 10:  # YYYY-MM-DD
                date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                return queryset.filter(created_at__date=date)
            else:
                return queryset.none()
        except (ValueError, TypeError):
            return queryset.none()

    def filter_created_at_gte(self, queryset, name, value):
        try:
            if len(value) == 4:  # YYYY
                year = int(value)
                return queryset.filter(created_at__year__gte=year)
            elif len(value) == 10:  # YYYY-MM-DD
                date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                return queryset.filter(created_at__date__gte=date)
            else:
                return queryset.none()
        except (ValueError, TypeError):
            return queryset.none()

    def filter_created_at_lte(self, queryset, name, value):
        try:
            if len(value) == 4:  # YYYY
                year = int(value)
                return queryset.filter(created_at__year__lte=year)
            elif len(value) == 10:  # YYYY-MM-DD
                date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                return queryset.filter(created_at__date__lte=date)
            else:
                return queryset.none()
        except (ValueError, TypeError):
            return queryset.none()