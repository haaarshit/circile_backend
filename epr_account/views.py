from rest_framework import viewsets, permissions, status, serializers,generics
from rest_framework.response import Response
from users.authentication import CustomJWTAuthentication
from .models import RecyclerEPR, ProducerEPR,EPRCredit,EPRTarget,CreditOffer,CounterCreditOffer,Transaction,WasteType
from .serializers import RecyclerEPRSerializer, ProducerEPRSerializer, EPRCreditSerializer,EPRTargetSerializer, CreditOfferSerializer,CounterCreditOfferSerializer,TransactionSerializer, WasteTypeSerializer, WasteTypeNameSerializer
from users.models import Recycler, Producer
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
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

from django.conf import settings


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


    def get_queryset(self):
            return RecyclerEPR.objects.filter(recycler=self.request.user)
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
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
            'email', 'full_name', 'mobile_no', 'designation', 'password',
            'company_name', 'city', 'state', 'gst_number', 'pcb_number', 'address',
            'company_logo', 'pcb_doc','registration_date'
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
            queryset = self.get_queryset()
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
            queryset = self.get_queryset()
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

            serializer.save(
                recycler=self.request.user,
                epr_account=get_epr_account,
                epr_credit=get_epr_credit,
            )

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

    def get_queryset(self):
        queryset =  ProducerEPR.objects.filter(producer=self.request.user)
        waste_type = self.request.query_params.get('waste_type', None)
        if waste_type:
            queryset = queryset.filter(waste_type=waste_type)

        return queryset

    # GET - List
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
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
            'email', 'full_name', 'mobile_no', 'designation', 'password',
            'company_name', 'city', 'state', 'gst_number', 'pcb_number', 'address',
            'company_logo', 'pcb_doc','registration_date'
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
            queryset = self.get_queryset()
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
            queryset = self.get_queryset()
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
            
            print(request.data)

            serializer = self.get_serializer(instance, data=request.data, partial=True)
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
            return Response({
                "status": False,
                "error": e.detail if hasattr(e, 'detail') else str(e)
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
                    raise ValidationError({"error": "Invalid credit_offer_id or not authorized."})
                    
                producer_epr_id = self.request.data['producer_epr']
                producer_epr = ProducerEPR.objects.get(id=producer_epr_id, producer=self.request.user)

                if producer_epr.waste_type !=  get_credit_offer.waste_type:
                   raise ValidationError({  "error": f"Your EPR Account's Waste Type does not matches the the waste type of the credit offer you want to buy. Epr's waste type:{producer_epr.waste_type} Credit offer's waste type: {get_credit_offer.waste_type}", "status": False})
              
                

                 # Validate quantity against credit_available
                validated_data = serializer.validated_data
                quantity = validated_data.get("quantity")
                credit_available = get_credit_offer.credit_available

                if quantity is None:
                    raise ValidationError({"error": "Quantity is required to create a counter credit offer."})

                if quantity > credit_available:
                    raise ValidationError({
                        "error": f"Quantity ({quantity}) exceeds available credits ({credit_available}) in the credit offer."
                    })

                serializer.save(
                    producer=self.request.user,
                    recycler=get_credit_offer.recycler,
                    credit_offer=get_credit_offer,
                    status='pending',
                    is_approved=False
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
class PublicCreditOfferListView(generics.ListAPIView):
    queryset = CreditOffer.objects.filter(is_sold=False).select_related('epr_account', 'epr_credit')
    serializer_class = CreditOfferSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CreditOfferFilter
    ordering_fields = [
        'price_per_credit',  
        'FY',
        'credit_available',
        'waste_type',
        'epr_credit__credit_type',
    ]
    ordering = ['price_per_credit']  

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
            return Transaction.objects.filter(recycler=user)
        elif isinstance(user, Producer):
            return Transaction.objects.filter(producer=user)
        return Transaction.objects.none()
 
        # GET - List
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
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
            credit_offer_id = request.query_params.get('credit_offer_id')
            counter_credit_offer_id = request.query_params.get('counter_credit_offer_id')

            # Validate query parameters
            if not credit_offer_id and not counter_credit_offer_id:
                return Response({
                    "status": False,
                    "error": "Provide either credit_offer_id or counter_credit_offer_id"
                }, status=status.HTTP_400_BAD_REQUEST)
    
            if credit_offer_id and counter_credit_offer_id:
                return Response({
                    "status": False,
                    "error": "Provide only one of credit_offer_id or counter_credit_offer_id"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prepare data 
            data = request.data.copy()
            data['producer'] = request.user.id

            data.pop('is_complete', None)
            data.pop('transaction_proof', None)
            data.pop('status', None)

            producer_epr = None
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
                # Fetch producer_epr from request body
                producer_epr_id = data.get('producer_epr_id')
                if not producer_epr_id:
                    return Response({
                        "status": False,
                        "error": "producer_epr_id is required in the request body when creating a transaction from a credit offer"
                    }, status=status.HTTP_400_BAD_REQUEST)
                try:
                     producer_epr = ProducerEPR.objects.get(id=producer_epr_id, producer=request.user)
                except ProducerEPR.DoesNotExist:
                    return Response({
                        "status": False,
                        "error": "Invalid producer_epr_id or not authorized"
                    }, status=status.HTTP_400_BAD_REQUEST)


            # Populate data from CreditOffer
            if credit_offer_id:
                try:
                    credit_offer = CreditOffer.objects.get(id=credit_offer_id)
                    data['credit_offer'] = credit_offer.id
                    data['recycler'] = credit_offer.recycler.id
                    data['credit_quantity'] = credit_offer.credit_available
                    data['waste_type'] = credit_offer.waste_type
                    data['recycler_type'] = credit_offer.epr_account.recycler_type
                    data['total_price'] = float(data['credit_quantity']) * credit_offer.price_per_credit
                    data['price_per_credit'] = credit_offer.price_per_credit
                    data['credit_type'] = credit_offer.epr_credit.credit_type
                    data['product_type'] = credit_offer.epr_credit.product_type
                    data['producer_type'] = request.user.epr_accounts.first().producer_type
                    data['offered_by'] = credit_offer.recycler.unique_id
                except CreditOffer.DoesNotExist:
                    return Response({
                        "status": False,
                        "error": "Credit offer not found"
                    }, status=status.HTTP_404_NOT_FOUND)

            # Populate data from CounterCreditOffer
            else:
                try:
                    counter_credit_offer = CounterCreditOffer.objects.get(id=counter_credit_offer_id)
                    if counter_credit_offer.status != 'approved':
                        return Response({
                            "status": False,
                            "error": "Counter credit offer must be approved"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    data['counter_credit_offer'] = counter_credit_offer.id
                    data['credit_offer'] = counter_credit_offer.credit_offer.id
                    data['recycler'] = counter_credit_offer.recycler.id
                    data['credit_quantity'] = counter_credit_offer.quantity  
                    data['waste_type'] = counter_credit_offer.credit_offer.waste_type
                    data['recycler_type'] = counter_credit_offer.credit_offer.epr_account.recycler_type
                    data['total_price'] = float(data['credit_quantity']) * counter_credit_offer.offer_price
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
            ).first()

            if not epr_target:
                return Response({
                    "status": False,
                    "error": "No matching EPRTarget found for this transaction, Please make epr target for given epr account"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate credit_quantity against EPRTarget
            remaining_quantity = epr_target.target_quantity - epr_target.achieved_quantity
            if float(data['credit_quantity']) > remaining_quantity:
                return Response({
                    "status": False,
                    "error": f"Credit quantity ({data['credit_quantity']}) cannot exceed remaining target quantity ({remaining_quantity})"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Add producer_epr to data
            data['producer_epr'] = producer_epr.id
            print(data['producer_epr'])

            # Serialize and save the data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            transaction = serializer.save()

   
            # Fetch producer and recycler details
            producer = Producer.objects.get(id=request.user.id)
            recycler = Recycler.objects.get(id=data['recycler'])


            # comman field
            email ='support@circle8.in'
            contact_number = '+91 9620220013'

            # Email to Recycler (HTML)
            recycler_subject = "New Transaction Created"
            recycler_html_message = (
                f"<!DOCTYPE html>"
                f"<html>"
                f"<body style='font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;'>"
                f"<div style='max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
                f"<h2 style='color: #2c3e50; text-align: center;'>New Transaction Notification</h2>"
                f"<p style='color: #34495e;'>Dear <strong>{recycler.full_name}</strong>,</p>"
                f"<p style='color: #34495e;'>A new transaction has been created by <strong>{producer.full_name}</strong>. Below are the details:</p>"
              
                f"<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>"

                f"<tr><td style='padding: 10px;'><strong>Request By: </strong></td><td style='padding: 10px;'>{transaction.producer.unique_id}</td></tr>"
              
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Work Order ID</strong></td><td style='padding: 10px;'>{transaction.order_id}</td></tr>"
              
                f"<tr><td style='padding: 10px;'><strong>Work Order Date</strong></td><td style='padding: 10px;'>{transaction.work_order_date}</td></tr>"
                
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Waste Type</strong></td><td style='padding: 10px;'>{transaction.waste_type}</td></tr>"

                f"<tr><td style='padding: 10px;'><strong>Credit Type</strong></td><td style='padding: 10px;'>{transaction.credit_type}</td></tr>"
              
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Price per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"
              
                f"<tr><td style='padding: 10px;'><strong>Product Type</strong></td><td style='padding: 10px;'>{transaction.product_type}</td></tr>"
              
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Producer Type</strong></td><td style='padding: 10px;'>{transaction.producer_type}</td></tr>"

                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Total Price</strong></td><td style='padding: 10px;'>{transaction.total_price}</td></tr>"
              
              
                f"<tr><td style='padding: 10px;'><strong>Credit Quantity</strong></td><td style='padding: 10px;'>{transaction.credit_quantity}</td></tr>"

              
                f"<tr><td style='padding: 10px;'><strong>Price Per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"

                              
                f"<tr><td style='padding: 10px;'><strong>Trail Documents</strong></td><td style='padding: 10px;'>{transaction.credit_offer.trail_documents}</td></tr>"


                f"<tr><td style='padding: 10px;'><strong>Status</strong></td><td style='padding: 10px;'>{transaction.status}</td></tr>"
              
                f"</table>"

                f"<h3 style='color: #2980b9;'>Producer Details</h3>"
                f"<strong>EPR Registration No:</strong> {transaction.producer_epr.epr_registration_number} <br>"
                f"<strong>EPR Registered Name:</strong> {transaction.producer_epr.epr_registered_name}<br>"
                f"<strong>Email:</strong> {email}<br>"
                f"<strong>Contact Number:</strong> {contact_number}<br>"
                f"<p style='color: #34495e; text-align: center;'>Please review and update the transaction status as needed.</p>"
                f"<div style='text-align: center; margin-top: 20px;'>"
                f"</div>"
                f"<p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>This is an automated message. Please do not reply directly to this email.</p>"
                f"</div>"
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

            # Email to Producer (Stylish HTML)
            producer_subject = "Transaction Request Sent to Recycler"
            producer_html_message = (
                f"<!DOCTYPE html>"
                f"<html>"
                f"<body style='font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;'>"
                f"<div style='max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
                f"<h2 style='color: #2c3e50; text-align: center;'>Transaction Request Confirmation</h2>"
                f"<p style='color: #34495e;'>Dear <strong>{producer.full_name}</strong>,</p>"
                f"<p style='color: #34495e;'>Your transaction request has been successfully sent to <strong>{recycler.full_name}</strong>. Below are the details:</p>"
                f"<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>"

                f"<tr><td style='padding: 10px;'><strong>Offered By: </strong></td><td style='padding: 10px;'>{transaction.recycler.unique_id}</td></tr>"
              
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Work Order ID</strong></td><td style='padding: 10px;'>{transaction.order_id}</td></tr>"
              
                f"<tr><td style='padding: 10px;'><strong>Work Order Date</strong></td><td style='padding: 10px;'>{transaction.work_order_date}</td></tr>"
                
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Waste Type</strong></td><td style='padding: 10px;'>{transaction.waste_type}</td></tr>"

                f"<tr><td style='padding: 10px;'><strong>Credit Type</strong></td><td style='padding: 10px;'>{transaction.credit_type}</td></tr>"
              
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Price per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"
              
                f"<tr><td style='padding: 10px;'><strong>Product Type</strong></td><td style='padding: 10px;'>{transaction.product_type}</td></tr>"
              
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Producer Type</strong></td><td style='padding: 10px;'>{transaction.producer_type}</td></tr>"
              
                f"<tr><td style='padding: 10px;'><strong>Credit Quantity</strong></td><td style='padding: 10px;'>{transaction.credit_quantity}</td></tr>"

              
                f"<tr><td style='padding: 10px;'><strong>Price Per Credit</strong></td><td style='padding: 10px;'>{transaction.price_per_credit}</td></tr>"
                f"<tr style='background-color: #ecf0f1;'><td style='padding: 10px;'><strong>Total Price</strong></td><td style='padding: 10px;'>{transaction.total_price}</td></tr>"

                f"<tr><td style='padding: 10px;'><strong>Recycler Type</strong></td><td style='padding: 10px;'>{transaction.recycler_type}</td></tr>"


                f"<tr><td style='padding: 10px;'><strong>Trail Documents</strong></td><td style='padding: 10px;'>{transaction.credit_offer.trail_documents}</td></tr>"

                f"<tr><td style='padding: 10px;'><strong>Status</strong></td><td style='padding: 10px;'>{transaction.status}</td></tr>"
              
                f"</table>"

                f"<h3 style='color: #2980b9;'>Recycler Details</h3>"
                f"<strong>EPR Registration No:</strong> {transaction.credit_offer.epr_account.epr_registration_number} <br>"
                f"<strong>EPR Registered Name:</strong> {transaction.credit_offer.epr_account.epr_registered_name}<br>"
                f"<strong>Email:</strong> {email}<br>"
                f"<strong>Contact Number:</strong> {contact_number}<br>"
                f"<p style='color: #34495e; text-align: center;'>Please review and update the transaction status as needed.</p>"
                f"<div style='text-align: center; margin-top: 20px;'>"
                f"</div>"
                f"<p style='color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;'>This is an automated message. Please do not reply directly to this email.</p>"
                f"</div>"
                f"</body>"
                f"</html>"
            )
            send_mail(
                subject=producer_subject,
                message="",  
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[producer.email],
                fail_silently=False,
                html_message=producer_html_message
            )
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
   
            # TODO => ADD CHECK IF TRANSACTION IS ALREADY APPROVED
            
            if transaction.status == 'approved':
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
                    transaction.credit_offer.is_sold = True
                    transaction.credit_offer.credit_available = 0
                    transaction.credit_offer.save()
            
            return Response({"data":serializer.data,"status":True})
        
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


    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
     # Block DELETE method
 
    def destroy(self, request, *args, **kwargs):
        return Response({
            "status": False,
            "error": "Deletion of transactions is not allowed."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    


# WASTE FILTERS
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

class WasteTypeListView(APIView):
    def get(self, request):
        waste_types = WasteType.objects.all()
        serializer = WasteTypeSerializer(waste_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

class WasteTypeNamesView(APIView):
    def get(self, request):
        waste_types = WasteType.objects.all()
        serializer = WasteTypeNameSerializer(waste_types, many=True)
        response_data = {
            "status": True,
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)