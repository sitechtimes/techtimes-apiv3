from django.urls import path
from users.views import UserCreationViewSet, UserSignOut, UserSendVerifcationCodeViewSet, UserSignIn, UserVerifyVerificationCode

urlpatterns = [
    path("auth/signup", UserCreationViewSet.as_view({"post": "create"}), name="signup"),
    path("auth/send_token", UserSendVerifcationCodeViewSet.as_view({"get": "sendVerificationCode"}), name="send_token"),
    path("auth/verify/<str:token>", UserVerifyVerificationCode.as_view({"get": "verifyCode"}), name="verify_code"),
    path("auth/signin", UserSignIn.as_view({"post": "signIn"}), name="signin"),
    path("auth/logout", UserSignOut.as_view({"post": "signOut"}), name="signout")
]
