from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SuperAdmin,TransactionFee,Blog
from .authentication import SuperAdminJWTAuthentication
from .permissions import IsSuperAdmin
from .utils import ResponseWrapperMixin  # Import the mixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status,serializers
from rest_framework.exceptions import ValidationError
from .utils import ResponseWrapperMixin
from django.db.models import Max, Min, Avg

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.shortcuts import get_object_or_404

import os
import json
from django.http import Http404


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
from users.models import Recycler, Producer,Newsletter
from users.serializers import RecyclerSerializer, ProducerSerializer,ProducerDetailSerializer,RecyclerDetailSerializer

from .serializers import SuperAdminSerializer, SuperAdminLoginSerializer,TransactionFeeSerializer,NewsletterSerializer,BlogSerializer



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

            if transaction.status == 'approved' and isinstance(request.user, SuperAdmin):
                credit_offer = transaction.credit_offer

                if credit_offer.credit_available < transaction.credit_quantity:
                            raise ValidationError(f"Not enough credit is available in credit offer for this transaction. Available credit {credit_offer.credit_available}. Required credit {transaction.credit_quantity} ")
                epr_target = EPRTarget.objects.filter(
                    epr_account=transaction.producer_epr,
                    waste_type=transaction.waste_type,
                    product_type=transaction.product_type,
                    credit_type=transaction.credit_type,
                    is_achieved=False
                ).annotate(
                remaining_quantity=F('target_quantity') - F('achieved_quantity')
                ).filter(
                    remaining_quantity__gte=transaction.credit_quantity
                ).first()

                if not epr_target:
                    raise ValidationError(
                         f"No matching EPR Target found. Please create an EPR target for the given EPR account where credit type should be {transaction.credit_type}, product type should be {transaction.product_type} and waste type {transaction.waste_type} and remaining Target quantity is higher than {transaction.credit_quantity}"
                    )


                if epr_target:
                    epr_target.achieved_quantity += int(transaction.credit_quantity)
                    if epr_target.achieved_quantity == epr_target.target_quantity:
                        epr_target.is_achieved = True
                    epr_target.save()
                
                # if transaction.counter_credit_offer:
                #     transaction.credit_offer.credit_available -= transaction.credit_quantity 
                #     if transaction.credit_offer.credit_available == 0:
                #         transaction.credit_offer.is_sold = True
                #     transaction.credit_offer.save()
                # else:
                # transaction.credit_offer.credit_available -= transaction.credit_quantity 
                # if transaction.credit_offer.credit_available == 0:
                #     transaction.credit_offer.is_sold = True
                # if transaction.credit_offer.credit_available < transaction.credit_offer.minimum_purchase:
                #     transaction.credit_offer.credit_available = transaction.credit_offer.minimum_purchase
                # transaction.credit_offer.save()
      
                credit_offer.credit_available = credit_offer.credit_available - transaction.credit_quantity
                if credit_offer.credit_available < credit_offer.minimum_purchase:
                    credit_offer.minimum_purchase = credit_offer.credit_available
                credit_offer.is_sold = credit_offer.credit_available == 0
                credit_offer.save()

                  # Email to Recycler
                recycler = transaction.recycler
                producer = transaction.producer
                
                # Common fields
                email = 'support@circle8.in'
                contact_number = '+91 9620220013'

                # Email to Recycler (Stylish HTML)
                recycler_subject = "Transaction Approved by SuperAdmin"
                recycler_html_message = (
                 
                    f"<!DOCTYPE html>"
                    f"<html>"
                    f"<head>"
                    f"    <meta charset='UTF-8'>"
                    f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                    f"    <title>Transaction Approval Notification</title>"
                    f"    <style>"
                    f"        body {{"
                    f"            font-family: Arial, sans-serif;"
                    f"            margin: 0;"
                    f"            padding: 20px;"
                    f"            background-color: #f4f4f4;"
                    f"        }}"
                    f"        .container {{"
                    f"            max-width: 600px;"
                    f"            background: #ffffff;"
                    f"            padding: 20px;"
                    f"            border-radius: 8px;"
                    f"            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);"
                    f"        }}"
                    f"        h2 {{"
                    f"            color: #2c3e50;"
                    f"            text-align: center;"
                    f"        }}"
                    f"        .details {{"
                    f"            margin: 20px 0;"
                    f"        }}"
                    f"        .details table {{"
                    f"            width: 100%;"
                    f"            border-collapse: collapse;"
                    f"        }}"
                    f"        .details th, .details td {{"
                    f"            border: 1px solid #ddd;"
                    f"            padding: 8px;"
                    f"            text-align: left;"
                    f"        }}"
                    f"        .details th {{"
                    f"            background-color: #3498db;"
                    f"            color: white;"
                    f"        }}"
                    f"        .status {{"
                    f"            text-align: center;"
                    f"            padding: 10px;"
                    f"            font-weight: bold;"
                    f"            background-color: #27ae60;"
                    f"            color: white;"
                    f"            border-radius: 4px;"
                    f"        }}"
                    f"        .cta {{"
                    f"            text-align: center;"
                    f"            margin-top: 20px;"
                    f"        }}"
                    f"        .cta a {{"
                    f"            text-decoration: none;"
                    f"            background: #27ae60;"
                    f"            color: white;"
                    f"            padding: 10px 20px;"
                    f"            border-radius: 5px;"
                    f"            display: inline-block;"
                    f"        }}"
                    f"    </style>"
                    f"</head>"
                    f"<body>"
                    f"    <div class='container'>"
                    f"        <h2>📢 Transaction Approval Notification</h2>"
                    f"        <p>Dear <strong>{recycler.full_name}</strong>,</p>"
                    f"        <p>A transaction involving your credit offer has been approved by the SuperAdmin. Below are the details:</p>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <h3>🛠 Transaction Details</h3>"
                    f"            <table>"
                    f"                <tr><th>Request By</th><td>{producer.unique_id}</td></tr>"
                    f"                <tr><th>Work Order ID</th><td>{transaction.order_id}</td></tr>"
                    f"                <tr><th>Work Order Date</th><td>{transaction.work_order_date}</td></tr>"
                    f"                <tr><th>Waste Type</th><td>{transaction.waste_type}</td></tr>"
                    f"                <tr><th>Credit Type</th><td>{transaction.credit_type}</td></tr>"
                    f"                <tr><th>Price per Credit</th><td>{transaction.price_per_credit}</td></tr>"
                    f"                <tr><th>Product Type</th><td>{transaction.product_type}</td></tr>"
                    f"                <tr><th>Producer Type</th><td>{transaction.producer_type}</td></tr>"
                    f"                <tr><th>Credit Quantity</th><td>{transaction.credit_quantity}</td></tr>"
                    f"                <tr><th>Total Price</th><td>{transaction.total_price}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <h3>👤 Producer Details</h3>"
                    f"            <table>"
                    f"                <tr><th>EPR Registration Number</th><td>{transaction.producer_epr.epr_registration_number}</td></tr>"
                    f"                <tr><th>EPR Registered Name</th><td>{transaction.producer_epr.epr_registered_name}</td></tr>"
                    f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                    f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <h3>📁 Trail Documents</h3>"
                    f"            <ul>"
                    f"                  {''.join([f'<li>✅ {doc}</li>' for doc in transaction.credit_offer.trail_documents if doc.strip()])}"
                    f"            </ul>"
                    f"        </div>"
                    f"        "
                    f"        <div class='status'>Status: {transaction.status}</div>"
                    # f"        "
                    # f"        <div class='cta'>"
                    # f"            <a href='#'>Upload Documents</a>"
                    # f"        </div>"
                    # f"        "
                    # f"        <p style='color: #34495e; text-align: center; margin-top: 20px;'>"
                    # f"            Please upload the necessary documents (trail_documents, recycler_transfer_proof) to complete the transaction."
                    # f"        </p>"
                    # f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                    # f"            This is an automated message. Please do not reply directly to this email."
                    # f"        </p>"
                    f"    </div>"
                    f"</body>"
                    f"</html>"
                )
                send_mail(
                    subject=recycler_subject,
                    message="",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recycler.email],
                    fail_silently=False,
                    html_message=recycler_html_message
                )
            
            return Response( serializer.data, status=status.HTTP_200_OK)
        
        except serializers.ValidationError as e:

            if isinstance(e.detail, dict):
            # Flatten dictionary errors
                error_messages = []
                for key, value in e.detail.items():
                        if isinstance(value, list):
                            # Extract string from each ErrorDetail object
                            error_messages.extend(str(err) for err in value)
                        else:
                            error_messages.append(str(value))
                error_message = error_messages[0] if error_messages else "An unknown error occurred."
            elif isinstance(e.detail, list):
                    # Handle list of ErrorDetail objects
                    error_message = str(e.detail[0]) if e.detail else "An unknown error occurred."
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
        

class ContactMessagesView(ResponseWrapperMixin, APIView):
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        try:
            # Define JSON file path
            json_dir = getattr(settings, 'CONTACT_JSON_DIR', os.path.join(settings.BASE_DIR, 'contact_messages'))
            json_file = os.path.join(json_dir, 'contact_messages.json')

            # Check if file exists
            if not os.path.exists(json_file):
                return Response(
                    {
                        "status": False,
                        "message": "No contact messages found",
                        "data": []
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)

            # Validate that messages is a list
            if not isinstance(messages, list):
                return Response(
                    {
                        "status": False,
                        "message": "Invalid data format in JSON file",
                        "data": []
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Return messages
            return Response(messages)

        except json.JSONDecodeError:
            return Response(
                {
                    "status": False,
                    "message": "Error decoding JSON file",
                    "data": []
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "error": str(e),
                    "data": []
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# NEWSLETTER

class CreateNewsletterView(ResponseWrapperMixin, generics.CreateAPIView):
    """
    View for creating a newsletter (SuperAdmin only)
    """
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            newsletter = serializer.save()

            return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED

            )
        except Exception as e:
            return Response(
                {"error": str(e), "status": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SendNewsletterView(ResponseWrapperMixin, APIView):
    """
    View for sending a newsletter to all subscribers (SuperAdmin only)
    """
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def post(self, request, newsletter_id):
        try:
            newsletter = get_object_or_404(Newsletter, id=newsletter_id)
            if newsletter.is_sent:
                return Response(
                    "This newsletter has already been sent",
                    status=status.HTTP_400_BAD_REQUEST
                )

            if newsletter.send_newsletter():
                return Response(
                    "Newsletter sent successfully",
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Failed to send newsletter", "status": False},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"error": str(e), "status": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListNewslettersView(ResponseWrapperMixin, generics.ListAPIView):
    """
    View for listing all newsletters (SuperAdmin only)
    """
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                    serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e), "status": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# BLOGS

class BlogListCreateView(ResponseWrapperMixin, generics.ListCreateAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title', 'created_at']

    def perform_create(self, serializer):
        if not isinstance(self.request.user, SuperAdmin):
            raise ValidationError("Only SuperAdmins can create blogs.")
        serializer.save(created_by=self.request.user)

class BlogDetailView(ResponseWrapperMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    authentication_classes = [SuperAdminJWTAuthentication]
    permission_classes = [IsSuperAdmin]
    lookup_field = 'pk'  # Placeholder for ID or slug

    def get_object(self):
        lookup_value = self.kwargs.get('pk', '')
        if not lookup_value:
            raise Http404("Blog identifier not provided")

        if lookup_value.isdigit():
            try:
                return Blog.objects.get(id=int(lookup_value))
            except Blog.DoesNotExist:
                pass  
        try:
            return Blog.objects.get(slug=lookup_value)
        except Blog.DoesNotExist:
            raise Http404("Blog not found")

    def perform_update(self, serializer):
        if not isinstance(self.request.user, SuperAdmin):
            raise ValidationError("Only SuperAdmins can update blogs.")
        serializer.save()

    def perform_destroy(self, instance):
        if not isinstance(self.request.user, SuperAdmin):
            raise ValidationError("Only SuperAdmins can delete blogs.")
        instance.delete()