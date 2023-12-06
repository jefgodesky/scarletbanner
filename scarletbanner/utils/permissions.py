from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated(detail="This action requires authentication.")
        return super().has_permission(request, view)


class IsSelfOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj or request.user.is_staff
