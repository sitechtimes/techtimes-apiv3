from rest_framework import serializers
from users.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="user already exists")]
    )
    
    class Meta(serializers.ModelSerializer.Meta):
        model = User # type: ignore[reportAssignmentType]
        fields = ['username', 'email', 'password'] 
        extra_kwargs = {
            'password': {'write_only': True},     
        }
    def validate_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta(serializers.ModelSerializer.Meta):
        model = User # type: ignore[reportAssignmentType]  
        fields = ["id", "username", "email", "role", "image_url", "verified"]
        read_only_fields = fields

