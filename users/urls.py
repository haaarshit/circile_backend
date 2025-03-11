from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterRecyclerView,
    RegisterProducerView,
    LoginView,
    send_verification_email,
    verify_email,
    GetProfileView,
    UpdateUserProfileView
)

urlpatterns = [
    # Registration Routes
    path('register/recycler/', RegisterRecyclerView.as_view(), name='register-recycler'),
    path('register/producer/', RegisterProducerView.as_view(), name='register-producer'),

    # Authentication Routes
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('update/', UpdateUserProfileView.as_view(), name='udpate_view'),
    path('profile/', GetProfileView.as_view(), name='profile_view'),

    # Email Verification Routes
    path('send-verification-email/', send_verification_email, name='send-verification-email'),
    path('verify-email/<str:user_type>/<str:token>/', verify_email, name='verify-email'),
]