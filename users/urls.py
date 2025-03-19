from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
from .refresh_token import CustomRefreshTokenAuthentication
from .views import (
    RegisterRecyclerView,
    RegisterProducerView,
    LoginView,
    send_verification_email,
    verify_email,
    GetProfileView,
    UpdateUserProfileView,
    ForgotPasswordView,
    ResetPasswordView,
    UserCountStatsView,
    CheckProfileCompletionView
)

urlpatterns = [
    # Registration Routes
    path('register/recycler/', RegisterRecyclerView.as_view(), name='register-recycler'),
    path('register/producer/', RegisterProducerView.as_view(), name='register-producer'),
    # Authentication Routes
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    # /api/users/token/refresh
    path('token/refresh/',  CustomRefreshTokenAuthentication.as_view(), name='token_refresh'),
    # password reset
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:user_type>/<str:token>/', ResetPasswordView.as_view(), name='reset-password'),

    path('update/', UpdateUserProfileView.as_view(), name='udpate_view'),
    path('profile/', GetProfileView.as_view(), name='profile_view'),

    # check profile completion status  
    path('check-profile-completion/', CheckProfileCompletionView.as_view(), name='check_profile_completion'),

    # Email Verification Routes
    path('send-verification-email/', send_verification_email, name='send-verification-email'),
    path('verify-email/<str:user_type>/<str:token>/', verify_email, name='verify-email'),
    path('counts/', UserCountStatsView.as_view(), name='user-epr-stats'),

]