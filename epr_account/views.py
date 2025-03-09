from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from users.authentication import CustomJWTAuthentication
from .models import RecyclerEPR, ProducerEPR,EPRCredit,EPRTarget
from .serializers import RecyclerEPRSerializer, ProducerEPRSerializer, EPRCreditSerializer,EPRTargetSerializer
from users.models import Recycler, Producer
from rest_framework.parsers import MultiPartParser, FormParser

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