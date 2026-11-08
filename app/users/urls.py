from django.urls import path
from users.views import UserCreationViewSet, UserLogOut, UserSendVerifcationCodeViewSet, UserSignIn, UserVerifyVerificationCode

urlpatterns = [
    path("auth/signup", UserCreationViewSet.as_view(), name="signup"),
    path("auth/send_token", UserSendVerifcationCodeViewSet.as_view(), name="send_token"),
    path("auth/verify/<token>", UserVerifyVerificationCode.as_view(), name="verify_code"),
    path("auth/signin", UserSignIn.as_view(), name="signin"),
    path("auth/logout", UserLogOut.as_view(), name="signout")
]
