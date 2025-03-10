from rest_framework import viewsets, permissions, status, serializers,generics
from rest_framework.response import Response
from users.authentication import CustomJWTAuthentication
from .models import RecyclerEPR, ProducerEPR,EPRCredit,EPRTarget,CreditOffer,CounterCreditOffer
from .serializers import RecyclerEPRSerializer, ProducerEPRSerializer, EPRCreditSerializer,EPRTargetSerializer, CreditOfferSerializer,CounterCreditOfferSerializer
from users.models import Recycler, Producer
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404

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

# RECYLER -> CREATE EPR ACCOUNT 
class RecyclerEPRViewSet(viewsets.ModelViewSet):
    print("entered RecyclerEPRViewSet =====================> ")
    serializer_class = RecyclerEPRSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated,IsRecycler]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return RecyclerEPR.objects.filter(recycler=self.request.user)
    # PUT
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.recycler != request.user:
            return Response({"error": "You are not authorized to update this record."}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)
    
    # PATCH
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

# RECYLER -> CREATE CREDIT
class EPRCreditViewSet(viewsets.ModelViewSet):
    serializer_class = EPRCreditSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated,IsRecycler]

    def get_queryset(self):
        epr_account_id = self.request.query_params.get("epr_id")
        if epr_account_id:
            try:
               get_epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
            except RecyclerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_account_id or not authorized."})
            if get_epr_account:
                return EPRCredit.objects.filter(producer=self.request.user,epr_account=get_epr_account)
        return EPRCredit.objects.filter(recycler=self.request.user)
 
    def get_serializer(self, *args, **kwargs):
        if self.request.method == "POST":
            epr_account_id = self.request.query_params.get("epr_id")

            if not epr_account_id:
                raise serializers.ValidationError({"error": "epr_account_id is required in query parameters."})

            try:
                epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
            except RecyclerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_account_id or not authorized."})

            kwargs["data"] = {
                **self.request.data,  # Preserve request data
                "epr_account": epr_account.id,  
                "epr_registration_number": epr_account.epr_registration_number,
                "waste_type": epr_account.waste_type,
            }

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(recycler=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.recycler != request.user:
            return Response({"error": "You are not authorized to update this record."}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
# RECYLER -> CREATE CREDIT OFFER
class CreditOfferViewSet(viewsets.ModelViewSet):
    serializer_class = CreditOfferSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated,IsRecycler]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        epr_account_id = self.request.query_params.get("epr_id")
        epr_credit_id = self.request.query_params.get("epr_credit_id")

        if epr_account_id:
                get_epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
                if epr_credit_id:
                    get_epr_credit = EPRCredit.objects.get(id=epr_credit_id, recycler=self.request.user,epr_account=get_epr_account)
                    if get_epr_account and get_epr_credit:
                        return CreditOffer.objects.filter(recycler=self.request.user,epr_account=get_epr_account,epr_credit=get_epr_credit)
                else:
                    return CreditOffer.objects.filter(recycler=self.request.user,epr_account=get_epr_account)
                
        return CreditOffer.objects.filter(recycler=self.request.user)

    def get_serializer(self, *args, **kwargs):
        print("Enter get serializer ")
        if self.request.method == "POST":
            print("Enter get serializer ")
            epr_account_id = self.request.query_params.get("epr_id")
            epr_credit_id = self.request.query_params.get("epr_credit_id")

            if not epr_account_id or not epr_credit_id:
                raise serializers.ValidationError(
                    {"error": "Both epr_account_id and epr_credit_id are required in query parameters."}
                )

            try:
                get_epr_account = RecyclerEPR.objects.get(id=epr_account_id, recycler=self.request.user)
                epr_credit = EPRCredit.objects.get(id=epr_credit_id, recycler=self.request.user, epr_account=get_epr_account)
            except RecyclerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_account_id or not authorized."})
            except EPRCredit.DoesNotExist:
                raise serializers.ValidationError({"error": "No record found for credit with the given EPR account."})
            data = kwargs.get("data", {}).copy()
        
            
            print(kwargs["data"])
            
            request_data = {}
            for key, value in self.request.data.items():
                # in case if values are in the list
                if isinstance(value, list) and value:
                    request_data[key] = value[0]  
                else:
                    request_data[key] = value 
                
            # Add the additional fields
            request_data.update({
                "epr_account": get_epr_account.id,
                "epr_registration_number": get_epr_account.epr_registration_number,
                "waste_type": get_epr_account.waste_type,
                "epr_credit": epr_credit.id
            })
            
            kwargs["data"] = request_data
            print("-----------")
            print(kwargs["data"])

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        epr_account_id = self.request.query_params.get("epr_id")
        epr_credit_id = self.request.query_params.get("epr_credit_id")
        
        # Get the related objects
        epr_account = RecyclerEPR.objects.get(id=epr_account_id)
        epr_credit = EPRCredit.objects.get(id=epr_credit_id)
        
        # Save with all required relationships
        serializer.save(
            recycler=self.request.user,
            epr_account=epr_account,
            epr_credit=epr_credit
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.recycler != request.user:
            return Response({"error": "You are not authorized to update this record."}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# PRODUCER -> CREATE EPR ACCOUNT 
class ProducerEPRViewSet(viewsets.ModelViewSet):
    
    serializer_class = ProducerEPRSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated,IsProducer]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return ProducerEPR.objects.filter(producer=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.producer != request.user:
            return Response({"error": "You are not authorized to update this record."}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        print('pathc method called')
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
# PRODUCER -> ADD TARGET
class EPRTargetViewSet(viewsets.ModelViewSet):
    serializer_class = EPRTargetSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated,IsProducer]

    def get_queryset(self):
         
        epr_account_id = self.request.query_params.get("epr_id")
        if epr_account_id:
            try:
               get_epr_account = ProducerEPR.objects.get(id=epr_account_id, producer=self.request.user)
            except ProducerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_account_id or not authorized."})
            if get_epr_account:
                return EPRTarget.objects.filter(producer=self.request.user,epr_account=get_epr_account)
        return EPRTarget.objects.filter(producer=self.request.user)
 
    def get_serializer(self, *args, **kwargs):
        if self.request.method == "POST":
            epr_account_id = self.request.query_params.get("epr_id")

            if not epr_account_id:
                raise serializers.ValidationError({"error": "epr_account_id is required in query parameters."})

            try:
                epr_account = ProducerEPR.objects.get(id=epr_account_id, producer=self.request.user)
            except ProducerEPR.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid epr_account_id or not authorized."})

            kwargs["data"] = {
                **self.request.data,  # Preserve request data
                "epr_account": epr_account.id,  
                "epr_registration_number": epr_account.epr_registration_number,
                "waste_type": epr_account.waste_type,
            }

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(producer=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.producer != request.user:
            return Response({"error": "You are not authorized to update this record."}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    

# PRODUCER -> CREATE COUNTER CREDIT OFFER
class CounterCreditOfferViewSet(viewsets.ModelViewSet):
    serializer_class = CounterCreditOfferSerializer
    authentication_classes = [CustomJWTAuthentication]
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsProducer]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsRecycler]
        else:  # list, retrieve
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):

        credit_offer_id = self.request.query_params.get("credit_offer_id")
    
        if isinstance(self.request.user, Producer):
            if credit_offer_id:
                try:
                    get_credit_offer = CreditOffer.objects.get(id=credit_offer_id)
                    return CounterCreditOffer.objects.filter(credit_offer=get_credit_offer, producer=self.request.user)
                except CreditOffer.DoesNotExist:
                    raise serializers.ValidationError({"error": "Credit offer not found."})
            return CounterCreditOffer.objects.filter(producer=self.request.user)
        
        # For Recyclers - filter by recycler
        elif isinstance(self.request.user, Recycler):
            if credit_offer_id:
                try:
                    get_credit_offer = CreditOffer.objects.get(id=credit_offer_id, recycler=self.request.user)
                    return CounterCreditOffer.objects.filter(credit_offer=get_credit_offer, recycler=self.request.user)
                except CreditOffer.DoesNotExist:
                    raise serializers.ValidationError({"error": "Credit offer not found or not authorized."})
            return CounterCreditOffer.objects.filter(recycler=self.request.user)
        
        return CounterCreditOffer.objects.none()
    
    def get_serializer(self, *args, **kwargs):
            if self.request.method == "POST":
                credit_offer_id = self.request.query_params.get("credit_offer_id")
                if credit_offer_id:
                        try:
                          get_credit_offer = CreditOffer.objects.get(id=credit_offer_id)
                        except CreditOffer.DoesNotExist:
                          raise serializers.ValidationError({"error": "Invalid epr_account_id or not authorized."})
                else:    
                    raise serializers.ValidationError(
                        {"error": "Both credit offer id is required for creating counter credit offer"}
                    )

                request_data = {}
                for key, value in self.request.data.items():
                    # in case if values are in the list
                    if isinstance(value, list) and value:
                        request_data[key] = value[0]  
                    else:
                        request_data[key] = value 
                    
                # Add the additional fields
                request_data.update({
                    "recycler": get_credit_offer.recycler,  
                    "credit_offer":get_credit_offer.id,
                    "producer":self.request.user.id
                })
                
                kwargs["data"] = request_data


            return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        if(isinstance(self.request.user,Producer)):
            credit_offer_id = self.request.query_params.get("credit_offer_id")
            get_credit_offer = CreditOffer.objects.get(id=credit_offer_id)

            serializer.save(producer=self.request.user,recycler=get_credit_offer.recycler,credit_offer=get_credit_offer,status='Pending',is_approved=False)
        else:
            raise serializers.ValidationError(
                    {"error": "Only producer can create counter credit offer"}
                )
        
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.recycler != request.user:
            return Response(
                {"error": "You are not authorized to update this record."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)



class RecyclerDashboardView(APIView):
    
    serializer_class = CounterCreditOfferSerializer
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated,IsRecycler]

    def get(self, request):
            # Get the Recycler instance for the authenticated user
        recycler = request.user
            
            # Get all counter credit offers related to this recycler
        counter_offers = recycler.recycler_counter_credit_offers.all().values(
                "id", "producer__company_name", "quantity", "offer_price"
            )

        credit_offers = recycler.recycler_epr_credits.all().values(
            "epr_account","epr_registration_number","waste_type","producer_type","credit_type","year","processing_capacity","comulative_certificate_potential","available_certificate_value"
        )

        response_data = {
                "recycler": {
                    "id": recycler.id,
                    "company_name": recycler.company_name,
                },
                "counter_offers": list(counter_offers),
                "credit_offers": list(credit_offers),
            }

        return Response(response_data, status=200)