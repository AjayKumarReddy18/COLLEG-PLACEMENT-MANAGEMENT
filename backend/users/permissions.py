from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class IsStudent(BasePermission):
    """
    Allows access only to authenticated users with the STUDENT role.
    """

    message = "Access denied: You must be a Student to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.Role.STUDENT
        )


class IsCompany(BasePermission):
    """
    Allows access only to authenticated users with the COMPANY role.
    """

    message = "Access denied: You must be a Company representative to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.Role.COMPANY
        )


class IsTPO(BasePermission):
    """
    Allows access only to authenticated users with the TPO (Training & Placement Officer) role.
    Authorization is strictly based on user.role == TPO, not is_staff.
    """

    message = "Access denied: You must be a TPO to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.Role.TPO
        )
