from django.contrib.auth import get_user_model
from rest_framework import serializers

from scarletbanner.users.models import User as UserType

User = get_user_model()


class UserSerializer(serializers.ModelSerializer[UserType]):
    class Meta:
        model = User
        fields = ["username", "name", "email", "url", "is_active", "is_staff"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "username"},
        }


class UserPublicSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ["username", "url", "is_active", "is_staff"]


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password", "email"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
