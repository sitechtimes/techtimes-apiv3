import time
from datetime import timedelta
from typing import Any, cast
 
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import request
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.html import strip_tags
from jwt import DecodeError
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, Token
from users.models import User
from users.authentication import RegistrationAuthentication
from users.serializers import SignInSerializer, SignUpSerializer, UserSerializer
from users.tokens import EmailVerificationToken, RegistrationToken

EMAIL_COOLDOWN = 60  # Cooldown duration in seconds

class UserCreationViewSet(
    mixins.CreateModelMixin,    
    viewsets.GenericViewSet
):
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, req: Request, *args: Any, **kwargs: Any) -> Response:
        # deletes an account if they don't verify within 30 minutes though it only
        # deletes if someone else makes an account
        expiry_limit = timezone.now() - timedelta(minutes=30)
        User.objects.filter(verified=False, date_joined__lt=expiry_limit).delete()

        serializer = self.get_serializer(data=req.data)
        # checks if user with email already exists 
        if not serializer.is_valid():
            errors = cast(dict[str, Any], serializer.errors)
            email_errors = errors.get("email", [])
            if any(e.code == "unique" for e in email_errors):
                return Response({"message": "user already exists"}, status=status.HTTP_409_CONFLICT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # creates temp token to be used to send email for verification
            user = serializer.save()
            reg_token = str(RegistrationToken.for_user(user))
            return Response({"message": 'temp account created', "reg_token": reg_token}, status=status.HTTP_200_OK)
        except IntegrityError: 
            return Response({"message": "user already exists"}, status=status.HTTP_409_CONFLICT)

class UserSendVerifcationCodeViewSet(
    viewsets.GenericViewSet
):
    serializer_class=Serializer
    authentication_classes = [RegistrationAuthentication]
    permission_classes = [IsAuthenticated]
    def sendVerificationCode(self, req: Request) -> Response:
        user = cast(User, req.user)
        # checks if user is already verified and ignores the whole process
        if getattr(user, 'verified', False):
            return Response({"verified": True }, status=status.HTTP_200_OK)
        verification_code = getattr(user, 'verification_code', None)
        # if a verication code is generated check if there is a cooldown
        if verification_code:
            try:
                existing_code = EmailVerificationToken(verification_code, verify=True) 
                 
                iat = existing_code.get('iat', 0)
                cooldown= (iat + EMAIL_COOLDOWN) * 1000
                now_seconds = time.time()

                if (now_seconds - iat) < EMAIL_COOLDOWN: 
                    return Response({"message": "email machine on cooldown", "time": cooldown}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                    
            except (TokenError, DecodeError):
                pass 
        # otherwise generate a verification code and send email
        new_verification_token = str(EmailVerificationToken.for_user(user))
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
        return Response({"message": "email sent"}, status=status.HTTP_200_OK)

class UserVerifyVerificationCode(
    viewsets.GenericViewSet
):
    serializer = Serializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def verifyCode(self, request: Request, token: str) -> Response:
        try:
            validated_code = EmailVerificationToken(cast(Token,token))
        except TokenError:
            return Response({"message": "invalid or expired link"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=validated_code['user_id'])
        except User.DoesNotExist:
            return Response({"message": "invalid or expired link"}, status=status.HTTP_400_BAD_REQUEST)
        # if already validated it ignores it
        if user.verified:
            return Response({"message": "verified"}, status=status.HTTP_200_OK)
        # wrong token
        if user.verification_code != token:
            return Response({"message": "invalid link"}, status=status.HTTP_400_BAD_REQUEST)
        user.verified = True
        user.verification_code = None
        user.save(update_fields=["verification_code", "verified"])
        return Response({"message": "verified"}, status=status.HTTP_200_OK)

class UserSignIn(
    viewsets.GenericViewSet
):
    serializer_class = SignInSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    # verify creds
    def signIn(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
 
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = User.objects.filter(email__iexact=email).first()
        if not user or not user.check_password(password) or not user.is_active:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.verified:
            return Response({"message": "email not verified"}, status=status.HTTP_403_FORBIDDEN)
        # generates tokens
        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["role"] = user.role
        
        return Response({
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )
class UserSignOut(
    viewsets.GenericViewSet
):
    serializers=Serializer
    permission_classes=[IsAuthenticated]
    # blacklists tokens so they can't be used to log in
    def signOut(self, request: Request) -> Response:
        raw = request.data.get("refresh", "") if isinstance(request.data, dict) else None
        if raw:
            try:
                RefreshToken(cast(Token, raw)).blacklist()
            except TokenError:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)


