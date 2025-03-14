from django.urls import path,include

from .views import (
    RecyclerEPRViewSet,
    ProducerEPRViewSet,
    EPRCreditViewSet,
    EPRTargetViewSet,
    CreditOfferViewSet,
    CounterCreditOfferViewSet,
    PublicCreditOfferListView,
    TransactionViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()  

# EPR related endpoints
router.register(r'recycler', RecyclerEPRViewSet, basename='recycler-epr')
router.register(r'credit', EPRCreditViewSet, basename='recycler-credit') # problem
router.register(r'producer', ProducerEPRViewSet, basename='producer-epr')
router.register(r'target', EPRTargetViewSet, basename='producer-target')

# Offer related endpoints
router.register(r'credit-offers', CreditOfferViewSet, basename='credit-offers')
router.register(r'counter-credit-offers', CounterCreditOfferViewSet, basename='counter-credit-offers')

# transactions
router.register(r'transactions', TransactionViewSet, basename='transaction')


urlpatterns = [
    path('', include(router.urls)),
      path('public-credit-offers/', PublicCreditOfferListView.as_view(), name='public-credit-offers'),
]

