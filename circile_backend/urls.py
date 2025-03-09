"""
URL configuration for circile_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/',include('users.urls'),name='users'),
    path('api/epr/',include('epr_account.urls'),name='epr_account')
]

"""
# REGISTER FOR RECYCLER 
http://localhost:3000/api/users/register/recycler/
# REGISTER FOR RECYCLER
http://localhost:3000/api/users/register/producer/
# LOGIN FOR BOTH
http://localhost:3000/api/users/register/login/
# UPDATE FOR BOTH
http://localhost:3000/api/users/register/update/

# EPR_ACCOUNT [ROUTE FOR ALL => POST,PUT,DELETE,PATCH,GET]
# FOR RECYCLER
http://localhost:3000/api/epr/recycler/
# FOR PRODUCER
http://localhost:3000/api/epr/producer/
# EPR CREDIT -> ONLY FOR RECYLER
http://localhost:3000/api/epr/recycler/credit/
"""