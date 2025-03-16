from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import SuperAdmin
from uuid import UUID



class SuperAdminJWTAuthentication(JWTAuthentication):
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
        try:
            user_id = validated_token.get("user_id")
            if not user_id:
                raise AuthenticationFailed("Invalid token")

            user_id = UUID(user_id)
            superadmin = SuperAdmin.objects.filter(id=user_id).first()

            if not superadmin:
                raise AuthenticationFailed("SuperAdmin not found")
            if not superadmin.is_active:
                raise AuthenticationFailed("SuperAdmin is inactive")

            return superadmin

        except Exception:
            raise AuthenticationFailed("Invalid authentication token")