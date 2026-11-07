from rest_framework_simplejwt.tokens import Token
from datetime import timedelta

class RegistrationToken(Token):
    token_type = "registration"
    lifetime = timedelta(minutes=30)

class EmailVerificationToken(Token):
    token_type = "email_verification"
    lifetime = timedelta(minutes=30)
