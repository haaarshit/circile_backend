from rest_framework import status, serializers,generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
# Import serializer for user updates

from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.core.exceptions import ValidationError

import jwt
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .utils import validate_unique_email
from .models import Recycler, Producer
from .serializers import RecyclerSerializer, ProducerSerializer,RecyclerUpdateSerializer,ProducerUpdateSerializer,RecyclerDetailSerializer,ProducerDetailSerializer,ForgotPasswordSerializer,ResetPasswordSerializer
from .authentication import CustomJWTAuthentication
from epr_account.models import RecyclerEPR, ProducerEPR, EPRCredit, EPRTarget, CreditOffer, CounterCreditOffer, Transaction, PurchasesRequest




class RegisterRecyclerView(generics.CreateAPIView):
    """
    View for Recycler user registration
    """

    queryset = Recycler.objects.all()
    serializer_class = RecyclerSerializer
    permission_classes = [AllowAny]


    def create(self, request, *args, **kwargs):

        try:
            existing_user = validate_unique_email(request.data.get("email"))
            print('---------------------------------------------------------------------------')
            print(existing_user)
            print('---------------------------------------------------------------------------')
            if existing_user:
                return Response(
                    {"error": "User already exist.","status":False}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            request_data = {}
            for key, value in self.request.data.items():
                    if isinstance(value, list) and value:
                        request_data[key] = value[0]
                    else:
                        request_data[key] = value
            print(request_data)
            serializer = self.get_serializer(data=request_data)
            print(request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create user but keep is_verified as False
            user = serializer.save()
            user.generate_verification_token()
            user.send_verification_email()
            
            return Response({
                "message": "Registration successful. Please check your email to verify your account.",
                "user": serializer.data,
                "status":True
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return Response(
                {"error": f"{str(e)}","status":False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # return Response(
        #     {"error": "Registration failed due to an internal server error. Please try again later."},
        #     status=status.HTTP_500_INTERNAL_SERVER_ERROR
        # )

class RegisterProducerView(generics.CreateAPIView):
    """
    View for Producer user registration
    """

    queryset = Producer.objects.all()
    serializer_class = ProducerSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        
        try:
            existing_user =  validate_unique_email(request.data.get("email"))
            print('---------------------------------------------------------------------------')
            print(existing_user)
            print('---------------------------------------------------------------------------')
            if existing_user:
                return Response(
                    {"error": "User already exist.","status":False}, 
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
            ,"status":True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return Response(
                {"error": f"{str(e)}","status":False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LoginView(TokenObtainPairView):
    """
    Custom login view with email verification check
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get("username")
            password = request.data.get("password")
            user = None
            account_type = None

            try:
                user = Recycler.objects.get(email=email)
                account_type = "recycler"
            except Recycler.DoesNotExist:
                try:
                    user = Producer.objects.get(email=email)
                    account_type = "producer"
                except Producer.DoesNotExist:
                    return Response({"error": "Invalid email or password.","status":False}, status=status.HTTP_400_BAD_REQUEST)

            if not check_password(password, user.password):
                return Response({"error": "Invalid email or password.","status":False}, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_verified:
                user.generate_verification_token()
                user.send_verification_email()
                return Response({"error": "Email is not verified. Please check your email.","status":False}, status=status.HTTP_400_BAD_REQUEST)

            # Generate JWT tokens manually
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "account": account_type  ,
                "status":True
            })
        except Exception as e:
            # Handle other exceptions
            return Response(
                {"error": f"{str(e)}","status":False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class UpdateUserProfileView(APIView):
  
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
     
    # TODO -> MAY REMOVE 
    # def put(self, request):
    #     return self.update_profile(request, partial=False)  
    def put(self, request):
            return Response(
                {"error": "PUT method is not allowed. Please use PATCH instead.","status":False},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
    def patch(self, request):
            return self.update_profile(request, partial=True)  

    def update_profile(self, request, partial):
            try:
                user = request.user  # Authenticated user
                protected_fields = ['email', 'mobile_no','password']
                for field in protected_fields:
                    if field in request.data:
                        print(field)
                        current_value = getattr(user, field)
                        print(field)
                        requested_value = request.data.get(field)
                        
                        # Only raise error if they're actually trying to change the value
                        if current_value != requested_value:
                            return Response(
                                {"error": f"{field} cannot be modified after registration","status":False},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                if isinstance(user, Recycler):
                    serializer = RecyclerUpdateSerializer(user, data=request.data, partial=partial)
                elif isinstance(user, Producer):
                    serializer = ProducerUpdateSerializer(user, data=request.data, partial=partial)
                else:
                    return Response({"error": "Invalid user type","status":False}, status=status.HTTP_400_BAD_REQUEST)

                if serializer.is_valid():
                    try:
                        serializer.save()  # This triggers model save() and clean()
                        return Response(
                            {"message": "Profile updated successfully", "data": serializer.data, "status": True},
                            status=status.HTTP_200_OK
                        )
                    except ValidationError as e:
                        # Handle validation errors from the model's clean() method
                        error_dict = e.message_dict if hasattr(e, 'message_dict') else {'general': str(e)}
                        return Response(
                            {
                                "error": "Validation failed",
                                "details": error_dict,
                                "status": False
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                else:
                    return Response(
                        {
                            "error": "Invalid data",
                            "details": serializer.errors,
                            "status": False
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                    print(f"Registration error: {str(e)}")
                    return Response(
                        {"error": f"{str(e)}","status":False},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
         # Handle password change specifically
        # if 'password' in request.data:
        #     current_password = request.data.get('current_password')
        #     new_password = request.data.get('password')
            
        #     if not current_password:
        #         return Response(
        #             {"error": "Current password is required to change password"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
            
        #     if not check_password(current_password, user.password):
        #         return Response(
        #             {"error": "Current password is incorrect"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
            
        #     if len(new_password) < 8:  # Basic validation, add more as needed
        #         return Response(
        #             {"error": "New password must be at least 8 characters"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
            
        #     user.set_password(new_password)
        #     user.save()
            
        #     data = request.data.copy()
        #     data.pop('password')
        #     data.pop('current_password', None)  
        # else:
        #     data = request.data

class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Get the refresh token from the request data
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required", "status": False},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Blacklist the refresh token
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError as e:
                return Response(
                    {"error": "Invalid refresh token", "status": False},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"message": "Successfully logged out", "status": True},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"{str(e)}", "status": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetProfileView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user  # Authenticated user
            
            # Determine user type and use appropriate serializer
            if isinstance(user, Recycler):
                serializer = RecyclerDetailSerializer(user)  # Create a detailed serializer for profile viewing
            elif isinstance(user, Producer):
                serializer = ProducerDetailSerializer(user)  # Create a detailed serializer for profile viewing
            else:
                return Response({"error": "Invalid user type","status":False}, status=status.HTTP_400_BAD_REQUEST)
            
            # Return user profile data
            return Response(
                {
                    "status": "success",
                    "message": "Profile retrieved successfully",
                    "data": serializer.data,
                    "status":True
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
                    print(f"Registration error: {str(e)}")
                    return Response(
                        {"error": f"{str(e)}","status":False},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class ForgotPasswordView(APIView):
    def post(self, request):
        try:
            serializer = ForgotPasswordSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                user = Recycler.objects.filter(email=email).first() or Producer.objects.filter(email=email).first()
                
                if not user:
                    return Response(
                    {"error": f"user not found with this email", "status": False},
                    status=status.HTTP_400_BAD_REQUEST
                )
                     
                if user and user.is_active:
                    user.generate_password_reset_token()
                    user.send_password_reset_email()
                    return Response({"message": "Password reset email sent.","status":True}, status=status.HTTP_200_OK)
                return Response({"error": "User not found or inactive."}, status=status.HTTP_404_NOT_FOUND)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {"error": f"{str(e)}", "status": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResetPasswordView(APIView):
    def post(self, request, user_type, token):
        
        try:
            serializer = ResetPasswordSerializer(data=request.data)
            if serializer.is_valid():
                new_password = serializer.validated_data['new_password']
                if user_type.lower() == "recycler":
                    user = Recycler.objects.filter(password_reset_token=token).first()
                elif user_type.lower() == "producer":
                    user = Producer.objects.filter(password_reset_token=token).first()
                else:
                    return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

                if user and user.reset_password(token, new_password):
                    return Response({"message": "Password reset successfully.","status":True}, status=status.HTTP_200_OK)
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserCountStatsView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user  # Authenticated user
            stats = {
                "user_type": None,
                "epr_accounts": 0,
                "epr_credits": 0,  # For Recycler only
                "epr_targets": 0,  # For Producer only
                "credit_offers": 0,  # For Recycler only
                "counter_credit_offers_made": 0,  # For Producer only
                "counter_credit_offers_received": 0,  # For Recycler only
                "transactions": 0,
                "achived_targets":0,
                "complete_order":0,
                "pending_order":0,
                "direct_purchase":0
            }

            if isinstance(user, Recycler):
                stats["user_type"] = "recycler"
                # Count Recycler-specific records
                stats["epr_accounts"] = RecyclerEPR.objects.filter(recycler=user).count()
                stats["epr_credits"] = EPRCredit.objects.filter(recycler=user).count()
                stats["credit_offers"] = CreditOffer.objects.filter(recycler=user).count()
                stats["counter_credit_offers_received"] = CounterCreditOffer.objects.filter(recycler=user).count()
                stats["transactions"] = Transaction.objects.filter(recycler=user).count()
                stats["pending_order"] = Transaction.objects.filter(recycler=user,is_complete=False).count()
                stats["complete_order"] = Transaction.objects.filter(recycler=user,is_complete=True).count()
                stats["direct_purchase"] = PurchasesRequest.objects.filter(recycler=user).count()
                


            elif isinstance(user, Producer):
                stats["user_type"] = "producer"
                stats["epr_accounts"] = ProducerEPR.objects.filter(producer=user).count()
                stats["epr_targets"] = EPRTarget.objects.filter(producer=user).count()
                stats["achived_targets"] = EPRTarget.objects.filter(producer=user,is_achieved=True).count()
                stats["counter_credit_offers_made"] = CounterCreditOffer.objects.filter(producer=user).count()
                stats["transactions"] = Transaction.objects.filter(producer=user).count()
                stats["pending_order"] = Transaction.objects.filter(producer=user,is_complete=False).count()
                stats["complete_order"] = Transaction.objects.filter(producer=user,is_complete=True).count()
                stats["direct_purchase"] = PurchasesRequest.objects.filter(producer=user).count()

            else:
                return Response(
                    {"error": "Invalid user type", "status": False},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {
                    "status": True,
                    "message": "EPR statistics retrieved successfully",
                    "data": stats
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e), "status": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CheckProfileCompletionView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user  # Authenticated user
            
            # Define required fields for each user type
            recycler_required_fields = [
                'email', 'mobile_no', 'company_name', 'address', 'full_name',
                'city', 'state', 
                'designation','gst_number','pcb_number',
                'account_holder_name', 'account_number', 'bank_name', 
                'ifsc_code', 'branch_name'

            ]
            
            producer_required_fields = [
                'email', 'mobile_no', 'company_name', 'address', 'full_name',
                'city', 'state',  
                'designation','gst_number','pcb_number'
            ]
            
            # Check user type and validate completeness
            if isinstance(user, Recycler):
                required_fields = recycler_required_fields
                user_type = "recycler"
            elif isinstance(user, Producer):
                required_fields = producer_required_fields
                user_type = "producer"
            else:
                return Response(
                    {"status": False, "message": "Invalid user type"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for incomplete fields
            incomplete_fields = []
            for field in required_fields:
                try:
                    value = getattr(user, field)
                    # Check if field is None or empty string
                    if value is None or (isinstance(value, str) and not value.strip()):
                        incomplete_fields.append(field)
                except AttributeError:
                    # Field doesn't exist in model
                    incomplete_fields.append(field)
            
            if incomplete_fields:
                return Response({
                    "status": False,
                    "message": "Profile is incomplete",
                    "details": {
                        "user_type": user_type,
                        "incomplete_fields": incomplete_fields
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                "status": True,
                "message": "Profile is complete",
                "details": {
                    "user_type": user_type
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"status": False, "message": f"Error checking profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            return Response({'error': 'User not found',"status":False}, status=status.HTTP_404_NOT_FOUND)

    # Generate and send new verification token
    user.generate_verification_token()
    user.send_verification_email()

    return Response({
        'message': 'Verification email resent successfully',"status":True
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def verify_email(request, user_type, token):
    try:
 
        # Select the correct model based on user type
        model = Recycler if user_type.lower() == "recycler" else Producer
        user = get_object_or_404(model, verification_token=token)

        # Check if token is expired (24 hours)
        if (timezone.now() - user.token_created_at).total_seconds() > 24 * 3600:
            return Response({'error': 'Verification token has expired',"status":False}, status=status.HTTP_400_BAD_REQUEST)

        # Verify user
        user.is_verified = True
        user.verification_token = None
        user.save()

        # TODO -> redirect to profile of the user
        return Response({'message': 'Email verified successfully',"status":True}, status=status.HTTP_200_OK)
    
    except Exception as e:
                    print(f"Mail verification error: {str(e)}")
                    return Response(
                        {"error": f"{str(e)}","status":False},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )