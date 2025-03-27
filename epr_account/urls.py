from django.urls import path,include

from .views import (
    RecyclerEPRViewSet,
    ProducerEPRViewSet,
    EPRCreditViewSet,
    EPRTargetViewSet,
    CreditOfferViewSet,
    CounterCreditOfferViewSet,
    PublicCreditOfferListView,PublicCreditOfferDetailView,
    TransactionViewSet,WasteTypeDetailView, WasteTypeListView,WasteTypeNamesView,PurchasesRequestViewSet
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

router.register(r'purchases-requests', PurchasesRequestViewSet, basename='purchases-request')
urlpatterns = [
    path('', include(router.urls)),
    path('public-credit-offers/', PublicCreditOfferListView.as_view(), name='public-credit-offers'),
    path('public-credit-offers/<uuid:pk>/', PublicCreditOfferDetailView.as_view(), name='credit-offer-detail'),
    path('waste-types/<str:waste_type_name>/', WasteTypeDetailView.as_view(), name='waste-type-detail'),
    path('waste-types/', WasteTypeListView.as_view(), name='waste-type-list'),
    path('waste-type-names/', WasteTypeNamesView.as_view(), name='waste-type-names'),  # New route

]

