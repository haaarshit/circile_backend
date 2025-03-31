from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SuperAdmin,TransactionFee
from .serializers import SuperAdminSerializer, SuperAdminLoginSerializer,TransactionFeeSerializer
from .authentication import SuperAdminJWTAuthentication
from .permissions import IsSuperAdmin
from .utils import ResponseWrapperMixin  # Import the mixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status,serializers
from rest_framework.exceptions import ValidationError
from .utils import ResponseWrapperMixin
from django.db.models import Max, Min, Avg



# EPR Account Models and Serializers (Assuming you have these in epr_account app)
from epr_account.models import (
    RecyclerEPR, ProducerEPR, EPRCredit, EPRTarget, CreditOffer, 
    CounterCreditOffer, Transaction,PurchasesRequest
)
from epr_account.serializers import (
    RecyclerEPRSerializer, ProducerEPRSerializer, EPRCreditSerializer, 
    EPRTargetSerializer, CreditOfferSerializer, CounterCreditOfferSerializer, 
    TransactionSerializer,PurchasesRequestSerializer
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
    filterset_fields = ['epr_registration_number', 'waste_type', 'recycler_type', 'city', 'state']

class RecyclerEPRDetailView(BaseSuperAdminModelDetailView):
    queryset = RecyclerEPR.objects.all()
    serializer_class = RecyclerEPRSerializer

# ProducerEPR Views
class ProducerEPRListCreateView(BaseSuperAdminModelView):
    queryset = ProducerEPR.objects.all()
    serializer_class = ProducerEPRSerializer
    filterset_fields = ['epr_registration_number', 'waste_type', 'producer_type', 'city', 'state']

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
    filterset_fields = ['epr_registration_number', 'waste_type', 'product_type', 'credit_type', 'FY','is_achieved']

class EPRTargetDetailView(BaseSuperAdminModelDetailView):
    queryset = EPRTarget.objects.all()
    serializer_class = EPRTargetSerializer

# CreditOffer Views
class CreditOfferListCreateView(BaseSuperAdminModelView):
    queryset = CreditOffer.objects.all()
    serializer_class = CreditOfferSerializer
    filterset_fields = ['epr_registration_number', 'waste_type', 'FY', 'is_approved', 'is_sold','epr_credit']

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
    filterset_fields = ['order_id', 'waste_type', 'credit_type', 'status', 'is_complete']

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            transaction = serializer.save()

            # TODO SEND MAIL TO RECYCLER IF TRANSACTION GET APPROVED
            # Move EPRTarget/CreditOffer logic here for Superadmin approval
            if transaction.status == 'approved' and isinstance(request.user, SuperAdmin):
                epr_target = EPRTarget.objects.filter(
                    epr_account=transaction.producer_epr,
                    waste_type=transaction.waste_type,
                    product_type=transaction.product_type,
                    credit_type=transaction.credit_type,
                    is_achieved=False
                ).first()

                if epr_target:
                    epr_target.achieved_quantity += int(transaction.credit_quantity)
                    if epr_target.achieved_quantity == epr_target.target_quantity:
                        epr_target.is_achieved = True
                    epr_target.save()
                
                if transaction.counter_credit_offer:
                    transaction.credit_offer.credit_available -= transaction.credit_quantity 
                    if transaction.credit_offer.credit_available == 0:
                        transaction.credit_offer.is_sold = True
                    transaction.credit_offer.save()
                else:
                    transaction.credit_offer.credit_available -= transaction.credit_quantity 
                    if transaction.credit_offer.credit_available == 0:
                        transaction.credit_offer.is_sold = True
                    transaction.credit_offer.save()
            
            return Response( serializer.data, status=status.HTTP_200_OK)
        
        except serializers.ValidationError as e:
            if isinstance(e.detail, dict):
            # Flatten the nested dictionary error messages
                error_messages = []
                for key, value in e.detail.items():
                    if isinstance(value, list):  # Typical DRF ValidationError structure
                        error_messages.extend(value)
                    else:
                        error_messages.append(str(value))
                
                error_message = error_messages[0] if error_messages else "An unknown error occurred."
            else:
                error_message = str(e)
    
            return Response({
         
                 error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

# PurchasesRequest Views
class PurchasesRequestListCreateView(BaseSuperAdminModelView):
    queryset = PurchasesRequest.objects.all()
    serializer_class = PurchasesRequestSerializer
    filterset_fields = ['status']  # Adjust fields as per your model

class PurchasesRequestDetailView(BaseSuperAdminModelDetailView):
    queryset = PurchasesRequest.objects.all()
    serializer_class = PurchasesRequestSerializer


class SuperAdminCountStatsView(APIView):
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        try:
            # Ensure the user is a SuperAdmin
            user = request.user
            if not isinstance(user, SuperAdmin):
                return Response(
                    {"error": "User is not a SuperAdmin", "status": False},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Aggregate counts from all relevant tables
            stats = {
                "total_superadmins": SuperAdmin.objects.count(),
                "total_recyclers": Recycler.objects.count(),
                "total_producers": Producer.objects.count(),
                "total_recycler_epr_accounts": RecyclerEPR.objects.count(),
                "total_producer_epr_accounts": ProducerEPR.objects.count(),
                "total_epr_credits": EPRCredit.objects.count(),
                "total_epr_targets": EPRTarget.objects.count(),
                "total_achieved_targets": EPRTarget.objects.filter(is_achieved=True).count(),
                "total_credit_offers": CreditOffer.objects.count(),
                "total_counter_credit_offers": CounterCreditOffer.objects.count(),
                "total_transactions": Transaction.objects.count(),
                "total_completed_transactions": Transaction.objects.filter(is_complete=True).count(),
                "total_pending_transactions": Transaction.objects.filter(is_complete=False).count(),
                "total_direct_purchases": PurchasesRequest.objects.count()
            }

            return Response(
                {
                    "status": True,
                    "message": "SuperAdmin statistics retrieved successfully",
                    "data": stats
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e), "status": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# TRANSACTION FEE 
class TransactionFeeListCreateView(ResponseWrapperMixin, generics.ListCreateAPIView):
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]
    queryset = TransactionFee.objects.all()
    serializer_class = TransactionFeeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_fee', 'description']

class TransactionFeeDetailView(ResponseWrapperMixin, generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]
    queryset = TransactionFee.objects.all()
    serializer_class = TransactionFeeSerializer


class CreditOfferPriceStatsView(APIView):
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        try:
            # Check if there are any records
            if not CreditOffer.objects.exists():
                return Response(
                    {
                        "status": False,
                        "message": "No CreditOffer records found",
                        "data": {}
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get max and min price_per_credit
            price_stats = CreditOffer.objects.aggregate(
                max_price=Max('price_per_credit'),
                min_price=Min('price_per_credit')
            )

            # Calculate average as (max_price + min_price) / 2
            max_price = price_stats['max_price']
            min_price = price_stats['min_price']
            average_price = (max_price + min_price) / 2 if max_price is not None and min_price is not None else 0.0

            # Fetch records with max and min price_per_credit
            max_price_record = CreditOffer.objects.filter(price_per_credit=max_price).first()
            min_price_record = CreditOffer.objects.filter(price_per_credit=min_price).first()

            # Serialize the records
            max_serializer = CreditOfferSerializer(max_price_record)
            min_serializer = CreditOfferSerializer(min_price_record)

            # Prepare response data
            response_data = {
                "maximum_price": float(max_price) if max_price is not None else None,
                "minimum_price": float(min_price) if min_price is not None else None,
                "average_price": float(average_price),
                "maximum_price_record": max_serializer.data,
                "minimum_price_record": min_serializer.data
            }

            return Response(
                {
                    "status": True,
                    "message": "Credit offer price statistics retrieved successfully",
                    "data": response_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )