from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/',include('users.urls'),name='users'),
    path('api/epr/',include('epr_account.urls'),name='epr_account')
]
