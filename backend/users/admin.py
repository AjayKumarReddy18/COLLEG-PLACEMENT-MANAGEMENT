from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.
    Used strictly for development/testing inspection.
    """

    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "student_id",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "student_id")
    ordering = ("-created_at",)

    # Fieldsets for viewing / editing users in admin
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {"fields": ("first_name", "last_name", "phone_number", "student_id")},
        ),
        (
            "Role & Permissions",
            {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important Dates", {"fields": ("created_at", "updated_at", "last_login")}),
    )

    # Fieldsets for adding users in admin
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "student_id",
                    "phone_number",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "last_login")
