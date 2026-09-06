from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

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
    student_id = serializers.CharField(
        required=True,
        max_length=50,
        help_text="Unique Student or College ID",
    )

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
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def validate_student_id(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Student ID cannot be blank.")
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

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        # Ensure role cannot be set by client and is strictly STUDENT
        validated_data.pop("role", None)

        user = User.objects.create_user(
            role=User.Role.STUDENT,
            password=password,
            **validated_data,
        )
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

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        # Ensure role and student_id cannot be set by client and role is strictly COMPANY
        validated_data.pop("role", None)
        validated_data.pop("student_id", None)

        user = User.objects.create_user(
            role=User.Role.COMPANY,
            password=password,
            **validated_data,
        )
        return user


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

        # Attempt to find user by email or student_id
        user = None
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            # First attempt: search by student_id
            user = User.objects.filter(student_id__iexact=identifier).first()
            # Fallback: search by email (if user typed email without @ or as username)
            if not user:
                user = User.objects.filter(email__iexact=identifier).first()

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
