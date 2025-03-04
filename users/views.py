from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

import jwt
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .utils import validate_unique_email
from .models import Recycler, Producer
from .serializers import RecyclerSerializer, ProducerSerializer

class RegisterRecyclerView(generics.CreateAPIView):
    """
    View for Recycler user registration
    """

    queryset = Recycler.objects.all()
    serializer_class = RecyclerSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # print('---------------------------------------------------------------------------')
        # print(request.data.get("email"))
        # print('---------------------------------------------------------------------------')
        existing_user =  validate_unique_email(request.data.get("email"))
        print('---------------------------------------------------------------------------')
        print(existing_user)
        print('---------------------------------------------------------------------------')
        if existing_user:
            return Response(
                {"error": "User already exist."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user but keep is_verified as False
        user = serializer.save()
        user.generate_verification_token()
        user.send_verification_email()
        
        return Response({
            "message": "Registration successful. Please check your email to verify your account.",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)


class RegisterProducerView(generics.CreateAPIView):
    """
    View for Producer user registration
    """

    queryset = Producer.objects.all()
    serializer_class = ProducerSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # print('---------------------------------------------------------------------------')
        # print(request.data.get("email"))
        # print('---------------------------------------------------------------------------')
        existing_user =  validate_unique_email(request.data.get("email"))
        print('---------------------------------------------------------------------------')
        print(existing_user)
        print('---------------------------------------------------------------------------')
        if existing_user:
            return Response(
                {"error": "User already exist."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user but keep is_verified as False
        user = serializer.save()
        user.generate_verification_token()
        user.send_verification_email()
        
        return Response({
            "message": "Registration successful. Please check your email to verify your account.",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    """
    Custom login view with email verification check
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get("username")

        print('---------------------------------------------------------------------------')
        print(email)
        print('---------------------------------------------------------------------------')
        

        # Check both Recycler and Producer models
        try:
            user = Recycler.objects.get(email=email)
        except Recycler.DoesNotExist:
            try:
                user = Producer.objects.get(email=email)
            except Producer.DoesNotExist:
                return Response(
                    {"error": "Invalid email or password."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Verify email status
        if not user.is_verified:
            return Response(
                {"error": "Email not verified. Please check your email."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().post(request, *args, **kwargs)


@api_view(['POST'])
def send_verification_email(request):
    """
    Resend verification email
    """
    email = request.data.get('email')

    # Check both Recycler and Producer models
    try:
        user = Recycler.objects.get(email=email)
    except Recycler.DoesNotExist:
        try:
            user = Producer.objects.get(email=email)
        except Producer.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Generate and send new verification token
    user.generate_verification_token()
    user.send_verification_email()

    return Response({
        'message': 'Verification email resent successfully'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
# def verify_email(request,user_type,token):
#     """
#     Verify user email using token
#     """
    # token = request.GET.get('token')

    # # Try to find user in both Recycler and Producer models
    # def find_user_by_token(token):
    #     for model in [Recycler, Producer]:
    #         try:
    #             return model.objects.get(verification_token=token)
    #         except model.DoesNotExist:
    #             continue
    #     return None

    # user = find_user_by_token(token)

    # if not user:
    #     return Response({
    #         'error': 'Invalid verification token'
    #     }, status=status.HTTP_400_BAD_REQUEST)

    # # Check token expiration (24 hours)
    # if (timezone.now() - user.token_created_at).total_seconds() > 24 * 3600:
    #     return Response({
    #         'error': 'Verification token has expired'
    #     }, status=status.HTTP_400_BAD_REQUEST)

    # # Verify the user
    # user.is_verified = True
    # user.verification_token = None
    # user.save()

    # return Response({
    #     'message': 'Email verified successfully'
    # }, status=status.HTTP_200_OK)

def verify_email(request, user_type, token):
 
    # Select the correct model based on user type
    model = Recycler if user_type.lower() == "recycler" else Producer
    user = get_object_or_404(model, verification_token=token)

    # Check if token is expired (24 hours)
    if (timezone.now() - user.token_created_at).total_seconds() > 24 * 3600:
        return Response({'error': 'Verification token has expired'}, status=status.HTTP_400_BAD_REQUEST)

    # Verify user
    user.is_verified = True
    user.verification_token = None
    user.save()

    # TODO -> redirect to profile of the user
    return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)