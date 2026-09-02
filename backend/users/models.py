from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of usernames.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        role = extra_fields.get("role")
        valid_roles = [User.Role.STUDENT, User.Role.COMPANY, User.Role.TPO]
        if role and role not in valid_roles:
            raise ValueError(
                f"Invalid role: {role}. Role must be one of {valid_roles}"
            )

        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)  # Securely hashes the password
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.TPO)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the College Placement Management System.
    Strictly supports only 3 roles: STUDENT, COMPANY, TPO.
    """

    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        COMPANY = "COMPANY", "Company"
        TPO = "TPO", "TPO"

    # Core Identifiers
    student_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Student / College ID",
        help_text="Unique Student or College ID (Applicable for Students)",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
    )

    # Personal Information
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Phone Number",
    )

    # Role & Status
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        verbose_name="User Role",
        help_text="Role in the placement system (STUDENT, COMPANY, TPO)",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Status",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff Status",
        help_text="Designates whether the user can log into the Django admin site.",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
