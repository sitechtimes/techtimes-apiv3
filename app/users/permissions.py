import jwt
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView
from core import settings
from users.models import User
from rest_framework.exceptions import AuthenticationFailed

class HasValidRegistrationToken(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return False
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.SIMPLE_JWT["SIGNING_KEY"], algorithms=["HS256"])
            if payload.get('purpose') != 'registration':
                return False
            if payload.get('exp') < payload.get('iat'):
                return False
            email = payload.get("email")
            request.user = User.objects.get(email=email)
            return True
        except(jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            raise AuthenticationFailed({"message": "Registration token invalid or expired"})
