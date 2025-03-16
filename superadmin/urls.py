from django.urls import path
from .views import (
    SuperAdminLoginView, SuperAdminListCreateView, SuperAdminRetrieveUpdateDestroyView,
    RecyclerEPRListCreateView, RecyclerEPRDetailView,
    ProducerEPRListCreateView, ProducerEPRDetailView,
    EPRCreditListCreateView, EPRCreditDetailView,
    EPRTargetListCreateView, EPRTargetDetailView,
    CreditOfferListCreateView, CreditOfferDetailView,
    CounterCreditOfferListCreateView, CounterCreditOfferDetailView,
    TransactionListCreateView, TransactionDetailView,
    RecyclerListCreateView, RecyclerDetailView,
    ProducerListCreateView, ProducerDetailView,
)

urlpatterns = [
    # SuperAdmin Auth
    path('login/', SuperAdminLoginView.as_view(), name='superadmin-login'),
    path('superadmins/', SuperAdminListCreateView.as_view(), name='superadmin-list-create'),
    path('superadmins/<uuid:pk>/', SuperAdminRetrieveUpdateDestroyView.as_view(), name='superadmin-detail'),

    # RecyclerEPR
    path('recycler-epr/', RecyclerEPRListCreateView.as_view(), name='recycler-epr-list-create'),
    path('recycler-epr/<uuid:pk>/', RecyclerEPRDetailView.as_view(), name='recycler-epr-detail'),

    # ProducerEPR
    path('producer-epr/', ProducerEPRListCreateView.as_view(), name='producer-epr-list-create'),
    path('producer-epr/<uuid:pk>/', ProducerEPRDetailView.as_view(), name='producer-epr-detail'),

    # EPRCredit
    path('epr-credits/', EPRCreditListCreateView.as_view(), name='epr-credit-list-create'),
    path('epr-credits/<uuid:pk>/', EPRCreditDetailView.as_view(), name='epr-credit-detail'),

    # EPRTarget
    path('epr-targets/', EPRTargetListCreateView.as_view(), name='epr-target-list-create'),
    path('epr-targets/<uuid:pk>/', EPRTargetDetailView.as_view(), name='epr-target-detail'),

    # CreditOffer
    path('credit-offers/', CreditOfferListCreateView.as_view(), name='credit-offer-list-create'),
    path('credit-offers/<uuid:pk>/', CreditOfferDetailView.as_view(), name='credit-offer-detail'),

    # CounterCreditOffer
    path('counter-credit-offers/', CounterCreditOfferListCreateView.as_view(), name='counter-credit-offer-list-create'),
    path('counter-credit-offers/<uuid:pk>/', CounterCreditOfferDetailView.as_view(), name='counter-credit-offer-detail'),

    # Transaction
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<uuid:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),

    # Recycler
    path('recyclers/', RecyclerListCreateView.as_view(), name='recycler-list-create'),
    path('recyclers/<uuid:pk>/', RecyclerDetailView.as_view(), name='recycler-detail'),

    # Producer
    path('producers/', ProducerListCreateView.as_view(), name='producer-list-create'),
    path('producers/<uuid:pk>/', ProducerDetailView.as_view(), name='producer-detail'),
]