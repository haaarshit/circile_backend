from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from uuid import UUID
from users.models import Recycler, Producer

# class CustomRefreshTokenAuthentication(TokenRefreshView):
#     serializer_class = TokenRefreshSerializer
#     from users.models import Recycler, Producer

#     def post(self, request, *args, **kwargs):
#         print(request.data)
#         serializer = self.get_serializer(data=request.data)

#         try:
#             print(request.data)
#             serializer.is_valid(raise_exception=True)
#             refresh_token = serializer.validated_data["refresh"]
#             print(refresh_token)
#             token = RefreshToken(refresh_token)
#             print(token)

#             # Extract user_id from the refresh token
#             user_id = token.payload.get("user_id")
#             print(f"user_id:{user_id}")

#             if not user_id:
#                 return Response({"error": "Invalid token","status":False}, status=status.HTTP_401_UNAUTHORIZED)

#             try:
#                 user_id = UUID(user_id)  # Convert to UUID if needed
#             except ValueError:
#                 return Response({"error": "Invalid user ID format","status":False}, status=status.HTTP_401_UNAUTHORIZED)

#             # Check if user exists in Recycler or Producer
#             user = Recycler.objects.filter(id=user_id).first() or Producer.objects.filter(id=user_id).first()

#             if not user:
#                 return Response({"error": "User not found","status":False}, status=status.HTTP_401_UNAUTHORIZED)

#             if not user.is_active:
#                 return Response({"error": "User is inactive","status":False}, status=status.HTTP_403_FORBIDDEN)

#             # Return new access token
#             return Response({"access": str(token.access_token),"status":True}, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"error": "Invalid or expired refresh token","status":False}, status=status.HTTP_401_UNAUTHORIZED)


import traceback

class CustomRefreshTokenAuthentication(TokenRefreshView):
    serializer_class = TokenRefreshSerializer
    
    def post(self, request, *args, **kwargs):
        print(f"Request data: {request.data}")
        serializer = self.get_serializer(data=request.data)

        try:
            # Validate the serializer
            if not serializer.is_valid():
                print(f"Serializer errors: {serializer.errors}")
                return Response({
                    "error": "Invalid refresh token format",
                    "details": serializer.errors,
                    "status": False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the refresh token
            refresh_token = serializer.validated_data["refresh"]
            print(f"Refresh token: {refresh_token[:10]}...")
            
            # Parse the token
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

            # Extract user_id from the token payload
            user_id = token.payload.get("user_id")
            print(f"User ID from token: {user_id}")
            
            # Check if we got a user_id
            if not user_id:
                # Check what fields are in the payload for debugging
                print(f"Available payload fields: {token.payload.keys()}")
                return Response({
                    "error": "User ID not found in token",
                    "status": False
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Convert user_id to UUID if needed
            try:
                user_id = UUID(user_id)
            except ValueError as uuid_error:
                print(f"UUID conversion error: {uuid_error}")
                return Response({
                    "error": "Invalid user ID format",
                    "details": str(uuid_error),
                    "status": False
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Find the user
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

            # Return new access token
            return Response({
                "access": str(token.access_token),
                "status": True
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Print detailed error for debugging
            print(f"Unexpected error: {e}")
            print(traceback.format_exc())
            return Response({
                "error": "Error processing refresh token",
                "details": str(e),
                "status": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)