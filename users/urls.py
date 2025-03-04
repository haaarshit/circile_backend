from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterRecyclerView,
    RegisterProducerView,
    LoginView,
    send_verification_email,
    verify_email
)

urlpatterns = [
    # Registration Routes
    path('register/recycler/', RegisterRecyclerView.as_view(), name='register-recycler'),
    path('register/producer/', RegisterProducerView.as_view(), name='register-producer'),

    # Authentication Routes
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Email Verification Routes
    path('send-verification-email/', send_verification_email, name='send-verification-email'),
    path('verify-email/<str:user_type>/<str:token>/', verify_email, name='verify-email'),
]