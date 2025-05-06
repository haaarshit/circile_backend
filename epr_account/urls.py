from django.urls import path,include

from .views import (
    RecyclerEPRViewSet,
    ProducerEPRViewSet,
    EPRCreditViewSet,
    EPRTargetViewSet,
    CreditOfferViewSet,
    CounterCreditOfferViewSet,
    PublicCreditOfferListView,PublicCreditOfferDetailView,
    TransactionViewSet,WasteTypeDetailView, WasteTypeListView,WasteTypeNamesView,PurchasesRequestViewSet, OrderDetailView,ProducerTypeListView,
    RecyclerTypeListView,ProductTypeListView,CreditTypeListView, AllTypesView,AllowedDocsView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()  

# EPR related endpoints
router.register(r'recycler', RecyclerEPRViewSet, basename='recycler-epr')
router.register(r'credit', EPRCreditViewSet, basename='recycler-credit') 
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
    path('order/<uuid:record_id>/', OrderDetailView.as_view(), name='order_detail'),
    # New URLs for Specific Tables
    path('producer-types/', ProducerTypeListView.as_view(), name='producer-type-list'),
    path('recycler-types/', RecyclerTypeListView.as_view(), name='recycler-type-list'),
    path('product-types/', ProductTypeListView.as_view(), name='product-type-list'),
    path('credit-types/', CreditTypeListView.as_view(), name='credit-type-list'),
    path('all-types/', AllTypesView.as_view(), name='all-types'),
    path('allowed-docs/', AllowedDocsView.as_view(), name='allowed_docs'),
]

