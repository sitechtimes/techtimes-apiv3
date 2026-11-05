from rest_framework import serializers
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="username")
    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "image_url", "verified"]
