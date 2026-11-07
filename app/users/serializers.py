from rest_framework import serializers
from users.models import User
from rest_framework.validators import UniqueValidator

class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="user already exists")]
    )
    
    class Meta(serializers.ModelSerializer.Meta):
        model = User # type: ignore[reportAssignmentType]
        fields = ['username', 'email', 'password', 'role', 'image_url', 'verification_code', 'verified']
        extra_kwargs = {
            'password': {'write_only': True},
            'verification_code': {'write_only': True, 'required': False},
            'verified': {'read_only': True}          
        }

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

