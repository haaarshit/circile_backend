from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
# Import serializer for user updates

from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

import jwt
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .utils import validate_unique_email
from .models import Recycler, Producer
from .serializers import RecyclerSerializer, ProducerSerializer,RecyclerUpdateSerializer,ProducerUpdateSerializer
from .authentication import CustomJWTAuthentication

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
        # Send verification token to be verified
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

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("username")
        password = request.data.get("password")
        user = None

        try:
            user = Recycler.objects.get(email=email)
        except Recycler.DoesNotExist:
            try:
                user = Producer.objects.get(email=email)
            except Producer.DoesNotExist:
                return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            return Response({"error": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_verified:
            user.generate_verification_token()
            user.send_verification_email()
            return Response({"error": "Email is not verified. Please check your email."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT tokens manually
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })

class UpdateUserProfileView(APIView):
  
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
     
    # TODO -> MAY REMOVE 
    def put(self, request):
        return self.update_profile(request, partial=False)  

    def patch(self, request):
        return self.update_profile(request, partial=True)  

    def update_profile(self, request, partial):
        user = request.user  # Authenticated user

        if isinstance(user, Recycler):
            serializer = RecyclerUpdateSerializer(user, data=request.data, partial=partial)
        elif isinstance(user, Producer):
            serializer = ProducerUpdateSerializer(user, data=request.data, partial=partial)
        else:
            return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profile updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




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

