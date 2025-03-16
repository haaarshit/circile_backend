from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SuperAdmin
from .serializers import SuperAdminSerializer, SuperAdminLoginSerializer
from .authentication import SuperAdminJWTAuthentication
from .permissions import IsSuperAdmin
from .utils import ResponseWrapperMixin  # Import the mixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from .utils import ResponseWrapperMixin


# EPR Account Models and Serializers (Assuming you have these in epr_account app)
from epr_account.models import (
    RecyclerEPR, ProducerEPR, EPRCredit, EPRTarget, CreditOffer, 
    CounterCreditOffer, Transaction
)
from epr_account.serializers import (
    RecyclerEPRSerializer, ProducerEPRSerializer, EPRCreditSerializer, 
    EPRTargetSerializer, CreditOfferSerializer, CounterCreditOfferSerializer, 
    TransactionSerializer
)

# User Models and Serializers (Assuming you have these in users app)
from users.models import Recycler, Producer
from users.serializers import RecyclerSerializer, ProducerSerializer,ProducerDetailSerializer,RecyclerDetailSerializer

# SuperAdmin Login View
class SuperAdminLoginView(APIView):
    def post(self, request):
        # serializer = SuperAdminLoginSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # superadmin = serializer.validated_data['superadmin']
        # refresh = RefreshToken.for_user(superadmin)
        # return Response({
        #     'refresh': str(refresh),
        #     'access': str(refresh.access_token),
        # })
        try:
            serializer = SuperAdminLoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            superadmin = serializer.validated_data['superadmin']
            refresh = RefreshToken.for_user(superadmin)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'status':True
            }
            return Response(data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"status": False, "error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# SuperAdmin CRUD View
class SuperAdminListCreateView(ResponseWrapperMixin,generics.ListCreateAPIView):
    queryset = SuperAdmin.objects.all()
    serializer_class = SuperAdminSerializer

class SuperAdminRetrieveUpdateDestroyView(ResponseWrapperMixin,generics.RetrieveUpdateDestroyAPIView):
    queryset = SuperAdmin.objects.all()
    serializer_class = SuperAdminSerializer
    permission_classes = [IsSuperAdmin]  # Use custom permission


    authentication_classes = [SuperAdminJWTAuthentication]

# Generic View for all models with filtering
class BaseSuperAdminModelView(ResponseWrapperMixin,generics.ListCreateAPIView):
    authentication_classes = [SuperAdminJWTAuthentication]
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsSuperAdmin]
    

class BaseSuperAdminModelDetailView(ResponseWrapperMixin,generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    authentication_classes = [SuperAdminJWTAuthentication]

# RecyclerEPR Views
class RecyclerEPRListCreateView(BaseSuperAdminModelView):
    queryset = RecyclerEPR.objects.all()
    serializer_class = RecyclerEPRSerializer
    filterset_fields = ['epr_registration_number', 'waste_type', 'recycler_type', 'company_name', 'city', 'state']

class RecyclerEPRDetailView(BaseSuperAdminModelDetailView):
    queryset = RecyclerEPR.objects.all()
    serializer_class = RecyclerEPRSerializer

# ProducerEPR Views
class ProducerEPRListCreateView(BaseSuperAdminModelView):
    queryset = ProducerEPR.objects.all()
    serializer_class = ProducerEPRSerializer
    filterset_fields = ['epr_registration_number', 'waste_type', 'producer_type', 'company_name', 'city', 'state']

class ProducerEPRDetailView(BaseSuperAdminModelDetailView):
    queryset = ProducerEPR.objects.all()
    serializer_class = ProducerEPRSerializer

# EPRCredit Views
class EPRCreditListCreateView(BaseSuperAdminModelView):
    queryset = EPRCredit.objects.all()
    serializer_class = EPRCreditSerializer
    filterset_fields = ['epr_registration_number', 'waste_type', 'product_type', 'credit_type', 'year']

class EPRCreditDetailView(BaseSuperAdminModelDetailView):
    queryset = EPRCredit.objects.all()
    serializer_class = EPRCreditSerializer

# EPRTarget Views
class EPRTargetListCreateView(BaseSuperAdminModelView):
    queryset = EPRTarget.objects.all()
    serializer_class = EPRTargetSerializer
    filterset_fields = ['epr_registration_number', 'waste_type', 'product_type', 'credit_type', 'FY']

class EPRTargetDetailView(BaseSuperAdminModelDetailView):
    queryset = EPRTarget.objects.all()
    serializer_class = EPRTargetSerializer

# CreditOffer Views
class CreditOfferListCreateView(BaseSuperAdminModelView):
    queryset = CreditOffer.objects.all()
    serializer_class = CreditOfferSerializer
    filterset_fields = ['epr_registration_number', 'waste_type', 'FY', 'is_approved', 'is_sold']

class CreditOfferDetailView(BaseSuperAdminModelDetailView):
    queryset = CreditOffer.objects.all()
    serializer_class = CreditOfferSerializer

# CounterCreditOffer Views
class CounterCreditOfferListCreateView(BaseSuperAdminModelView):
    queryset = CounterCreditOffer.objects.all()
    serializer_class = CounterCreditOfferSerializer
    filterset_fields = ['status', 'is_approved']

class CounterCreditOfferDetailView(BaseSuperAdminModelDetailView):
    queryset = CounterCreditOffer.objects.all()
    serializer_class = CounterCreditOfferSerializer

# Transaction Views
class TransactionListCreateView(BaseSuperAdminModelView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filterset_fields = ['order_id', 'waste_type', 'credit_type', 'status', 'is_complete']

class TransactionDetailView(BaseSuperAdminModelDetailView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

# Recycler Views
class RecyclerListCreateView(BaseSuperAdminModelView):
    queryset = Recycler.objects.all()
    serializer_class = RecyclerDetailSerializer
    filterset_fields = ['email', 'unique_id', 'company_name', 'city', 'state', 'is_active', 'is_verified']

class RecyclerDetailView(BaseSuperAdminModelDetailView):
    queryset = Recycler.objects.all()
    serializer_class = RecyclerDetailSerializer

# Producer Views
class ProducerListCreateView(BaseSuperAdminModelView):
    queryset = Producer.objects.all()
    serializer_class = ProducerDetailSerializer
    filterset_fields = ['email', 'unique_id', 'company_name', 'city', 'state', 'is_active', 'is_verified']

class ProducerDetailView(BaseSuperAdminModelDetailView):
    queryset = Producer.objects.all()
    serializer_class = ProducerDetailSerializer