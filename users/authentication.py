from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth.models import AnonymousUser
from users.models import Recycler, Producer
from jwt import decode
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from uuid import UUID  
class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_user(self, validated_token):
        """
        Override the default user retrieval method to support multiple user models.
        """
        try:
            user_id = validated_token.get("user_id")
            if not user_id:
                raise AuthenticationFailed("Invalid token")

            user_id = UUID(user_id)    
            # Check in both Recycler and Producer models
            user = Recycler.objects.filter(id=user_id).first() or Producer.objects.filter(id=user_id).first()

            if not user:
                raise AuthenticationFailed("User not found")

            if not user.is_active:
                raise AuthenticationFailed("User is inactive")

            return user

        except Exception as e:
            raise AuthenticationFailed("Invalid authentication token")
