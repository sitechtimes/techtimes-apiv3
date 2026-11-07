from datetime import timedelta
from os import wait
from django.utils import timezone
from typing import Any
import time
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
from core import settings
from users.models import User
from users.permissions import HasValidRegistrationToken
from users.serializers import SignUpSerializer

EMAIL_COOLDOWN = 60  # Cooldown duration in seconds

class UserCreationViewSet(
    mixins.CreateModelMixin,    
    viewsets.GenericViewSet
):
    serializer_class = SignUpSerializer
    permission_classes = []
    
    def perform_create(self, serializer):
        expiry_limit = timezone.now() - timedelta(minutes=30)
        User.objects.filter(verified=False, date_joined__lt=expiry_limit).delete()
        return serializer.save()


    def create(self, req: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=req.data)
        
        if not serializer.is_valid():
            if 'email' in serializer.errors:
                return Response({"message": "user already exists"}, status=status.HTTP_409_CONFLICT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        try:
            user = self.perform_create(serializer)
            payload = {
                "userId": user.id,
                "purpose": "registration",
                "exp": int(time.time()) + (30 * 60)
            }
            reg_token = jwt.encode(payload, settings.SIMPLE_JWT['SIGNING_KEY'], algorithm='HS256')

            return Response({"message": 'temp account created', "reg_token": reg_token}, status=status.HTTP_200_OK)
        except IntegrityError: 
            return Response({"message": "user already exists"}, status=status.HTTP_409_CONFLICT)

class UserSendVerifcationCodeViewSet(
    viewsets.GenericViewSet
):
    serializer_class=Serializer
    permission_classes = [HasValidRegistrationToken]
    def sendVerificationCode(self, req: Request) -> Response:
        user = cast(User, req.user)
        # checks if user is already verified and ignores the whole process
        if getattr(user, 'verified', False):
            return Response({"verified": True }, status=status.HTTP_200_OK)
        verification_code = getattr(user, 'verification_code', None)
        # checks if db already has verification code and uses it
        if verification_code:
            try:
                existing_code = jwt.decode(verification_code, settings.SIMPLE_JWT['SIGNING_KEY'], algorithm=['HS256'])
                
                iat = existing_code.get('iat', 0)
                cooldown_end_ms = (iat + EMAIL_COOLDOWN) * 1000
                now_seconds = time.time()

                if (now_seconds - iat) < EMAIL_COOLDOWN: 
                    return Response({"message": "email machine on cooldown", "time": cooldown_end_ms}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                    
            except jwt.DecodeError:
                pass 

        payload = {
            "email": user.email,
            "iat": int(time.time()),
            "exp": int(time.time()) + (20 * 60)
        }
        new_verification_token = jwt.encode(payload, settings.SIMPLE_JWT['SIGNING_KEY'], algorithm="HS256")

        user.verification_code = new_verification_token
        user.save()

        html_message = f'Hello there, click the following link to verify your email: <a href="{settings.SITE_URL}:8000/auth/verify/{new_verification_token}">Verify Email</a>'        
        try:
            send_mail(
                subject="TechTimes Email confirmation",
                message=strip_tags(html_message),
                from_email=settings.MAILERS["default"]["OPTIONS"]["username"],
                recipient_list=[user.email],
                html_message=html_message,
                using="default",
                fail_silently=False,
            )
        except Exception:
            return Response({"message": "failed to send email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

