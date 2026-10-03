from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

from profiles.models import CompanyProfile, StudentProfile
from .validators import validate_email_address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model (safe read-only representation).
    Excludes sensitive fields like passwords and permissions.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "student_id",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "created_at",
        ]
        read_only_fields = fields


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new STUDENT.
    Enforces student_id requirement, password confirmation, and password complexity.
    Always assigns role = STUDENT.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    email = serializers.EmailField(validators=[validate_email_address])
    student_id = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        max_length=50,
        help_text="Unique Student or College ID",
    )
    department = serializers.CharField(required=False, allow_blank=True)
    course = serializers.CharField(required=False, allow_blank=True)
    year = serializers.IntegerField(required=False, min_value=1)
    cgpa = serializers.DecimalField(
        required=False,
        max_digits=4,
        decimal_places=2,
        min_value=Decimal("0.00"),
        max_value=Decimal("10.00"),
    )
    skills = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "student_id",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
            "department",
            "course",
            "year",
            "cgpa",
            "skills",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def validate_student_id(self, value):
        if value is None:
            return None
        val = value.strip()
        if not val:
            return None
        if User.objects.filter(student_id__iexact=val).exists():
            raise serializers.ValidationError("A student with this Student ID already exists.")
        return val

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        # Validate password complexity against Django's validators
        validate_password(password)

        profile_fields = ["department", "course", "year", "cgpa"]
        supplied_profile_fields = [field for field in profile_fields if field in attrs]
        if supplied_profile_fields and len(supplied_profile_fields) != len(profile_fields):
            raise serializers.ValidationError(
                {
                    field: "This field is required when creating a student profile."
                    for field in profile_fields
                    if field not in attrs
                }
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        profile_data = {
            field: validated_data.pop(field)
            for field in ["department", "course", "year", "cgpa", "skills"]
            if field in validated_data
        }
        # Ensure role cannot be set by client and is strictly STUDENT
        validated_data.pop("role", None)

        with transaction.atomic():
            user = User.objects.create_user(
                role=User.Role.STUDENT,
                password=password,
                **validated_data,
            )
            if profile_data:
                StudentProfile.objects.create(user=user, **profile_data)
        return user


class CompanyRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new COMPANY.
    Enforces password confirmation and password complexity.
    Always assigns role = COMPANY.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    email = serializers.EmailField(validators=[validate_email_address])
    company_name = serializers.CharField(required=False, allow_blank=True)
    company_description = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        validators=[validate_email_address],
    )
    contact_phone = serializers.CharField(required=False, allow_blank=True)
    company_size = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
            "company_name",
            "company_description",
            "industry",
            "location",
            "contact_email",
            "contact_phone",
            "company_size",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        # Validate password complexity against Django's validators
        validate_password(password)

        profile_fields = ["company_name", "industry", "location", "contact_email"]
        supplied_profile_fields = [field for field in profile_fields if field in attrs]
        if supplied_profile_fields and len(supplied_profile_fields) != len(profile_fields):
            raise serializers.ValidationError(
                {
                    field: "This field is required when creating a company profile."
                    for field in profile_fields
                    if field not in attrs
                }
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        profile_data = {
            field: validated_data.pop(field)
            for field in [
                "company_name",
                "company_description",
                "industry",
                "location",
                "contact_email",
                "contact_phone",
                "company_size",
            ]
            if field in validated_data
        }
        # Ensure role and student_id cannot be set by client and role is strictly COMPANY
        validated_data.pop("role", None)
        validated_data.pop("student_id", None)

        with transaction.atomic():
            user = User.objects.create_user(
                role=User.Role.COMPANY,
                password=password,
                **validated_data,
            )
            if profile_data:
                CompanyProfile.objects.create(user=user, **profile_data)
        return user


class TPORegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField(validators=[validate_email_address])
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        try:
            validate_password(
                attrs["password"],
                user=User(first_name=attrs["first_name"], last_name=attrs["last_name"], email=attrs["email"]),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(
            role=User.Role.TPO,
            password=password,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Accepts 'identifier' (which can be student_id or email) and 'password'.
    Returns JWT access and refresh tokens along with safe user info.
    """

    identifier = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Email address OR Student ID",
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        identifier = attrs.get("identifier", "").strip()
        password = attrs.get("password")

        if not identifier or not password:
            raise serializers.ValidationError(
                "Both identifier and password are required."
            )

        # Email-like identifiers must be valid emails; plain identifiers remain student IDs.
        user = None
        if "@" in identifier or any(char.isspace() for char in identifier):
            try:
                validate_email_address(identifier)
            except DjangoValidationError:
                raise serializers.ValidationError(
                    {"identifier": "Please enter a valid email address."}
                )
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(student_id__iexact=identifier).first()

        if user is None or not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid credentials. Please check your identifier and password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is currently inactive."
            )

        # Generate JWT Tokens
        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_email_address])
