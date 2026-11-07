from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from rest_framework.request import Request 

# is user verified with email
class IsVerified(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "verified", False))
