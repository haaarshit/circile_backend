from django.urls import path,include
from rest_framework import routers

from .views import (
    RecyclerEPRViewSet,
    ProducerEPRViewSet,
    EPRCreditViewSet,
    EPRTargetViewSet
)

router = routers.SimpleRouter()

router.register(r'recycler/credit',EPRCreditViewSet,basename='recycler/credit')
router.register(r'producer/target',EPRTargetViewSet,basename='producer/credit')
router.register(r'recycler',RecyclerEPRViewSet,basename='recycler')
router.register(r'producer',ProducerEPRViewSet,basename='producer')

urlpatterns = [
    path('',include(router.urls))
]