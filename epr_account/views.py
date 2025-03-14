from rest_framework import viewsets, permissions, status, serializers,generics
from rest_framework.response import Response
from users.authentication import CustomJWTAuthentication
from .models import RecyclerEPR, ProducerEPR,EPRCredit,EPRTarget,CreditOffer,CounterCreditOffer
from .serializers import RecyclerEPRSerializer, ProducerEPRSerializer, EPRCreditSerializer,EPRTargetSerializer, CreditOfferSerializer,CounterCreditOfferSerializer
from users.models import Recycler, Producer
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404
from .filters import CreditOfferFilter
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend


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
        epr_account_id = self.request.query_params.get("epr_id")
        if epr_account_id:
            try:
                get_epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
                return EPRCredit.objects.filter(recycler=self.request.user, epr_account=get_epr_account)
            except RecyclerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_id or not authorized."})
        return EPRCredit.objects.filter(recycler=self.request.user)

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
                    "recycler": self.request.user.id,  # Note: This might be a typo; should it be self.request.user.id?
                    "epr_registration_number": epr_account.epr_registration_number,
                    "waste_type": epr_account.waste_type,
                })

                kwargs["data"] = request_data
            return super().get_serializer(*args, **kwargs)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})


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
                epr_credit=get_epr_credit
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
                    epr_credit = EPRCredit.objects.get(id=epr_credit_id, recycler=self.request.user, epr_account=get_epr_account)
                except RecyclerEPR.DoesNotExist:
                    raise ValidationError({"error": "Invalid epr_account_id or not authorized."})
                except EPRCredit.DoesNotExist:
                    raise ValidationError({"error": "No record found for credit with the given EPR account."})

                request_data = {key: value[0] if isinstance(value, list) and value else value for key, value in self.request.data.items()}

                # Add additional fields
                request_data.update({
                    "epr_account": get_epr_account.id,
                    "epr_registration_number": get_epr_account.epr_registration_number,
                    "waste_type": get_epr_account.waste_type,
                    "epr_credit": epr_credit.id
                })

                kwargs["data"] = request_data
              # Handle PATCH requests with special care for JSONField
            elif self.request.method == "PATCH" and "supporting_doc" in self.request.data:
                # Get original data
                instance = self.get_object()
                # Create a separate data dictionary for patch
                patch_data = dict(self.request.data)
                
                # Special handling for supporting_doc if it's coming in as a string
                if "supporting_doc" in patch_data:
                    supporting_doc_value = patch_data["supporting_doc"]
                    # If it's a string representation of JSON, parse it
                    if isinstance(supporting_doc_value, list) and supporting_doc_value:
                        import json
                        try:
                            # Strip any whitespace/newlines and parse
                            cleaned_string = supporting_doc_value[0].strip()
                            patch_data["supporting_doc"] = json.loads(cleaned_string)
                        except json.JSONDecodeError:
                            raise ValidationError({"error": "Invalid JSON format for supporting_doc"})
                print(patch_data)

                
                kwargs["data"] = patch_data
                kwargs["partial"] = True
        

            return super().get_serializer(*args, **kwargs)

        except Exception as e:
            raise ValidationError({"error": str(e)})


# PRODUCER -> CREATE EPR ACCOUNT ✅ 
class ProducerEPRViewSet(viewsets.ModelViewSet):
    serializer_class = ProducerEPRSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsProducer]
    parser_classes = (MultiPartParser, FormParser,JSONParser)

    def get_queryset(self):
        return ProducerEPR.objects.filter(producer=self.request.user)

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
        elif isinstance(user, Recycler):
            filter_field = "recycler"
        else:
            return queryset  # Return empty queryset for unsupported user types

        # Base queryset for the user
        queryset = CounterCreditOffer.objects.filter(**{filter_field: user})

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
                "error": str(e)
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

                serializer.save(
                    producer=self.request.user,
                    recycler=get_credit_offer.recycler,
                    credit_offer=get_credit_offer,
                    status='Pending',
                    is_approved=False
                )
            else:
                raise ValidationError({"error": "Only producers can create counter credit offers."})

        except Exception as e:
            raise ValidationError({"error": f"Creation error: {str(e)}"})

# PUBLIC VIEW FOR LISTING CREDIT OFFERS

class PublicCreditOfferListView(generics.ListAPIView):
    queryset = CreditOffer.objects.filter(is_approved=True).select_related('epr_account', 'epr_credit')
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