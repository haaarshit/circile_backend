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
    CheckProfileCompletionView,
    send_contact_email,
    SubscribeView,
    unsubscribe_view,
    PublicBlogListView,
    PublicBlogDetailView,
    LatestBlogsView,
    battery_contact_email,
    UpdateEmailView,
    UpdatePasswordView,
    FetchBankDetailsAPIView,
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

    # update password and email where user is logged in
    path('update-email/', UpdateEmailView.as_view(), name='update-email'),
    path('update-password/', UpdatePasswordView.as_view(), name='update-password'),

    path('update/', UpdateUserProfileView.as_view(), name='udpate_view'),
    path('profile/', GetProfileView.as_view(), name='profile_view'),

    # check profile completion status  
    path('check-profile-completion/', CheckProfileCompletionView.as_view(), name='check_profile_completion'),

    # Email Verification Routes
    path('send-verification-email/', send_verification_email, name='send-verification-email'),
    path('verify-email/<str:user_type>/<str:token>/', verify_email, name='verify-email'),
    path('counts/', UserCountStatsView.as_view(), name='user-epr-stats'),

    path('contact/', send_contact_email, name='send_contact_email'),
    path('contact/battery/', battery_contact_email, name='battery_contact_email'),

    #  news letter
    path('newsletter/subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('newsletter/unsubscribe/<str:token>/', battery_contact_email, name='unsubscribe'),

    # blogs
    path('blogs/', PublicBlogListView.as_view(), name='public-blog-list'),  
    path('blogs/latest/', LatestBlogsView.as_view(), name='latest-blog-list'),  
    # path('blogs/<int:pk>/', PublicBlogDetailView.as_view(), name='public-blog-detail'),
    path('blogs/<str:pk>/', PublicBlogDetailView.as_view(), name='public-blog-detail'),

    path('fetch-bank-details/', FetchBankDetailsAPIView.as_view(), name='fetch-bank-details'),

]