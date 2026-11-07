from typing import Any, cast

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from users.tokens import RegistrationToken

# validate token
class RegistrationAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        try:
            return RegistrationToken(cast(Any, raw_token))
        except TokenError as e:
            raise InvalidToken({"detail": str(e)})
