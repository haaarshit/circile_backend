from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from uuid import UUID
from users.models import Recycler, Producer

from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id)
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomRefreshTokenAuthentication(TokenRefreshView):
    serializer_class = TokenRefreshSerializer
    
    def post(self, request, *args, **kwargs):
        print(f"Request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        
        try:
            if not serializer.is_valid():
                print(f"Serializer errors: {serializer.errors}")
                return Response({
                    "error": "Invalid refresh token format",
                    "details": serializer.errors,
                    "status": False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            refresh_token = serializer.validated_data["refresh"]
            
            try:
                token = RefreshToken(refresh_token)
                print(f"Token payload: {token.payload}")
            except Exception as token_error:
                print(f"Token parsing error: {token_error}")
                return Response({
                    "error": "Could not parse refresh token",
                    "details": str(token_error),
                    "status": False
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Extract user_id as string from the token payload
            user_id = token.payload.get("user_id")
            print(f"User ID from token: {user_id}")
            
            if not user_id:
                print(f"Available payload fields: {token.payload.keys()}")
                return Response({
                    "error": "User ID not found in token",
                    "status": False
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Query using the string representation directly
            user = Recycler.objects.filter(id=user_id).first() or Producer.objects.filter(id=user_id).first()
            
            if not user:
                print(f"No user found with ID: {user_id}")
                return Response({
                    "error": "User not found",
                    "status": False
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                print(f"User {user_id} is inactive")
                return Response({
                    "error": "User is inactive",
                    "status": False
                }, status=status.HTTP_403_FORBIDDEN)
            
            return Response({
                "access": str(token.access_token),
                "status": True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(traceback.format_exc())
            return Response({
                "error": "Error processing refresh token",
                "details": str(e),
                "status": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)