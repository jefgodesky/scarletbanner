from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import BasePermission

User = get_user_model()


def is_self_or_staff(subj: User | AnonymousUser, obj: User):
    is_user = subj == obj
    return is_user or subj.is_staff


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated(detail="This action requires authentication.")
        return super().has_permission(request, view)


class IsSelfOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_self_or_staff(request.user, obj)
