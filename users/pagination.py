from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CustomPagination(PageNumberPagination):
    page_size = 9  # Adjust as needed
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_next_page_number(self):
        if not self.page.has_next():
            return None
        return self.page.next_page_number()

    def get_previous_page_number(self):
        if not self.page.has_previous():
            return None
        return self.page.previous_page_number()
    
    def get_last_page_number(self):
        if self.page.paginator.count == 0:
            return None
        return math.ceil(self.page.paginator.count / self.page.paginator.per_page)


    def get_paginated_response(self, data):
        return Response({
            'status': True,
            'message': 'Blogs retrieved successfully',
            "pagination":{            
            'total': self.page.paginator.count,
            'next': self.get_next_page_number(),
            'previous': self.get_previous_page_number(),
            'last': self.get_last_page_number(),
            },
            'data': data
        })
