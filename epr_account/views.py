from rest_framework import viewsets, permissions, status, serializers,generics
from rest_framework.response import Response
from users.authentication import CustomJWTAuthentication
from .models import RecyclerEPR, ProducerEPR,EPRCredit,EPRTarget,CreditOffer,CounterCreditOffer,Transaction,WasteType,PurchasesRequest, ProducerType,RecyclerType,ProductType,CreditType, allowed_docs
from .serializers import RecyclerEPRSerializer, ProducerEPRSerializer, EPRCreditSerializer,EPRTargetSerializer, CreditOfferSerializer,CounterCreditOfferSerializer,TransactionSerializer, WasteTypeSerializer, WasteTypeNameSerializer, PurchasesRequestSerializer, ProducerTypeSerializer, RecyclerTypeSerializer, ProductTypeSerializer, CreditTypeSerializer
from users.models import Recycler, Producer
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError, ObjectDoesNotExist
from django.db.models import Q
from django.core.mail import send_mail

from django.db.models.functions import ExtractYear
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404
from .filters import CreditOfferFilter
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F

from superadmin.models import TransactionFee
from superadmin.views import CaseInsensitiveSearchFilter
from django.http import Http404

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from decouple import config 
from .filters import indian_states
transaction_email = config('TRANSACTION_EMAIL') 

class IsRecycler(permissions.BasePermission):
    """Custom permission to allow only recycler users"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and isinstance(request.user,Recycler)

    def has_object_permission(self, request, view, obj):
        return obj.recycler == request.user 


class IsProducer(permissions.BasePermission):
    """Custom permission to allow only producer users"""
    def has_permission(self, request, view):  
        return request.user.is_authenticated and isinstance(request.user,Producer)

    def has_object_permission(self, request, view, obj):
        return obj.producer == request.user


# RECYLER -> CREATE EPR ACCOUNT ✅ 
class RecyclerEPRViewSet(viewsets.ModelViewSet):

    serializer_class = RecyclerEPRSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated,IsRecycler]
    parser_classes = (MultiPartParser, FormParser,JSONParser)
 # Fields that can be used for ordering
    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    filterset_fields = ['waste_type', 'is_approved', 'city', 'state']  
    search_fields = ['epr_registration_number', 'epr_registered_name','epr_registration_date', 'city', 'state', 'address']  
    ordering_fields = ['created_at']  # Adjust this to match your model's field name
    ordering = ['-created_at']  # '-' indicates descending order

    def get_queryset(self):
            queryset = RecyclerEPR.objects.filter(recycler=self.request.user)
            waste_type = self.request.query_params.get('waste_type', None)
            is_approved = self.request.query_params.get('is_approved')

            if waste_type:
                queryset = queryset.filter(waste_type=waste_type)

            if is_approved:
                queryset = queryset.filter(is_approved=True)

            return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
            "status": False,
            "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()  # Automatically filters by ID and checks permissions
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)
    # PUT
    def update(self, request, *args, **kwargs):
       
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)
            
            if 'is_approved' in request.data:
                return Response({
                    "status": False,
                    "error": "Only admins can modify the 'is_approved' field."
                }, status=status.HTTP_403_FORBIDDEN)


            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": str(e.detail) if e.detail else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # PATCH
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)
            
            if 'is_approved' in request.data:
                return Response({
                    "status": False,
                    "error": "Only admins can modify the 'is_approved' field."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": str(e.detail) if e.detail else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        # serializer.save(producer=self.request.user)
        try:
            instance = serializer.save(recycler=self.request.user)
            try:
                instance.full_clean()
            except DjangoValidationError as e:
                # Delete the instance since it's invalid
                instance.delete()
                # Re-raise as a DRF ValidationError
                raise serializers.ValidationError({"error":  e.detail if hasattr(e, 'detail') else str(e), "status": False})

        except Exception as e:
            raise serializers.ValidationError({"error": str(e),"status":False})
    
    def create(self, request, *args, **kwargs):
        try:
            recycler = request.user  
            if not self.is_profile_complete(recycler):
                return Response({
                    "status": False,
                    "error": "You must complete your profile  before creating an EPR account."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'is_approved' in request.data:
                return Response({
                    "status": False,
                    "error": "Only admins can modify the 'is_approved' field."
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
             raise serializers.ValidationError({"error": e.detail if hasattr(e, 'detail') else str(e),"status":False}) 
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def is_profile_complete(self, recycler):
        """
        Check if the recycler's profile is complete based on all required fields.
        """
        required_fields = [
                'email', 'mobile_no', 'company_name', 'address', 'full_name',
                'city', 'state', 
                'designation','gst_number','pcb_number',
                'account_holder_name', 'account_number', 'bank_name', 
                'ifsc_code', 'branch_name'
        ]
        for field in required_fields:
            value = getattr(recycler, field, None)
            if value is None or value == "":
                return False
        return True


# RECYLER -> CREATE CREDIT   ✅ 
class EPRCreditViewSet(viewsets.ModelViewSet):
    serializer_class = EPRCreditSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsRecycler]
    parser_classes = (MultiPartParser, FormParser,JSONParser)
     # Fields that can be used for ordering
    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    search_fields = ['epr_registration_number', 'waste_type', 'product_type', 'state', 'credit_type','year'] 
    ordering_fields = ['created_at']  # Adjust this to match your model's field name
    ordering = ['-created_at']  # '-' indicates descending order


    def get_queryset(self):
       
        queryset = EPRCredit.objects.filter(recycler=self.request.user)

        # Filter by epr_account_id if provided
        epr_account_id = self.request.query_params.get("epr_id")
        if epr_account_id:
            try:
                get_epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
                queryset = queryset.filter(epr_account=get_epr_account)
            except RecyclerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_id or not authorized."})

        # Filter by year only if provided in query
        year = self.request.query_params.get("year")
        if year:  # Only apply filter if year is given
            try:
                year = int(year)  # Convert to integer to validate
                queryset = queryset.annotate(year_extracted=ExtractYear('year')).filter(year_extracted=year)
            except ValueError:
                raise serializers.ValidationError({"error": "Invalid year format. Please provide a valid 4-digit year (e.g., 2023)."})

        return queryset

    # GET - List
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # GET - Retrieve
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Http404:
            return Response({
            "status": False,
            "error": "No Epr Credit matches the given id"
        }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

    # POST - Create with Profile Completion Check
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def perform_create(self, serializer):
        instance = None
        try:
            instance = serializer.save(recycler=self.request.user)
            if instance is None:
              raise ValueError("Serializer.save() returned None, expected an instance.")
            instance.full_clean()  
        except DjangoValidationError as e:
            if instance is not None: 
                instance.delete()
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'error': str(e)})
        except Exception as e:
            if instance is not None:  # Only delete if instance was created
               instance.delete()
            raise serializers.ValidationError({"error": str(e)})

    # PUT - Update
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PATCH - Partial Update
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_serializer(self, *args, **kwargs):
        try:
            if self.request.method == "POST":
                epr_account_id = self.request.query_params.get("epr_id")
                if not epr_account_id:
                    raise serializers.ValidationError({"error": "epr_id is required in query parameters."})

                try:
                    epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
                    if not epr_account.is_approved:
                        raise serializers.ValidationError({"error": "Cannot create credit: EPR account is not approved by admin."})
                except RecyclerEPR.DoesNotExist:
                    raise serializers.ValidationError({"error": "Invalid epr_id or not authorized."})

                request_data = {}
                for key, value in self.request.data.items():
                    if isinstance(value, list) and value:
                        request_data[key] = value[0]
                    else:
                        request_data[key] = value

                request_data.update({
                    "epr_account": epr_account.id,
                    "recycler": self.request.user.id, 
                    "epr_registration_number": epr_account.epr_registration_number,
                    "waste_type": epr_account.waste_type,
                })

                kwargs["data"] = request_data
            return super().get_serializer(*args, **kwargs)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to delete this record."
                }, status=status.HTTP_403_FORBIDDEN)

            self.perform_destroy(instance)
            return Response({
                "status": True,
                "message": "EPR account deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

# RECYLER -> CREATE CREDIT OFFER ✅ 
class CreditOfferViewSet(viewsets.ModelViewSet):
    serializer_class = CreditOfferSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsRecycler]
    parser_classes = (MultiPartParser, FormParser,JSONParser)

      # Fields that can be used for ordering
    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    search_fields = ['epr_registration_number', 'waste_type', 'product_type', 'offer_title', 'credit_type','FY']
    ordering_fields = ['created_at']  # Adjust this to match your model's field name
    ordering = ['-created_at']  # '-' indicates descending order


    def get_queryset(self):
        epr_account_id = self.request.query_params.get("epr_id")
        epr_credit_id = self.request.query_params.get("epr_credit_id")
        
        queryset = CreditOffer.objects.filter(recycler=self.request.user)
        
        if epr_account_id:
            try:
                get_epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
                queryset = queryset.filter(epr_account=get_epr_account)
            except RecyclerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_account_id or not authorized."})
            
        if epr_credit_id:
            try:
                get_epr_credit = EPRCredit.objects.get(id=epr_credit_id, recycler=self.request.user)
                queryset = queryset.filter(epr_credit=get_epr_credit)
            except EPRCredit.DoesNotExist:
                raise serializers.ValidationError({"error": "No record found for credit with the given EPR account."})
            
        return queryset

    # GET - List
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # GET - Retrieve
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Http404:
            return Response({
            "status": False,
            "error": "No Record matches the given id"
        }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

    # POST - Create with Profile Completion Check
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
    def perform_create(self, serializer):
        try:
            epr_account_id = self.request.query_params.get("epr_id")
            epr_credit_id = self.request.query_params.get("epr_credit_id")

            get_epr_account = RecyclerEPR.objects.get(id=epr_account_id)
            get_epr_credit = EPRCredit.objects.get(id=epr_credit_id)


            credit_offer = serializer.save(
                recycler=self.request.user,
                epr_account=get_epr_account,
                epr_credit=get_epr_credit,
            )
            # get_epr_credit.current_processing += credit_offer.credit_available
            # get_epr_credit.save()

        except RecyclerEPR.DoesNotExist:
            raise ValidationError({"error": "Invalid epr_account_id or not authorized."})
        except EPRCredit.DoesNotExist:
            raise ValidationError({"error": "Invalid epr_credit_id or not authorized."})
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            raise ValidationError({"error": str(e)})

    # PUT - Update
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PATCH - Partial Update
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_serializer(self, *args, **kwargs):
        try:
            if self.request.method == "POST":
                epr_id = self.request.query_params.get("epr_id")
                epr_credit_id = self.request.query_params.get("epr_credit_id")

                if not epr_id or not epr_credit_id:
                    raise ValidationError({"error": "Both epr_id and epr_credit_id are required in query parameters."})

                try:
                    get_epr_account = RecyclerEPR.objects.get(id=epr_id, recycler=self.request.user)
                    if not get_epr_account.is_approved:
                     raise ValidationError({"error": "Cannot create credit offer: EPR account is not approved by admin."})
                    epr_credit = EPRCredit.objects.get(id=epr_credit_id, recycler=self.request.user, epr_account=get_epr_account)
                except RecyclerEPR.DoesNotExist:
                    raise ValidationError({"error": "Invalid epr_account_id or not authorized."})
                except EPRCredit.DoesNotExist:
                    raise ValidationError({"error": "No record found for credit with the given EPR account."})

                request_data = {key: value[0] if isinstance(value, list) and value else value for key, value in self.request.data.items()}
                
                # TODO -> ADD SOME ERROR REPSONSE IF EPR's reg number != epr_credit's reg number
                
                # Validate credit_available against comulative_certificate_potential
                credit_available = float(request_data.get("credit_available", 0.0))
                if credit_available > epr_credit.available_certificate_value:
                    raise ValidationError(
                       f"Credit offer's credit {credit_available} can't exceed availabe certificate value {epr_credit.available_certificate_value}"
                    )
                
                # Add additional fields
                request_data.update({
                    "epr_account": get_epr_account.id,
                    "epr_registration_number": epr_credit.epr_registration_number,
                    "waste_type": epr_credit.waste_type,
                    "epr_credit": epr_credit.id,
                    "credit_type":epr_credit.credit_type,
                    "product_type":epr_credit.product_type
                    
                })

                kwargs["data"] = request_data
              # Handle PATCH requests with special care for JSONField
            elif self.request.method == "PATCH" :
                # Get original data
                instance = self.get_object()
                # Create a separate data dictionary for patch
                patch_data = dict(self.request.data)
                 # Handle case where values are lists (from MultiPartParser/FormParser)
                patch_data = {key: value[0] if isinstance(value, list) and value else value for key, value in patch_data.items()}
                # Special handling for trail_documents if it's coming in as a string
                # if "trail_documents" in patch_data:
                #     trail_documents_value = patch_data["trail_documents"]
                #     # If it's a string representation of JSON, parse it
                #     if isinstance(trail_documents_value, list) and trail_documents_value:
                #         import json
                #         try:
                #             # Strip any whitespace/newlines and parse
                #             cleaned_string = trail_documents_value[0].strip()
                #             patch_data["trail_documents"] = json.loads(cleaned_string)
                #         except json.JSONDecodeError:
                #             raise ValidationError({"error": "Invalid JSON format for trail_documents"})
                # print(patch_data)

                
                # kwargs["data"] = patch_data
                # kwargs["partial"] = True

                if "trail_documents" in patch_data:
                    trail_documents_value = patch_data["trail_documents"]
                    if isinstance(trail_documents_value, str):
                        import json
                        try:
                            # Parse the string into a Python list
                            patch_data["trail_documents"] = json.loads(trail_documents_value)
                        except json.JSONDecodeError:
                            raise ValidationError({"error": "Invalid JSON format for trail_documents"})

                kwargs["data"] = patch_data
                kwargs["partial"] = True
        

            return super().get_serializer(*args, **kwargs)

        except Exception as e:
            raise ValidationError({"error": str(e)})

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to delete this record."
                }, status=status.HTTP_403_FORBIDDEN)

            self.perform_destroy(instance)
            return Response({
                "status": True,
                "message": "Credit record deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

# PRODUCER -> CREATE EPR ACCOUNT ✅ 
class ProducerEPRViewSet(viewsets.ModelViewSet):
    serializer_class = ProducerEPRSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsProducer]
    parser_classes = (MultiPartParser, FormParser,JSONParser)
    filter_backends = [DjangoFilterBackend]  
    filterset_fields = ['waste_type']

       # Fields that can be used for ordering
    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    filterset_fields = ['waste_type', 'is_approved', 'city', 'state']  
    search_fields = ['epr_registration_number', 'epr_registered_name','epr_registration_date', 'city', 'state', 'address'] 
    ordering_fields = ['created_at']  # Adjust this to match your model's field name
    ordering = ['-created_at']  # '-' indicates descending order

    def get_queryset(self):
        queryset =  ProducerEPR.objects.filter(producer=self.request.user)
        waste_type = self.request.query_params.get('waste_type', None)
        is_approved = self.request.query_params.get('is_approved')

        if waste_type:
            queryset = queryset.filter(waste_type=waste_type)

        if is_approved:
            queryset = queryset.filter(is_approved=True)

        return queryset

    # GET - List
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # GET - Retrieve
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

    # POST - Create with Profile Completion Check
    def create(self, request, *args, **kwargs):
        try:
            # Check if the user's profile is complete
            producer = request.user  # Assuming Producer is your user model
            if not self.is_profile_complete(producer):
                return Response({
                    "status": False,
                    "error": "You must complete your profile before creating an EPR record."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'is_approved' in request.data:
                return Response({
                    "status": False,
                    "error": "Only admins can modify the 'is_approved' field."
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PUT - Update
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)
            
            if 'is_approved' in request.data:
                return Response({
                    "status": False,
                    "error": "Only admins can modify the 'is_approved' field."
                }, status=status.HTTP_403_FORBIDDEN)


            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PATCH - Partial Update
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)
            
            if 'is_approved' in request.data:
                return Response({
                    "status": False,
                    "error": "Only admins can modify the 'is_approved' field."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        instance = None

        try:
            instance = serializer.save(producer=self.request.user)
            if instance is None:
              raise ValueError("Serializer.save() returned None, expected an instance.")
            instance.full_clean()  
        except DjangoValidationError as e:
            if instance is not None: 
                instance.delete()
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'error': str(e)})
        except Exception as e:
            if instance is not None:  # Only delete if instance was created
               instance.delete()
            raise serializers.ValidationError({"error": str(e)})

    def is_profile_complete(self, producer):

        required_fields = [
                'email', 'mobile_no', 'company_name', 'address', 'full_name',
                'city', 'state',  
                'designation','gst_number','pcb_number'
        ]
        for field in required_fields:
            value = getattr(producer, field, None)
            if value is None or value == "":
                return False
        return True

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to delete this record."
                }, status=status.HTTP_403_FORBIDDEN)

            self.perform_destroy(instance)
            return Response({
                "status": True,
                "message": "EPR account deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

# PRODUCER -> ADD TARGET  ✅ 
class EPRTargetViewSet(viewsets.ModelViewSet):
    serializer_class = EPRTargetSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsProducer]
    parser_classes = (MultiPartParser, FormParser,JSONParser)

    # Fields that can be used for ordering
    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    search_fields = ['epr_registration_number', 'waste_type', 'product_type', 'FY', 'credit_type','state']
    ordering_fields = ['created_at']  # Adjust this to match your model's field name
    ordering = ['-created_at']  # '-' indicates descending order

    def get_queryset(self):
        epr_account_id = self.request.query_params.get("epr_id")
        if epr_account_id:
            try:
                get_epr_account = ProducerEPR.objects.get(id=epr_account_id, producer=self.request.user)
                return EPRTarget.objects.filter(producer=self.request.user, epr_account=get_epr_account)
            except ProducerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_id or not authorized."})
        return EPRTarget.objects.filter(producer=self.request.user)

    # GET - List
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # GET - Retrieve
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

    # POST - Create with Profile Completion Check
    def create(self, request, *args, **kwargs):
        try:

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PUT - Update
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PATCH - Partial Update
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_serializer(self, *args, **kwargs):
        if self.request.method == "POST":
            epr_account_id = self.request.query_params.get("epr_id")
            if not epr_account_id:
                raise serializers.ValidationError({"error": "epr_id is required in query parameters."})

            try:
                epr_account = ProducerEPR.objects.get(id=epr_account_id, producer=self.request.user)
                if not epr_account.is_approved:
                        raise serializers.ValidationError({"error": "Cannot create credit: EPR account is not approved by admin."})
         
            except ProducerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_id or not authorized."})

            request_data = {}
            for key, value in self.request.data.items():
                if isinstance(value, list) and value:
                    request_data[key] = value[0]
                else:
                    request_data[key] = value

            request_data.update({
                "epr_account": epr_account.id,
                "producer": self.request.user.id,  
                "epr_registration_number": epr_account.epr_registration_number,
                "waste_type": epr_account.waste_type,
            })

            kwargs["data"] = request_data
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        instance = None

        try:
            instance = serializer.save(producer=self.request.user)
            if instance is None:
              raise ValueError("Serializer.save() returned None, expected an instance.")
            instance.full_clean()  
        except DjangoValidationError as e:
            if instance is not None: 
                instance.delete()
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'error': str(e)})
        except Exception as e:
            if instance is not None:  
               instance.delete()
            raise serializers.ValidationError({"error": str(e)})

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to delete this record."
                }, status=status.HTTP_403_FORBIDDEN)

            self.perform_destroy(instance)
            return Response({
                "status": True,
                "message": "Target record deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)


# PRODUCER -> CREATE COUNTER CREDIT OFFER | RECYCLER APPROVE OR REJECT IT
class CounterCreditOfferViewSet(viewsets.ModelViewSet):
    serializer_class = CounterCreditOfferSerializer
    authentication_classes = [CustomJWTAuthentication]
    parser_classes = (MultiPartParser, FormParser,JSONParser)  

     # Fields that can be used for ordering
    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    search_fields = ['FY','status','credit_offer__waste_type','credit_offer__product_type','credit_offer__credit_type']
    ordering_fields = ['created_at']  # Adjust this to match your model's field name
    ordering = ['-created_at']  # '-' indicates descending order


    def get_permissions(self):
        try:
            if self.action == 'create':
                permission_classes = [permissions.IsAuthenticated, IsProducer]
            elif self.action in ['update', 'partial_update']:
                permission_classes = [permissions.IsAuthenticated, IsRecycler]
            else:  # list, retrieve
                permission_classes = [permissions.IsAuthenticated]
            return [permission() for permission in permission_classes]
        except Exception as e:
            raise ValidationError({"error": f"Permission error: {str(e)}"})

    def get_queryset(self):
        user = self.request.user
        credit_offer_id = self.request.query_params.get("credit_offer_id")
        queryset = CounterCreditOffer.objects.none() 

        # Determine user type and filter field
        if isinstance(user, Producer):
            filter_field = "producer"
            queryset = CounterCreditOffer.objects.filter(**{filter_field: user})
        elif isinstance(user, Recycler):
            filter_field = "recycler"
            queryset = CounterCreditOffer.objects.filter(**{filter_field: user}).exclude(status="rejected")
        else:
            return queryset  # Return empty queryset for unsupported user types

        # Base queryset for the user

        if credit_offer_id:
            try:
                # For Recycler, ensure they own the CreditOffer; Producers don't need this check
                credit_offer_filter = (
                    Q(id=credit_offer_id, recycler=user) if isinstance(user, Recycler)
                    else Q(id=credit_offer_id)
                )
                get_credit_offer = CreditOffer.objects.get(credit_offer_filter)
                queryset = queryset.filter(credit_offer=get_credit_offer)
            except CreditOffer.DoesNotExist:
                error_msg = (
                    "Credit offer not found or not authorized." if isinstance(user, Recycler)
                    else "Credit offer not found."
                )
                raise ValidationError({"error": error_msg})

        return queryset

    # GET - List
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # GET - Retrieve
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PUT - Update
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "Only authorized recycler can update record."
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PATCH - Partial Update
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this record."
                }, status=status.HTTP_403_FORBIDDEN)
            
            if instance.quantity > instance.credit_offer.credit_available and request.data["status"] == "approved":
                return Response({
                    "status": False,
                    "error": f"Credit offer has only { instance.credit_offer.credit_available } credit for counter credit offer's { instance.quantity }"
                }, status=status.HTTP_400_BAD_REQUEST)

            

    # TODO SEND AN EMAIL TO THE PRODUCER  IF THE OFFER GET ACCEPTED
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            producer = instance.producer
            recycler = instance.recycler

            fee = 0
            fees = TransactionFee.objects.first()
            if fees:
                fee = fees.transaction_fee
                
            # Common fields
            email = 'support@circle8.in'
            contact_number = '+91 9620220013'

            # Email to Producer (Stylish HTML)
            producer_subject = "Counter Credit Offer"
                
            # calculate total price
            price_per_credit = instance.credit_offer.price_per_credit
            quantity = instance.quantity
            value = price_per_credit*quantity
            processing_fee = value*0.05
            gst = (value+processing_fee)*0.18
            total_price = value + processing_fee + gst

            if instance.status == 'approved' and instance.is_approved:

              # Send email to Producer if Counter Credit Offer is approved
                producer_html_message = (

                    f"<!DOCTYPE html>"
                    f"<html>"
                    f"<head>"
                    f"    <meta charset='UTF-8'>"
                    f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                    f"    <title>Counter Credit Offer Approval Notification</title>"
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
                    f"        <h2>📢 Counter Credit Offer Approval Notification</h2>"
                    f"        <p>Dear <strong>{producer.full_name}</strong>,</p>"
                    f"        <p>Your counter credit offer has been approved by <strong>{recycler.full_name}</strong>. Below are the details:</p>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <h3>🛠 Counter Offer Details</h3>"
                    f"            <table>"
                    f"                <tr><th>Offered By</th><td>{recycler.unique_id}</td></tr>"
                    f"                <tr><th>Work Order Date</th><td>{instance.created_at}</td></tr>"
                    f"                <tr><th>Credit Offer Title</th><td>{instance.credit_offer.offer_title}</td></tr>"
                    f"                <tr><th>Waste Type</th><td>{instance.credit_offer.waste_type}</td></tr>"
                    f"                <tr><th>Credit Type</th><td>{instance.credit_offer.credit_type}</td></tr>"
                    f"                <tr><th>Price per Credit</th><td>{instance.offer_price}</td></tr>"
                    f"                <tr><th>Total Price (Including GST and Fee)</th><td>{total_price}</td></tr>"
                    f"                <tr><th>Product Type</th><td>{instance.credit_offer.product_type}</td></tr>"
                    f"                <tr><th>Producer Type</th><td>{instance.producer_epr.producer_type}</td></tr>"
                    f"                <tr><th>Quantity</th><td>{instance.quantity}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <table>"
                    f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                    f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <h3>📁 Trail Documents</h3>"
                    f"            <ul>"
                    f"                   {''.join([f'<li>✅ {doc}</li>' for doc in instance.credit_offer.trail_documents if doc.strip()])}"
                    f"            </ul>"
                    f"        </div>"
                    f"        "
                    f"        <div class='status'>Status: {instance.status}</div>"
                    f"        "
                    f"        <div class='cta'>"
                    f"            <a href='#'>Proceed with Transaction</a>"
                    f"        </div>"
                    f"        "
                    f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                    f"            This is an automated message. Please do not reply directly to this email."
                    f"        </p>"
                    f"    </div>"
                    f"</body>"
                    f"</html>"
                )
                send_mail(
                    subject=producer_subject,
                    message="",
                    from_email=transaction_email,
                    recipient_list=[producer.email],
                    fail_silently=False,
                    html_message=producer_html_message
                )
                            # Email to Recycler (Stylish HTML)
                # recycler_subject = "Counter Credit Offer Approved - Action Required"
                # recycler_html_message = (
                #     f"<!DOCTYPE html>"
                #     f"<html>"
                #     f"<head>"
                #     f"    <meta charset='UTF-8'>"
                #     f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                #     f"    <title>Counter Credit Offer Approval Notification</title>"
                #     f"    <style>"
                #     f"        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}"
                #     f"        .container {{ max-width: 600px; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}"
                #     f"        h2 {{ color: #2c3e50; text-align: center; }}"
                #     f"        .details {{ margin: 20px 0; }}"
                #     f"        .details table {{ width: 100%; border-collapse: collapse; }}"
                #     f"        .details th, .details td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}"
                #     f"        .details th {{ background-color: #3498db; color: white; }}"
                #     f"        .status {{ text-align: center; padding: 10px; font-weight: bold; background-color: #27ae60; color: white; border-radius: 4px; }}"
                #     f"        .cta {{ text-align: center; margin-top: 20px; }}"
                #     f"        .cta a {{ text-decoration: none; background: #27ae60; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }}"
                #     f"    </style>"
                #     f"</head>"
                #     f"<body>"
                #     f"    <div class='container'>"
                #     f"        <h2>📢 Counter Credit Offer Approval Notification</h2>"
                #     f"        <p>Dear <strong>{recycler.full_name}</strong>,</p>"
                #     f"        <p>You have approved a counter credit offer from <strong>{producer.full_name}</strong>. Below are the details:</p>"
                #     f"        <div class='details'>"
                #     f"            <h3>🛠 Counter Offer Details</h3>"
                #     f"            <table>"
                #     f"                <tr><th>Requested By</th><td>{producer.unique_id}</td></tr>"
                #     f"                <tr><th>Work Order Date</th><td>{instance.created_at}</td></tr>"
                #     f"                <tr><th>Credit Offer Title</th><td>{instance.credit_offer.offer_title}</td></tr>"
                #     f"                <tr><th>Waste Type</th><td>{instance.credit_offer.waste_type}</td></tr>"
                #     f"                <tr><th>Credit Type</th><td>{instance.credit_offer.credit_type}</td></tr>"
                #     f"                <tr><th>Price per Credit</th><td>{instance.offer_price}</td></tr>"
                #     f"                <tr><th>Total Price (Including GST and Fee)</th><td>{total_price}</td></tr>"
                #     f"                <tr><th>Product Type</th><td>{instance.credit_offer.product_type}</td></tr>"
                #     f"                <tr><th>Producer Type</th><td>{instance.producer_epr.producer_type}</td></tr>"
                #     f"                <tr><th>Quantity</th><td>{instance.quantity}</td></tr>"
                #     f"            </table>"
                #     f"        </div>"
                #     f"        <div class='details'>"
                #     f"            <h3>🏭 Producer Details</h3>"
                #     f"            <table>"
                #     f"                <tr><th>EPR Registration Number</th><td>{instance.producer_epr.epr_registration_number}</td></tr>"
                #     f"                <tr><th>EPR Registered Name</th><td>{instance.producer_epr.epr_registered_name}</td></tr>"
                #     f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                #     f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                #     f"            </table>"
                #     f"        </div>"
                #     f"        <div class='details'>"
                #     f"            <h3>📁 Trail Documents</h3>"
                #     f"            <ul>"
                #     f"                   {''.join([f'<li>✅ {doc}</li>' for doc in instance.credit_offer.trail_documents if doc.strip()])}"
                #     f"            </ul>"
                #     f"        </div>"
                #     f"        <div class='status'>Status: {instance.status}</div>"
                #     f"        <div class='cta'>"
                #     f"            <a href='#'>Review Transaction Details</a>"
                #     f"        </div>"
                #     f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                #     f"            This is an automated message. Please do not reply directly to this email."
                #     f"        </p>"
                #     f"    </div>"
                #     f"</body>"
                #     f"</html>"
                # )
                # send_mail(
                #     subject=recycler_subject,
                #     message="",
                #     from_email=settings.DEFAULT_FROM_EMAIL,
                #     recipient_list=[recycler.email],
                #     fail_silently=False,
                #     html_message=recycler_html_message
                # )
            if instance.status == 'rejected':

              # Send email to Producer if Counter Credit Offer is rejected
                producer_html_message = (

                    f"<!DOCTYPE html>"
                    f"<html>"
                    f"<head>"
                    f"    <meta charset='UTF-8'>"
                    f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                    f"    <title>Counter Credit Offer Approval Notification</title>"
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
                    f"        <h2>📢 Counter Credit Offer Rejection Notification</h2>"
                    f"        <p>Dear <strong>{producer.full_name}</strong>,</p>"
                    f"        <p>Your counter credit offer has been rejected by <strong>{recycler.full_name}</strong>. Below are the details:</p>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <h3>🛠 Counter Offer Details</h3>"
                    f"            <table>"
                    f"                <tr><th>Offered By</th><td>{recycler.unique_id}</td></tr>"
                    f"                <tr><th>Work Order Date</th><td>{instance.created_at}</td></tr>"
                    f"                <tr><th>Credit Offer Title</th><td>{instance.credit_offer.offer_title}</td></tr>"
                    f"                <tr><th>Waste Type</th><td>{instance.credit_offer.waste_type}</td></tr>"
                    f"                <tr><th>Credit Type</th><td>{instance.credit_offer.credit_type}</td></tr>"
                    f"                <tr><th>Price per Credit</th><td>{instance.offer_price}</td></tr>"
                    f"                <tr><th>Total Price (Including GST and Fee)</th><td>{total_price}</td></tr>"
                    f"                <tr><th>Product Type</th><td>{instance.credit_offer.product_type}</td></tr>"
                    f"                <tr><th>Producer Type</th><td>{instance.producer_epr.producer_type}</td></tr>"
                    f"                <tr><th>Quantity</th><td>{instance.quantity}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <table>"
                    f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                    f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <h3>📁 Trail Documents</h3>"
                    f"            <ul>"
                    f"                   {''.join([f'<li>✅ {doc}</li>' for doc in instance.credit_offer.trail_documents if doc.strip()])}"
                    f"            </ul>"
                    f"        </div>"
                    f"        "
                    f"        <div class='status'>Status: {instance.status}</div>"
                    f"        "
                    f"        <div class='cta'>"
                    f"            <a href='#'>Proceed with Transaction</a>"
                    f"        </div>"
                    f"        "
                    f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                    f"            This is an automated message. Please do not reply directly to this email."
                    f"        </p>"
                    f"    </div>"
                    f"</body>"
                    f"</html>"
                )
                send_mail(
                    subject=producer_subject,
                    message="",
                    from_email=transaction_email,
                    recipient_list=[producer.email],
                    fail_silently=False,
                    html_message=producer_html_message
                )


            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_serializer(self, *args, **kwargs):  
        try:
            if self.request.method == "POST":
                credit_offer_id = self.request.query_params.get("credit_offer_id")
                if not credit_offer_id:
                    raise ValidationError(
                        {"error": "credit_offer_id is required for creating a counter credit offer."}
                    )

                try:
                    get_credit_offer = CreditOffer.objects.get(id=credit_offer_id)
                except CreditOffer.DoesNotExist:
                    raise ValidationError({"error": "Invalid credit_offer_id or not authorized."})

                request_data = {}
                for key, value in self.request.data.items():
                    if isinstance(value, list) and value:
                        request_data[key] = value[0]
                    else:
                        request_data[key] = value

                request_data.update({
                    "recycler": get_credit_offer.recycler.id,
                    "credit_offer": get_credit_offer.id,
                    "producer": self.request.user.id
                })

                kwargs["data"] = request_data

            return super().get_serializer(*args, **kwargs)

        except Exception as e:
            raise ValidationError({"error": f"Serializer error: {str(e)}"})
        
    # POST - Create with Profile Completion Check (Producer only)
    def create(self, request, *args, **kwargs):
        try:

        
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            # error_message = "An unexpected error occurred"
            # error_message = e.detail if hasattr(e, 'detail') else str(e)

            # if isinstance(error_message,dict):
            #     if error_message['error']:
            #         error_message = error_message['error']
    
            # # Since e.detail is a dict, access the 'error' key
            # if isinstance(e.detail, dict) and 'error' in e.detail:
            #     error_list = e.detail['error']  # Get the list under 'error' key
            #     if isinstance(error_list, list) and len(error_list) > 0:
            #         # Access the first ErrorDetail object
            #         first_error = error_list[0]
            #         # Extract the string from the ErrorDetail
            #         error_message = first_error.string if hasattr(first_error, 'string') else str(first_error)
            
            # if isinstance(error_message,list):
            #     error_message = error_message[0]
            error_message = e.detail if hasattr(e, 'detail') else str(e)
    
            # Handle case where error_message is a dict
            if isinstance(error_message, dict):
                # Check if 'error' key exists before accessing it
                if 'error' in error_message:
                    error_list = error_message['error']
                    if isinstance(error_list, list) and len(error_list) > 0:
                        first_error = error_list[0]
                        error_message = str(first_error)
                else:
                    # Handle other possible error keys (like 'producer_epr' in your case)
                    for key, value in error_message.items():
                        if isinstance(value, list) and len(value) > 0:
                            first_error = value[0]
                            error_message = str(first_error)
                            break
                    else:
                        # Fallback if no list found in dict
                        error_message = str(error_message)
            
            # Handle case where error_message is a list
            elif isinstance(error_message, list) and len(error_message) > 0:
                error_message = str(error_message[0])
            
            # Default case
            else:
                error_message = str(error_message)
            return Response({
                "status": False,
                "error": error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        """Handles object creation and assigns producer, recycler, and offer details."""
        try:
            if isinstance(self.request.user, Producer):
                credit_offer_id = self.request.query_params.get("credit_offer_id")
                try:
                    get_credit_offer = CreditOffer.objects.get(id=credit_offer_id)
                except CreditOffer.DoesNotExist:
                    raise serializer.ValidationError("Invalid credit_offer_id or not authorized.")
                    
                producer_epr_id = self.request.data['producer_epr']
                producer_epr = ProducerEPR.objects.get(id=producer_epr_id, producer=self.request.user)

                if producer_epr.waste_type !=  get_credit_offer.waste_type:
                   raise ValidationError(f"Your EPR Account's Waste Type does not matches the the waste type of the credit offer you want to buy. Epr's waste type:{producer_epr.waste_type} Credit offer's waste type: {get_credit_offer.waste_type}")
               
                #CHECK IF the appropriate target exist or not

                validated_data = serializer.validated_data
                quantity = validated_data.get("quantity")
                epr_target = EPRTarget.objects.filter(
                    epr_account=producer_epr,
                    waste_type=get_credit_offer.waste_type,
                    product_type=get_credit_offer.product_type,
                    credit_type=get_credit_offer.credit_type,
                    is_achieved=False
                ).annotate(
                    remaining_quantity=F('target_quantity') - F('achieved_quantity') - F('blocked_target')
                ).filter(
                    remaining_quantity__gte=quantity
                ).first()


                if not epr_target:
                    raise ValidationError(
                         f"No matching EPR Target found. Please create an EPR target for the given EPR account where credit type should be {get_credit_offer.credit_type} and product type should be {get_credit_offer.product_type} and remaining Target quantity is higher than {quantity}"
                    )



                 # Validate quantity against credit_available
   
                credit_available = get_credit_offer.credit_available
                blocked_credit = get_credit_offer.blocked_credit
                unblocked_credit = credit_available - blocked_credit

                if quantity is None:
                    raise ValidationError("Quantity is required to create a counter credit offer.")

                if quantity  > unblocked_credit:
                    raise ValidationError({
                        f"Quantity ({quantity}) exceeds available unblocked credits ({unblocked_credit}) in the credit offer."
                    })

                counter_credit_offer = serializer.save(
                    producer=self.request.user,
                    recycler=get_credit_offer.recycler,
                    credit_offer=get_credit_offer,
                    status='pending',
                    is_approved=False
                )

                fee = 0
                fees = TransactionFee.objects.first()
                if fees:
                    fee = fees.transaction_fee

                # Common fields
                email = 'support@circle8.in'
                contact_number = '+91 9620220013'

                total_price = (counter_credit_offer.credit_offer.price_per_credit * counter_credit_offer.quantity) + (counter_credit_offer.credit_offer.price_per_credit * counter_credit_offer.quantity) * 0.18 + fee

                
                # Send email to Recycler
                producer = counter_credit_offer.producer
                recycler = counter_credit_offer.recycler
                recycler_subject = "Counter Credit Offer Request"
                recycler_html_message = (
                    f"<!DOCTYPE html>"
                    f"<html>"
                    f"<head>"
                    f"    <meta charset='UTF-8'>"
                    f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                    f"    <title>Counter Credit Offer Request Notification</title>"
                    f"    <style>"
                    f"        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}"
                    f"        .container {{ max-width: 600px; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}"
                    f"        h2 {{ color: #2c3e50; text-align: center; }}"
                    f"        .details {{ margin: 20px 0; }}"
                    f"        .details table {{ width: 100%; border-collapse: collapse; }}"
                    f"        .details th, .details td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}"
                    f"        .details th {{ background-color: #3498db; color: white; }}"
                    f"        .status {{ text-align: center; padding: 10px; font-weight: bold; background-color: #27ae60; color: white; border-radius: 4px; }}"
                    f"        .cta {{ text-align: center; margin-top: 20px; }}"
                    f"        .cta a {{ text-decoration: none; background: #27ae60; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }}"
                    f"    </style>"
                    f"</head>"
                    f"<body>"
                    f"    <div class='container'>"
                    f"        <h2>📢 Counter Credit Offer Approval Notification</h2>"
                    f"        <p>Dear <strong>{recycler.full_name}</strong>,</p>"
                    f"        <p>You have a counter credit offer from <strong>{producer.full_name}</strong>. Below are the details:</p>"
                    f"        <div class='details'>"
                    f"            <h3>🛠 Counter Offer Details</h3>"
                    f"            <table>" 
                    f"                <tr><th>Requested By</th><td>{producer.unique_id}</td></tr>"
                    f"                <tr><th>Work Order Date</th><td>{counter_credit_offer.created_at}</td></tr>"
                    f"                <tr><th>Credit Offer Title</th><td>{counter_credit_offer.credit_offer.offer_title}</td></tr>"
                    f"                <tr><th>Waste Type</th><td>{counter_credit_offer.credit_offer.waste_type}</td></tr>"
                    f"                <tr><th>Credit Type</th><td>{counter_credit_offer.credit_offer.credit_type}</td></tr>"
                    f"                <tr><th>Price per Credit</th><td>{counter_credit_offer.offer_price}</td></tr>"
                    f"                <tr><th>Total Price (Including GST and Fee)</th><td>{total_price}</td></tr>"
                    f"                <tr><th>Product Type</th><td>{counter_credit_offer.credit_offer.product_type}</td></tr>"
                    f"                <tr><th>Producer Type</th><td>{counter_credit_offer.producer_epr.producer_type}</td></tr>"
                    f"                <tr><th>Quantity</th><td>{counter_credit_offer.quantity}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <table>"
                    f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                    f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <h3>📁 Trail Documents</h3>"
                    f"            <ul>"
                    f"                   {''.join([f'<li>✅ {doc}</li>' for doc in counter_credit_offer.credit_offer.trail_documents if doc.strip()])}"
                    f"            </ul>"
                    f"        </div>"
                    f"        <div class='status'>Status: {counter_credit_offer.status}</div>"
                    f"        <div class='cta'>"
                    f"            <a href='#'>Review Transaction Details</a>"
                    f"        </div>"
                    f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                    f"            This is an automated message. Please do not reply directly to this email."
                    f"        </p>"
                    f"    </div>"
                    f"</body>"
                    f"</html>"
                )
                send_mail(
                    subject=recycler_subject,
                    message="",
                    from_email=transaction_email,
                    recipient_list=[recycler.email],
                    fail_silently=False,
                    html_message=recycler_html_message
                )

            else:
                raise ValidationError({"error": "Only producers can create counter credit offers."})

        except Exception as e:
            raise ValidationError({"error": e.detail if hasattr(e, 'detail') else str(e)})

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # Check if user is either the producer or recycler associated with the record
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to delete this record."
                }, status=status.HTTP_403_FORBIDDEN)

            self.perform_destroy(instance)
            return Response({
                "status": True,
                "message": "Counter credit offer deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)


# PUBLIC VIEW FOR LISTING CREDIT OFFERS
@method_decorator(cache_page(60 * 15), name='dispatch')
class PublicCreditOfferListView(generics.ListAPIView):
    queryset = CreditOffer.objects.filter(is_sold=False).select_related('epr_account', 'epr_credit')
    serializer_class = CreditOfferSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Bypass authentication
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CreditOfferFilter
    ordering_fields = [
        'price_per_credit',  
        'FY',
        'credit_available',
        'waste_type',
        'epr_credit__credit_type',
        'created_at'
    ]
    ordering = ['-created_at','price_per_credit']  

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# New Detail View
class PublicCreditOfferDetailView(generics.RetrieveAPIView):
    queryset = CreditOffer.objects.filter(is_sold=False).select_related('epr_account', 'epr_credit')
    serializer_class = CreditOfferSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Bypass authentication


    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

# CREATED BY PRODUCER ONLY | UPDATED BY RECYCLER
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]

    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    search_fields = ['status','credit_quantity','order_id','waste_type','product_type','credit_type','producer_type','recycler_type','work_order_date']
    ordering_fields = ['created_at']  
    ordering = ['-created_at']  
    
    def get_permissions(self):
        try:
        #     if self.action == 'create':
        #         permission_classes = [permissions.IsAuthenticated, IsProducer]
        #     elif self.action in ['update', 'partial_update']:
        #         permission_classes = [permissions.IsAuthenticated, IsRecycler]
        #     else:  # list, retrieve
        #         permission_classes = [permissions.IsAuthenticated]
        #     return [permission() for permission in permission_classes]
        # except Exception as e:
        #     raise ValidationError({"error": f"Permission error: {str(e)}"})
            if self.action == 'create':
                permission_classes = [permissions.IsAuthenticated, IsProducer]
            elif self.action in ['update', 'partial_update']:
                permission_classes = [permissions.IsAuthenticated]  # Specific roles checked in serializer
            else:  # list, retrieve
                permission_classes = [permissions.IsAuthenticated]
            return [permission() for permission in permission_classes]
        except Exception as e:
            raise ValidationError({"error": f"Permission error: {str(e)}"})

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, Recycler):
            return Transaction.objects.filter(recycler=user)
        elif isinstance(user, Producer):
            return Transaction.objects.filter(producer=user)
        return Transaction.objects.none()
 
        # GET - List
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    def create(self, request, *args, **kwargs):
        try:
            # credit_offer_id = request.query_params.get('credit_offer_id')
            purchases_request_id = request.query_params.get('purchases_request_id')
            counter_credit_offer_id = request.query_params.get('counter_credit_offer_id')

            # Validate query parameters
            if not purchases_request_id and not counter_credit_offer_id:
                return Response({
                    "status": False,
                    "error": "Provide either purchases_request_id or counter_credit_offer_id"
                }, status=status.HTTP_400_BAD_REQUEST)
    
            if purchases_request_id and counter_credit_offer_id:
                return Response({
                    "status": False,
                    "error": "Provide only one of purchases_request_id or counter_credit_offer_id"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prepare data 
            data = request.data.copy()
            data['producer'] = request.user.id

            data.pop('is_complete', None)
            data.pop('transaction_proof', None)
            data.pop('status', None)
            data.pop('is_approved', None)
            data.pop('producer_transfer_proof', None)
            data.pop('trail_documents', None)
            data.pop('recycler_transfer_proof', None)

            producer_epr = None
            counter_credit_offer = None
            purchases_request = None


            if counter_credit_offer_id:
                # Fetch producer_epr from CounterCreditOffer
                try:
                    counter_credit_offer = CounterCreditOffer.objects.get(id=counter_credit_offer_id)
                    if counter_credit_offer.status != 'approved':
                        return Response({
                            "status": False,
                            "error": "Counter credit offer must be approved"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    producer_epr = counter_credit_offer.producer_epr
                    if not producer_epr:
                        return Response({
                            "status": False,
                            "error": "Counter credit offer does not have an associated producer EPR account"
                        }, status=status.HTTP_400_BAD_REQUEST)
                except CounterCreditOffer.DoesNotExist:
                    return Response({
                        "status": False,
                        "error": "Counter credit offer not found"
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
              # Fetch producer_epr and credit_offer from PurchasesRequest
                try:
                    purchases_request = PurchasesRequest.objects.get(id=purchases_request_id)
                    if purchases_request.status != 'approved':
                        return Response({
                            "status": False,
                            "error": "Purchase request must be approved"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    producer_epr = purchases_request.producer_epr
                    if not producer_epr:
                        return Response({
                            "status": False,
                            "error": "Purchase request does not have an associated producer EPR account"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    if not purchases_request.credit_offer:
                        return Response({
                            "status": False,
                            "error": "Purchase request does not have an associated credit offer"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    # Verify the producer matches the requesting user
                    if purchases_request.producer != request.user:
                        return Response({
                            "status": False,
                            "error": "You are not authorized to use this purchase request as producer of purchase request does not match your identity"
                        }, status=status.HTTP_403_FORBIDDEN)
                except PurchasesRequest.DoesNotExist:
                    return Response({
                        "status": False,
                        "error": "Purchase request not found"
                    }, status=status.HTTP_404_NOT_FOUND)

            fee = 0
            fees = TransactionFee.objects.first()
            if fees:
                fee = fees.transaction_fee

            # Populate data from purchase request
            if purchases_request_id:
                try:

                    if purchases_request.is_complete:
                         return Response({
                            "status": False,
                            "error": "Transaction has been already created for the purchase request"
                        }, status=status.HTTP_400_BAD_REQUEST)

                    credit_offer = purchases_request.credit_offer
                    if not credit_offer:  # Handle case where credit_offer is None
                        return Response({
                            "status": False,
                            "error": "Purchase request does not have an associated credit offer"
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # calculate total price
                    price_per_credit =  credit_offer.price_per_credit 
                    quantity = purchases_request.quantity
                    value = price_per_credit*quantity
                    processing_fee = value*0.05
                    gst = (value+processing_fee)*0.18
                    total_price = value + processing_fee + gst

                    data['counter_credit_offer'] = None
                    data['credit_offer'] = credit_offer.id
                    data['recycler'] = credit_offer.recycler.id
                    data['credit_quantity'] = purchases_request.quantity
                    data['waste_type'] = credit_offer.waste_type
                    data['recycler_type'] = credit_offer.epr_account.recycler_type
                    data['total_price'] = total_price
                    data['price_per_credit'] = credit_offer.price_per_credit
                    data['credit_type'] = credit_offer.epr_credit.credit_type
                    data['product_type'] = credit_offer.epr_credit.product_type
                    data['producer_type'] = request.user.epr_accounts.first().producer_type
                    data['offered_by'] = credit_offer.recycler.unique_id

                except Exception as e:
                    return Response({
                        "status": False,
                        "error": f"Error processing purchase request: {str(e)}"
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Populate data from CounterCreditOffer
            else:
                try:
                    # counter_credit_offer = CounterCreditOffer.objects.get(id=counter_credit_offer_id)
                    if counter_credit_offer.is_complete:
                         return Response({
                            "status": False,
                            "error": "Transaction has been already created for the counter credit offer request"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    if counter_credit_offer.status != 'approved':
                        return Response({
                            "status": False,
                            "error": "Counter credit offer must be approved"
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # calculate total price
                    price_per_credit =  counter_credit_offer.offer_price 
                    quantity = counter_credit_offer.quantity  
                    value = price_per_credit*quantity
                    processing_fee = value*0.05
                    gst = (value+processing_fee)*0.18
                    total_price = value + processing_fee + gst
                    
                    data['counter_credit_offer'] = counter_credit_offer.id
                    data['credit_offer'] = counter_credit_offer.credit_offer.id
                    data['recycler'] = counter_credit_offer.recycler.id
                    data['credit_quantity'] = counter_credit_offer.quantity  
                    data['waste_type'] = counter_credit_offer.credit_offer.waste_type
                    data['recycler_type'] = counter_credit_offer.credit_offer.epr_account.recycler_type
                    data['total_price'] = total_price
                    data['price_per_credit'] = counter_credit_offer.offer_price
                    data['credit_type'] = counter_credit_offer.credit_offer.epr_credit.credit_type
                    data['product_type'] = counter_credit_offer.credit_offer.epr_credit.product_type
                    data['producer_type'] = request.user.epr_accounts.first().producer_type
                    data['offered_by'] = request.user.unique_id
                except CounterCreditOffer.DoesNotExist:
                    return Response({
                        "status": False,
                        "error": "Counter credit offer not found"
                    }, status=status.HTTP_404_NOT_FOUND)
            
             # Fetch EPRTarget for validation
            

            # CHECK IF WASTE TYPE OF GIVEN EPR ID OF PRODUCER MATCHES THE WASTE TYPE OF THE CREDIT OR COUNTER CREDIT OFFER
            if producer_epr.waste_type != data['waste_type']:
                 return Response({
                    "status": False,
                    "error": f"Your EPR Account's Waste Type does not matches the the waste type of the credit offer you want to buy. Epr's waste type:{producer_epr.waste_type}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # CHECK IF THE TRANSACTION CREDIT QUANTITY DOES NOT EXCEED THE REMAINING TARGET QUANTITY
            epr_target = EPRTarget.objects.filter(
                epr_account=producer_epr,
                waste_type=producer_epr.waste_type,
                product_type=data.get('product_type'),
                credit_type=data.get('credit_type'),
                is_achieved=False
                ).annotate(
                remaining_quantity=F('target_quantity') - F('achieved_quantity') - F('blocked_target')
                ).filter(
                    remaining_quantity__gte=data.get('credit_quantity')
                ).first()

            if not epr_target:
                return Response({
                    "status": False,
                    "error":  f"No matching EPR Target found. Please create an EPR target for the given EPR account where credit type should be {data.get('credit_type')}, product type should be {data.get('product_type')} and waste type {data['waste_type']} and remaining Target quantity is higher than {data.get('credit_quantity')}"
                }, status=status.HTTP_400_BAD_REQUEST)

            epr_target.blocked_target += float(data['credit_quantity'])
            epr_target.save()
            # Validate credit_quantity against EPRTarget
            # remaining_quantity = epr_target.target_quantity - epr_target.achieved_quantity
            # if float(data['credit_quantity']) > remaining_quantity:
            #     return Response({
            #         "status": False,
            #         "error": f"Credit quantity ({data['credit_quantity']}) cannot exceed remaining target quantity ({remaining_quantity})"
            #     }, status=status.HTTP_400_BAD_REQUEST)
            
            
            # Add producer_epr to data
            data['producer_epr'] = producer_epr.id
            # Validate available credits (credit_available - blocked_amount)
            credit_offer = purchases_request.credit_offer if purchases_request else counter_credit_offer.credit_offer
                # Lock the credit_offer row to prevent race conditions
            credit_offer = CreditOffer.objects.get(id=credit_offer.id)
            available_after_blocked = credit_offer.credit_available - credit_offer.blocked_credit
            if available_after_blocked < float(data['credit_quantity']):
                    return Response({
                        "status": False,
                        "error": f"Not enough unblocked credits available. Available: {available_after_blocked}, Requested: {data['credit_quantity']}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Block the credit amount
            credit_offer.blocked_credit += float(data['credit_quantity'])
            credit_offer.save()

            # Serialize and save the data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            transaction = serializer.save()

             # Update is_complete if counter_credit_offer_id was provided
            if counter_credit_offer:
                counter_credit_offer.is_complete = True
                counter_credit_offer.save()

             # Update is_complete if purchase_request_id  was provided
            if purchases_request:
                purchases_request.is_complete = True
                purchases_request.save()
   
            # # Fetch producer and recycler details
            # producer = Producer.objects.get(id=request.user.id)
            # recycler = Recycler.objects.get(id=data['recycler'])


            # # comman field
            # email ='support@circle8.in'
            # contact_number = '+91 9620220013'

            # # Email to Recycler (HTML)
            # recycler_subject = "New Transaction Created"
            # recycler_html_message = (
            #     f"<!DOCTYPE html>"
            #     f"<html>"
            #     f"<body style='font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;'>"
            #     f"<div style='max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
            #     f"<h2 style='color: #2c3e50; text-align: center;'>New Transaction Notification</h2>"
            #     f"<p style='color: #34495e;'>Dear <strong>{recycler.full_name}</strong>,</p>"
            #     f"<p style='color: #34495e;'>A new transaction has been created by <strong>{producer.full_name}</strong>. Below are the details:</p>"
              
            #     f"<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>"

            #     f"<tr><td style='padding: 10px;'><strong>Request By: </strong></td><td style='padding: 10px;'>{transaction.producer.unique_id}</td></tr>"
              
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Work Order ID</strong></td><td style='padding: 10px;'>{transaction.order_id}</td></tr>"
              
            #     f"<tr><td style='padding: 10px;'><strong>Work Order Date</strong></td><td style='padding: 10px;'>{transaction.work_order_date}</td></tr>"
                
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Waste Type</strong></td><td style='padding: 10px;'>{transaction.waste_type}</td></tr>"

            #     f"<tr><td style='padding: 10px;'><strong>Credit Type</strong></td><td style='padding: 10px;'>{transaction.credit_type}</td></tr>"
              
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Price per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"
              
            #     f"<tr><td style='padding: 10px;'><strong>Product Type</strong></td><td style='padding: 10px;'>{transaction.product_type}</td></tr>"
              
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Producer Type</strong></td><td style='padding: 10px;'>{transaction.producer_type}</td></tr>"

            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Total Price</strong></td><td style='padding: 10px;'>{transaction.total_price}</td></tr>"
              
              
            #     f"<tr><td style='padding: 10px;'><strong>Credit Quantity</strong></td><td style='padding: 10px;'>{transaction.credit_quantity}</td></tr>"

              
            #     f"<tr><td style='padding: 10px;'><strong>Price Per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"

                              
            #     f"<tr><td style='padding: 10px;'><strong>Trail Documents</strong></td><td style='padding: 10px;'>{transaction.credit_offer.trail_documents}</td></tr>"


            #     f"<tr><td style='padding: 10px;'><strong>Status</strong></td><td style='padding: 10px;'>{transaction.status}</td></tr>"
              
            #     f"</table>"

            #     f"<h3 style='color: #2980b9;'>Producer Details</h3>"
            #     f"<strong>EPR Registration No:</strong> {transaction.producer_epr.epr_registration_number} <br>"
            #     f"<strong>EPR Registered Name:</strong> {transaction.producer_epr.epr_registered_name}<br>"
            #     f"<strong>Email:</strong> {email}<br>"
            #     f"<strong>Contact Number:</strong> {contact_number}<br>"
            #     f"<p style='color: #34495e; text-align: center;'>Please review and update the transaction status as needed.</p>"
            #     f"<div style='text-align: center; margin-top: 20px;'>"
            #     f"</div>"
            #     f"<p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>This is an automated message. Please do not reply directly to this email.</p>"
            #     f"</div>"
            #     f"</body>"
            #     f"</html>"
            # )
            # send_mail(
            #     subject=recycler_subject,
            #     message="",
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[recycler.email],
            #     fail_silently=False,
            #     html_message=recycler_html_message
            # )

            # # Email to Producer (Stylish HTML)
            # producer_subject = "Transaction Request Sent to Recycler"
            # producer_html_message = (
            #     f"<!DOCTYPE html>"
            #     f"<html>"
            #     f"<body style='font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;'>"
            #     f"<div style='max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
            #     f"<h2 style='color: #2c3e50; text-align: center;'>Transaction Request Confirmation</h2>"
            #     f"<p style='color: #34495e;'>Dear <strong>{producer.full_name}</strong>,</p>"
            #     f"<p style='color: #34495e;'>Your transaction request has been successfully sent to <strong>{recycler.full_name}</strong>. Below are the details:</p>"
            #     f"<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>"

            #     f"<tr><td style='padding: 10px;'><strong>Offered By: </strong></td><td style='padding: 10px;'>{transaction.recycler.unique_id}</td></tr>"
              
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Work Order ID</strong></td><td style='padding: 10px;'>{transaction.order_id}</td></tr>"
              
            #     f"<tr><td style='padding: 10px;'><strong>Work Order Date</strong></td><td style='padding: 10px;'>{transaction.work_order_date}</td></tr>"
                
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Waste Type</strong></td><td style='padding: 10px;'>{transaction.waste_type}</td></tr>"

            #     f"<tr><td style='padding: 10px;'><strong>Credit Type</strong></td><td style='padding: 10px;'>{transaction.credit_type}</td></tr>"
              
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Price per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"
              
            #     f"<tr><td style='padding: 10px;'><strong>Product Type</strong></td><td style='padding: 10px;'>{transaction.product_type}</td></tr>"
              
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Producer Type</strong></td><td style='padding: 10px;'>{transaction.producer_type}</td></tr>"
              
            #     f"<tr><td style='padding: 10px;'><strong>Credit Quantity</strong></td><td style='padding: 10px;'>{transaction.credit_quantity}</td></tr>"

              
            #     f"<tr><td style='padding: 10px;'><strong>Price Per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"
            #     f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Total Price</strong></td><td style='padding: 10px;'>{transaction.total_price}</td></tr>"

            #     f"<tr><td style='padding: 10px;'><strong>Recycler Type</strong></td><td style='padding: 10px;'>{transaction.recycler_type}</td></tr>"


            #     f"<tr><td style='padding: 10px;'><strong>Trail Documents</strong></td><td style='padding: 10px;'>{transaction.credit_offer.trail_documents}</td></tr>"

            #     f"<tr><td style='padding: 10px;'><strong>Status</strong></td><td style='padding: 10px;'>{transaction.status}</td></tr>"
              
            #     f"</table>"

            #     f"<h3 style='color: #2980b9;'>Recycler Details</h3>"
            #     f"<strong>EPR Registration No:</strong> {transaction.credit_offer.epr_account.epr_registration_number} <br>"
            #     f"<strong>EPR Registered Name:</strong> {transaction.credit_offer.epr_account.epr_registered_name}<br>"
            #     f"<strong>Email:</strong> {email}<br>"
            #     f"<strong>Contact Number:</strong> {contact_number}<br>"
            #     f"<p style='color: #34495e; text-align: center;'>Please review and update the transaction status as needed.</p>"
            #     f"<div style='text-align: center; margin-top: 20px;'>"
            #     f"</div>"
            #     f"<p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>This is an automated message. Please do not reply directly to this email.</p>"
            #     f"</div>"
            #     f"</body>"
            #     f"</html>"
            # )
            # send_mail(
            #     subject=producer_subject,
            #     message="",  
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[producer.email],
            #     fail_silently=False,
            #     html_message=producer_html_message
            # )
           
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            transaction = serializer.save()
   
            
            return Response({"data":serializer.data,"status":True})
        
        except serializers.ValidationError as e:
            error_message = e.detail if hasattr(e, 'detail') else str(e)
    
            # Handle case where error_message is a dict
            if isinstance(error_message, dict):
                # Check if 'error' key exists before accessing it
                if 'error' in error_message:
                    error_list = error_message['error']
                    if isinstance(error_list, list) and len(error_list) > 0:
                        first_error = error_list[0]
                        error_message = str(first_error)
                else:
                    # Handle other possible error keys (like 'producer_epr' in your case)
                    for key, value in error_message.items():
                        if isinstance(value, list) and len(value) > 0:
                            first_error = value[0]
                            error_message = str(first_error)
                            break
                    else:
                        # Fallback if no list found in dict
                        error_message = str(error_message)
            
            # Handle case where error_message is a list
            elif isinstance(error_message, list) and len(error_message) > 0:
                error_message = str(error_message[0])
            
            # Default case
            else:
                error_message = str(error_message)
            return Response({
                "status": False,
                "error": error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
     # Block DELETE method
 
    def destroy(self, request, *args, **kwargs):
        return Response({
            "status": False,
            "error": "Deletion of transactions is not allowed."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    


# PURCHASE REQUEST
class PurchasesRequestViewSet(viewsets.ModelViewSet):
    queryset = PurchasesRequest.objects.all()
    serializer_class = PurchasesRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]

         # Fields that can be used for ordering
    filter_backends = [DjangoFilterBackend, CaseInsensitiveSearchFilter, OrderingFilter]
    search_fields = ['FY','status','credit_offer__waste_type','credit_offer__product_type','credit_offer__credit_type']
    ordering_fields = ['created_at']  # Adjust this to match your model's field name
    ordering = ['-created_at']  # '-' indicates descending order

    def get_permissions(self):
        try:
            if self.action == 'create':
                permission_classes = [permissions.IsAuthenticated, IsProducer]
            elif self.action in ['update', 'partial_update']:
                permission_classes = [permissions.IsAuthenticated, IsRecycler]
            else:  # list, retrieve
                permission_classes = [permissions.IsAuthenticated]
            return [permission() for permission in permission_classes]
        except Exception as e:
            raise ValidationError({"error": f"Permission error: {str(e)}"})

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, Recycler):
            return PurchasesRequest.objects.filter(recycler=user).exclude(status="rejected")
        elif isinstance(user, Producer):
            return PurchasesRequest.objects.filter(producer=user)
        return PurchasesRequest.objects.none()
    

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())  
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)


    def get_serializer(self, *args, **kwargs):
        if self.request.method == "POST":
            # Fetch credit_offer_id from query params
            credit_offer_id = self.request.query_params.get('credit_offer_id')
            if not credit_offer_id:
                raise ValidationError({"error": "credit_offer_id is required in query parameters"})

            # Get the CreditOffer
            try:
                credit_offer = CreditOffer.objects.get(id=credit_offer_id)
            except CreditOffer.DoesNotExist:
                raise ValidationError({"error": "Invalid credit_offer_id"})

            # Prepare request data by copying the original data
            request_data = self.request.data.copy() if hasattr(self.request.data, 'copy') else dict(self.request.data)
            
            # Validate producer_epr from request body
            producer_epr_id = request_data.get('producer_epr')
            quantity = request_data.get('quantity')



            # if credit_offer.minimum_purchase < credit_offer.credit_available:
            if int(quantity) < int(credit_offer.minimum_purchase):
                    raise ValidationError("quantity should be greater than or equal to minimum purchase")
            elif int(quantity) > int(credit_offer.credit_available - credit_offer.blocked_credit):
                    raise ValidationError( f"Not enough unblocked credits available. Available: {credit_offer.credit_available - credit_offer.blocked_credit}, Requested: {quantity}")

            if not producer_epr_id:
                raise ValidationError({"error": "producer_epr is required in the request body"})
            try:
                producer_epr = ProducerEPR.objects.get(id=producer_epr_id)
                if producer_epr.producer != self.request.user:
                    raise ValidationError("producer_epr must belong to the requesting Producer")
                if producer_epr.waste_type != credit_offer.waste_type:
                    raise ValidationError("Given epr account's waste type does not match the credit offer's waste type")
            except ProducerEPR.DoesNotExist:
                raise ValidationError({"error": "Invalid producer_epr ID"})
            
            # TODO => TARGET QUANTITY CHECK (SHOULD BE GREATER OR EQUAL TO QUANTITY OF THE REQUEST BODY)

            epr_target = EPRTarget.objects.filter(
                    epr_account=producer_epr,
                    waste_type=credit_offer.waste_type,
                    product_type=credit_offer.product_type,
                    credit_type=credit_offer.credit_type,
                    is_achieved=False
                ).annotate(
                        remaining_quantity=F('target_quantity') - F('achieved_quantity') - F('blocked_target')
                ).filter(
                    remaining_quantity__gte=quantity
                ).first()



            if not epr_target:
                    raise ValidationError(
                         f"No matching EPR Target found. Please create an EPR target for the given EPR account where credit type should be {credit_offer.credit_type} and product type should be {credit_offer.product_type} and  remaining Target quantity is higher than {quantity}"
                    )



            # Add recycler, producer, and credit_offer to the data as UUID strings
            request_data.update({
                "recycler": str(credit_offer.recycler.id),
                "producer": str(self.request.user.id),
                "credit_offer": str(credit_offer.id),
                # Keep producer_epr as the UUID string from the request body
            })

            kwargs["data"] = request_data
            kwargs["context"] = {'request': self.request}  # Ensure context is passed

        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            purchase_request = serializer.save()
            producer = purchase_request.producer
            recycler = purchase_request.recycler

            fee = 0
            fees = TransactionFee.objects.first()
            if fees:
                    fee = fees.transaction_fee

            total_price = (purchase_request.credit_offer.price_per_credit*purchase_request.quantity) +  (purchase_request.credit_offer.price_per_credit*purchase_request.quantity)*0.18 + fee
            trail_documents_html = "".join([f"<li>✅ {doc}</li>" for doc in purchase_request.credit_offer.trail_documents])

                # Common fields
            email = 'support@circle8.in'
            contact_number = '+91 9620220013'

                # EMAIL TO RECYCLER
            recycler_subject = "Purchase Request"
            recycler_html_message = (
                    f"<!DOCTYPE html>"
                    f"<html>"
                    f"<head>"
                    f"    <meta charset='UTF-8'>"
                    f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                    f"    <title>Purchase Request Notification</title>"
                    f"    <style>"
                    f"        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}"
                    f"        .container {{ max-width: 600px; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}"
                    f"        h2 {{ color: #2c3e50; text-align: center; }}"
                    f"        .details {{ margin: 20px 0; }}"
                    f"        .details table {{ width: 100%; border-collapse: collapse; }}"
                    f"        .details th, .details td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}"
                    f"        .details th {{ background-color: #3498db; color: white; }}"
                    f"        .status {{ text-align: center; padding: 10px; font-weight: bold; background-color: #27ae60; color: white; border-radius: 4px; }}"
                    f"        .cta {{ text-align: center; margin-top: 20px; }}"
                    f"        .cta a {{ text-decoration: none; background: #27ae60; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }}"
                    f"    </style>"
                    f"</head>"
                    f"<body>"
                    f"    <div class='container'>"
                    f"        <h2>📢 Purchase Request Notification</h2>"
                    f"        <p>Dear <strong>{recycler.full_name}</strong>,</p>"
                    f"        <p>You have a purchase request from <strong>{producer.full_name}</strong>. Below are the details:</p>"
                    f"        <div class='details'>"
                    f"            <h3>🛠 Purchase Request Details</h3>"
                    f"            <table>"
                    f"                <tr><th>Requested By</th><td>{producer.unique_id}</td></tr>"
                    f"                <tr><th>Work Order Date</th><td>{purchase_request.created_at}</td></tr>"
                    f"                <tr><th>Credit Offer Title</th><td>{purchase_request.credit_offer.offer_title}</td></tr>"
                    f"                <tr><th>Waste Type</th><td>{purchase_request.credit_offer.waste_type}</td></tr>"
                    f"                <tr><th>Credit Type</th><td>{purchase_request.credit_offer.credit_type}</td></tr>"
                    f"                <tr><th>Price per Credit</th><td>{purchase_request.credit_offer.price_per_credit}</td></tr>"
                    f"                <tr><th>Total Price (Including GST)</th><td>{total_price}</td></tr>"
                    f"                <tr><th>Product Type</th><td>{purchase_request.credit_offer.product_type}</td></tr>"
                    f"                <tr><th>Quantity</th><td>{purchase_request.quantity}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <table>"
                    f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                    f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <h3>📁 Trail Documents</h3>"
                    f"            <ul>{trail_documents_html}</ul>"
                    f"        </div>"
                    f"        <div class='status'>Status: {purchase_request.status}</div>"
                    f"        <div class='cta'>"
                    f"            <a href='#'>Review Transaction Details</a>"
                    f"        </div>"
                    f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                    f"            This is an automated message. Please do not reply directly to this email."
                    f"        </p>"
                    f"    </div>"
                    f"</body>"
                    f"</html>"
                )
            send_mail(
                    subject=recycler_subject,
                    message="",
                    from_email=transaction_email,
                    recipient_list=[recycler.email],
                    fail_silently=False,
                    html_message=recycler_html_message
                )

            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
              # error_message = "An unexpected error occurred"
            # error_message = e.detail if hasattr(e, 'detail') else str(e)
            # if isinstance(error_message,dict):
            #     if error_message['error']:
            #         error_message = error_message['error']
    
            # # Since e.detail is a dict, access the 'error' key
            # if isinstance(e.detail, dict) and 'error' in e.detail:
            #     error_list = e.detail['error']  # Get the list under 'error' key
            #     if isinstance(error_list, list) and len(error_list) > 0:
            #         # Access the first ErrorDetail object
            #         first_error = error_list[0]
            #         # Extract the string from the ErrorDetail
            #         error_message = first_error.string if hasattr(first_error, 'string') else str(first_error)
            
            error_message = e.detail if hasattr(e, 'detail') else str(e)
    
            # Handle case where error_message is a dict
            if isinstance(error_message, dict):
                # Check if 'error' key exists before accessing it
                if 'error' in error_message:
                    error_list = error_message['error']
                    if isinstance(error_list, list) and len(error_list) > 0:
                        first_error = error_list[0]
                        error_message = str(first_error)
                else:
                    # Handle other possible error keys (like 'producer_epr' in your case)
                    for key, value in error_message.items():
                        if isinstance(value, list) and len(value) > 0:
                            first_error = value[0]
                            error_message = str(first_error)
                            break
                    else:
                        # Fallback if no list found in dict
                        error_message = str(error_message)
            
            # Handle case where error_message is a list
            elif isinstance(error_message, list) and len(error_message) > 0:
                error_message = str(error_message[0])
            
            # Default case
            else:
                error_message = str(error_message)
            
            if isinstance(error_message,list):
                error_message = error_message[0]
            return Response({
                "status": False,
                "error": error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if isinstance(request.user, Recycler) and instance.recycler != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to update this PurchasesRequest"
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            # TODO => CHECK THAT QUANITY SHOULD NOT EXCEED THE CREDIT AVAILABLE OF THE CREDIT OFFER
            purchase_request = serializer.save()
    


            producer = purchase_request.producer
            recycler = purchase_request.recycler

            fee = 0
            fees = TransactionFee.objects.first()
            if fees:
                fee = fees.transaction_fee
                
            # Common fields
            email = 'support@circle8.in'
            contact_number = '+91 9620220013'

            trail_documents_html = "".join([f"<li>✅ {doc}</li>" for doc in purchase_request.credit_offer.trail_documents])
            # Send email to Producer if Purchase Request is approved
            if purchase_request.status == 'approved' and purchase_request.is_approved:


                # Email to Producer (Stylish HTML)
                producer_subject = "Purchase Request Approved"
                total_price = (purchase_request.credit_offer.price_per_credit*purchase_request.quantity) +  (purchase_request.credit_offer.price_per_credit*purchase_request.quantity)*0.18 + fee
                producer_html_message = (
    

                f"<!DOCTYPE html>"
                f"<html>"
                f"<head>"
                f"    <meta charset='UTF-8'>"
                f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                f"    <title>Purchase Request Approval Notification</title>"
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
                f"        <h2>📢 Purchase Request Approval Notification</h2>"
                f"        <p>Dear <strong>{producer.full_name}</strong>,</p>"
                f"        <p>Your purchase request has been approved by <strong>{recycler.full_name}</strong>. Below are the details:</p>"
                f"        "
                f"        <div class='details'>"
                f"            <h3>🛠 Purchase Request Details</h3>"
                f"            <table>"
                f"                <tr><th>Offered By</th><td>{recycler.unique_id}</td></tr>"
                f"                <tr><th>Work Order Date</th><td>{purchase_request.created_at}</td></tr>"
                f"                <tr><th>Credit Offer Title</th><td>{purchase_request.credit_offer.offer_title}</td></tr>"
                f"                <tr><th>Waste Type</th><td>{purchase_request.credit_offer.waste_type}</td></tr>"
                f"                <tr><th>Credit Type</th><td>{purchase_request.credit_offer.credit_type}</td></tr>"
                f"                <tr><th>Price per Credit</th><td>{purchase_request.credit_offer.price_per_credit}</td></tr>"
                f"                <tr><th>Total Price (Including GST)</th><td>{total_price}</td></tr>"
                f"                <tr><th>Product Type</th><td>{purchase_request.credit_offer.product_type}</td></tr>"
                f"                <tr><th>Quantity</th><td>{purchase_request.quantity}</td></tr>"
                f"            </table>"
                f"        </div>"
                f"        <div class='details'>"
                f"            <table>"
                f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                f"            </table>"
                f"        </div>"
                f"        <div class='details'>"
                f"            <h3>📁 Trail Documents</h3>"
                f"            <ul>"
                f"                {trail_documents_html}"
                f"            </ul>"
                f"        </div>"
                f"        "
                f"        <div class='status'>Status: {purchase_request.status}</div>"
                f"        "
                f"        <div class='cta'>"
                f"            <a href='#'>Proceed with Transaction</a>"
                f"        </div>"
                f"        "
                f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                f"            This is an automated message. Please do not reply directly to this email."
                f"        </p>"
                f"    </div>"
                f"</body>"
                f"</html>"
                )
                send_mail(
                    subject=producer_subject,
                    message="",
                    from_email=transaction_email,
                    recipient_list=[producer.email],
                    fail_silently=False,
                    html_message=producer_html_message
                )

                # # EMAIL TO RECYCLER
                # recycler_subject = "Purchase Request Approved"
                # recycler_html_message = (
                #     f"<!DOCTYPE html>"
                #     f"<html>"
                #     f"<head>"
                #     f"    <meta charset='UTF-8'>"
                #     f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                #     f"    <title>Purchase Request Approval Notification</title>"
                #     f"    <style>"
                #     f"        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}"
                #     f"        .container {{ max-width: 600px; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}"
                #     f"        h2 {{ color: #2c3e50; text-align: center; }}"
                #     f"        .details {{ margin: 20px 0; }}"
                #     f"        .details table {{ width: 100%; border-collapse: collapse; }}"
                #     f"        .details th, .details td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}"
                #     f"        .details th {{ background-color: #3498db; color: white; }}"
                #     f"        .status {{ text-align: center; padding: 10px; font-weight: bold; background-color: #27ae60; color: white; border-radius: 4px; }}"
                #     f"        .cta {{ text-align: center; margin-top: 20px; }}"
                #     f"        .cta a {{ text-decoration: none; background: #27ae60; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }}"
                #     f"    </style>"
                #     f"</head>"
                #     f"<body>"
                #     f"    <div class='container'>"
                #     f"        <h2>📢 Purchase Request Approval Notification</h2>"
                #     f"        <p>Dear <strong>{recycler.full_name}</strong>,</p>"
                #     f"        <p>You have approved a purchase request from <strong>{producer.full_name}</strong>. Below are the details:</p>"
                #     f"        <div class='details'>"
                #     f"            <h3>🛠 Purchase Request Details</h3>"
                #     f"            <table>"
                #     f"                <tr><th>Requested By</th><td>{producer.unique_id}</td></tr>"
                #     f"                <tr><th>Work Order Date</th><td>{purchase_request.created_at}</td></tr>"
                #     f"                <tr><th>Credit Offer Title</th><td>{purchase_request.credit_offer.offer_title}</td></tr>"
                #     f"                <tr><th>Waste Type</th><td>{purchase_request.credit_offer.waste_type}</td></tr>"
                #     f"                <tr><th>Credit Type</th><td>{purchase_request.credit_offer.credit_type}</td></tr>"
                #     f"                <tr><th>Price per Credit</th><td>{purchase_request.credit_offer.price_per_credit}</td></tr>"
                #     f"                <tr><th>Total Price (Including GST)</th><td>{total_price}</td></tr>"
                #     f"                <tr><th>Product Type</th><td>{purchase_request.credit_offer.product_type}</td></tr>"
                #     f"                <tr><th>Quantity</th><td>{purchase_request.quantity}</td></tr>"
                #     f"            </table>"
                #     f"        </div>"
                #     f"        <div class='details'>"
                #     f"            <h3>🏭 Producer Details</h3>"
                #     f"            <table>"
                #     f"                <tr><th>EPR Registration Number</th><td>{purchase_request.producer_epr.epr_registration_number}</td></tr>"
                #     f"                <tr><th>EPR Registered Name</th><td>{purchase_request.producer_epr.epr_registered_name}</td></tr>"
                #     f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                #     f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                #     f"            </table>"
                #     f"        </div>"
                #     f"        <div class='details'>"
                #     f"            <h3>📁 Trail Documents</h3>"
                #     f"            <ul>{trail_documents_html}</ul>"
                #     f"        </div>"
                #     f"        <div class='status'>Status: {purchase_request.status}</div>"
                #     f"        <div class='cta'>"
                #     f"            <a href='#'>Review Transaction Details</a>"
                #     f"        </div>"
                #     f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                #     f"            This is an automated message. Please do not reply directly to this email."
                #     f"        </p>"
                #     f"    </div>"
                #     f"</body>"
                #     f"</html>"
                # )
                # send_mail(
                #     subject=recycler_subject,
                #     message="",
                #     from_email=settings.DEFAULT_FROM_EMAIL,
                #     recipient_list=[recycler.email],
                #     fail_silently=False,
                #     html_message=recycler_html_message
                # )

            if purchase_request.status == 'rejected':
                producer_subject = "Purchase Request Rejected"
                total_price = (purchase_request.credit_offer.price_per_credit*purchase_request.quantity) +  (purchase_request.credit_offer.price_per_credit*purchase_request.quantity)*0.18 + fee
                producer_html_message = (
    
                    f"<!DOCTYPE html>"
                    f"<html>"
                    f"<head>"
                    f"    <meta charset='UTF-8'>"
                    f"    <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                    f"    <title>Purchase Request Approval Notification</title>"
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
                    f"        <h2>📢 Purchase Request Rejection Notification</h2>"
                    f"        <p>Dear <strong>{producer.full_name}</strong>,</p>"
                    f"        <p>Your purchase request has been rejected by <strong>{recycler.full_name}</strong>. Below are the details:</p>"
                    f"        "
                    f"        <div class='details'>"
                    f"            <h3>🛠 Purchase Request Details</h3>"
                    f"            <table>"
                    f"                <tr><th>Offered By</th><td>{recycler.unique_id}</td></tr>"
                    f"                <tr><th>Work Order Date</th><td>{purchase_request.created_at}</td></tr>"
                    f"                <tr><th>Credit Offer Title</th><td>{purchase_request.credit_offer.offer_title}</td></tr>"
                    f"                <tr><th>Waste Type</th><td>{purchase_request.credit_offer.waste_type}</td></tr>"
                    f"                <tr><th>Credit Type</th><td>{purchase_request.credit_offer.credit_type}</td></tr>"
                    f"                <tr><th>Price per Credit</th><td>{purchase_request.credit_offer.price_per_credit}</td></tr>"
                    f"                <tr><th>Total Price (Including GST)</th><td>{total_price}</td></tr>"
                    f"                <tr><th>Product Type</th><td>{purchase_request.credit_offer.product_type}</td></tr>"
                    f"                <tr><th>Quantity</th><td>{purchase_request.quantity}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <table>"
                    f"                <tr><th>Email</th><td><a href='mailto:{email}'>{email}</a></td></tr>"
                    f"                <tr><th>Contact Number</th><td>{contact_number}</td></tr>"
                    f"            </table>"
                    f"        </div>"
                    f"        <div class='details'>"
                    f"            <h3>📁 Trail Documents</h3>"
                    f"            <ul>"
                    f"                {trail_documents_html}"
                    f"            </ul>"
                    f"        </div>"
                    f"        "
                    f"        <div class='status'>Status: {purchase_request.status}</div>"
                    f"        "
                    f"        <div class='cta'>"
                    f"            <a href='#'>Proceed with Transaction</a>"
                    f"        </div>"
                    f"        "
                    f"        <p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>"
                    f"            This is an automated message. Please do not reply directly to this email."
                    f"        </p>"
                    f"    </div>"
                    f"</body>"
                    f"</html>"
                )
                send_mail(
                    subject=producer_subject,
                    message="",
                    from_email=transaction_email,
                    recipient_list=[producer.email],
                    fail_silently=False,
                    html_message=producer_html_message
                )
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.producer != request.user:
                return Response({
                    "status": False,
                    "error": "You are not authorized to delete this record."
                }, status=status.HTTP_403_FORBIDDEN)

            self.perform_destroy(instance)
            return Response({
                "status": True,
                "message": " Purchase request deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND if "DoesNotExist" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class OrderDetailView(APIView):
    """
    A GET-only view to retrieve a record from either CounterCreditOffer or PurchasesRequest
    based on the record_id provided in the path parameters.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, record_id, *args, **kwargs):
        """
        Retrieve a record based on the record_id, checking both CounterCreditOffer and PurchasesRequest.

        :param record_id: The ID of the record to retrieve (UUID)
        """
        try:
            user = request.user
            type = ""
            instance = None
            serializer = None
            instance = CounterCreditOffer.objects.filter(id=record_id).first()
            if instance:
                    serializer = CounterCreditOfferSerializer(instance)
                    type = "counter credit"
            else:
                    # Check PurchasesRequest (Producer also creates these)
                instance = PurchasesRequest.objects.filter(id=record_id).first()
                if instance:
                    serializer = PurchasesRequestSerializer(instance)
                    type = "direct purchase"

            # Determine user type and filter accordingly
            # if isinstance(user, Producer):
            #     # Check CounterCreditOffer first (Producer creates these)
            #     instance = CounterCreditOffer.objects.filter(id=record_id, producer=user).first()
            #     if instance:
            #         serializer = CounterCreditOfferSerializer(instance)
            #     else:
            #         # Check PurchasesRequest (Producer also creates these)
            #         instance = PurchasesRequest.objects.filter(id=record_id, producer=user).first()
            #         if instance:
            #             serializer = PurchasesRequestSerializer(instance)

            # elif isinstance(user, Recycler):
            #     # Check CounterCreditOffer (Recycler updates/approves these)
            #     instance = CounterCreditOffer.objects.filter(id=record_id, recycler=user).first()
            #     if instance:
            #         serializer = CounterCreditOfferSerializer(instance)
            #     else:
            #         # Check PurchasesRequest (Recycler updates/approves these)
            #         instance = PurchasesRequest.objects.filter(id=record_id, recycler=user).first()
            #         if instance:
            #             serializer = PurchasesRequestSerializer(instance)

            # If no instance is found
            if not instance:
                return Response({
                    "status": False,
                    "error": f"No record found with ID {record_id} for this user."
                }, status=status.HTTP_404_NOT_FOUND)

            # Return the serialized data
            return Response({
                "status": True,
                "data": serializer.data,
                "type":type
            }, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            # This shouldn't typically trigger due to .first(), but kept for robustness
            return Response({
                "status": False,
                "error": f"Record with ID {record_id} does not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# WASTE FILTERS
@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class WasteTypeDetailView(APIView):
    def get(self, request, waste_type_name):
        try:
            # Case-insensitive lookup
            waste_type = WasteType.objects.get(name__iexact=waste_type_name)
            serializer = WasteTypeSerializer(waste_type)
            response_data = {
                "status": True,
                "data": serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except WasteType.DoesNotExist:
            response_data = {
                "status": False,
                "error": f"Waste type '{waste_type_name}' not found"
            }
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class WasteTypeListView(APIView):
    def get(self, request):
        waste_types = WasteType.objects.all()
        serializer = WasteTypeSerializer(waste_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class WasteTypeNamesView(APIView):
    def get(self, request):
        waste_types = WasteType.objects.all()
        serializer = WasteTypeNameSerializer(waste_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)
    


@method_decorator(cache_page(60 * 30), name='dispatch')
class ProducerTypeListView(APIView):
    def get(self, request):
        producer_types = ProducerType.objects.all()
        serializer = ProducerTypeSerializer(producer_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

@method_decorator(cache_page(60 * 30), name='dispatch')
class RecyclerTypeListView(APIView):
    def get(self, request):
        recycler_types = RecyclerType.objects.all()
        serializer = RecyclerTypeSerializer(recycler_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

@method_decorator(cache_page(60 * 30), name='dispatch')
class ProductTypeListView(APIView):
    def get(self, request):
        product_types = ProductType.objects.all()
        serializer = ProductTypeSerializer(product_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

@method_decorator(cache_page(60 * 30), name='dispatch')
class CreditTypeListView(APIView):
    def get(self, request):
        credit_types = CreditType.objects.all()
        serializer = CreditTypeSerializer(credit_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)
    

@method_decorator(cache_page(60 * 30 * 24), name='dispatch')  
class AllTypesView(APIView):
    def get(self, request):
        # Fetch all data
        waste_types = WasteType.objects.all()
        # producer_types = ProducerType.objects.all()
        recycler_types = RecyclerType.objects.values('name').distinct()
        product_types = ProductType.objects.values('name').distinct()
        credit_types = CreditType.objects.values('name').distinct()
        formatted_allowed_docs = [{"name": doc} for doc in allowed_docs]
        states = [{"name": s} for s in indian_states]

        # Serialize the data
        waste_serializer = WasteTypeNameSerializer(waste_types, many=True)
        # producer_serializer = ProducerTypeSerializer(producer_types, many=True)
        recycler_serializer = RecyclerTypeSerializer(recycler_types, many=True)
        product_serializer = ProductTypeSerializer(product_types, many=True)
        credit_serializer = CreditTypeSerializer(credit_types, many=True)

        # Construct the response
        response_data = {
            "status": True,
            "data": {
                "waste_type": waste_serializer.data,
                "recycler_type": recycler_serializer.data,
                "product_type": product_serializer.data,
                "credit_type": credit_serializer.data,
                "trail_documents": formatted_allowed_docs,
                "state": states
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

@method_decorator(cache_page(60 * 30 * 24), name='dispatch')  
class AllowedDocsView(APIView):
    def get(self, request):
        return Response({'allowed_docs': allowed_docs,"status":True}, status=status.HTTP_200_OK)