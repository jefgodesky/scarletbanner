from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from scarletbanner.utils.permissions import IsAuthenticated, IsSelfOrStaff

from .serializers import UserCreateSerializer, UserSerializer

User = get_user_model()


@extend_schema_view(
    create=extend_schema(
        summary="Create a new user",
        description="Create a new user with the given username, password, and "
        "email. You won’t be able to log in with this user until "
        "you have verified your email address.",
    ),
    list=extend_schema(summary="List all users", description="This endpoint returns a list of all users."),
    retrieve=extend_schema(
        summary="Retrieve a user", description="This endpoint returns the user with the given username."
    ),
    update=extend_schema(
        summary="Update a user",
        description="This endpoint updates the user with the given username. "
        "You must supply all fields, even if they are unchanged. "
        "You can only update your own account (unless you have "
        "staff privileges).",
    ),
    partial_update=extend_schema(
        summary="Update a user",
        description="This endpoint updates the user with the given username. "
        "You can supply just the fields that you wish to change "
        "to this endpoint. You can only update your own account "
        "(unless you have staff privileges).",
    ),
    destroy=extend_schema(
        summary="Delete a user",
        description="This endpoint deletes the user with the given username. "
        "You can only delete your own account (unless you have "
        "staff privileges).",
    ),
    me=extend_schema(
        summary="Retrieve your own account",
        description="This endpoint returns the currently authenticated user.",
    ),
)
class UserViewSet(
    CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet
):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        self_or_staff = ["update", "partial_update", "destroy", "me"]
        if self.action in self_or_staff:
            return [IsAuthenticated(), IsSelfOrStaff()]
        return super().get_permissions()

    def get_queryset(self, *args, **kwargs):
        return User.objects.all()

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=True)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)
