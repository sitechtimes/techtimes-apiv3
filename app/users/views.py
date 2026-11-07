import time
from typing import Any
import jwt
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.db import IntegrityError
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from typing import cast

from rest_framework.serializers import Serializer
from users.models import User
from users.serializers import SignUpSerializer

EMAIL_COOLDOWN = 60  # Cooldown duration in seconds

class UserCreationViewSet(
    mixins.CreateModelMixin,    
    viewsets.GenericViewSet
):
    serializer_class = SignUpSerializer
    permission_classes = []
    def create(self, req: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=req.data)
        
        if not serializer.is_valid():
            if 'email' in serializer.errors:
                return Response({"message": "user already exists"}, status=status.HTTP_409_CONFLICT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        try:
            self.perform_create(serializer)
            return Response(status=status.HTTP_200_OK)
        except IntegrityError: 
            return Response({"message": "user already exists"}, status=status.HTTP_409_CONFLICT)

class UserSendVerifcationCodeViewSet(
    viewsets.GenericViewSet
):
    serializer_class=Serializer
    permission_classes = []
    def sendVerificationCode(self, req: Request) -> Response:
        user = cast(User, req.user)

        if getattr(user, 'verified', False):
            return Response({"verified": True}, status=status.HTTP_200_OK)
