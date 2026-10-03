from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    CompanyRegistrationSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    StudentRegistrationSerializer,
    TPORegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


class StudentRegistrationView(generics.CreateAPIView):
    """
    Public endpoint for student registration.
    Assigns role = STUDENT automatically.
    """

    permission_classes = [AllowAny]
    serializer_class = StudentRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Student registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CompanyRegistrationView(generics.CreateAPIView):
    """
    Public endpoint for company registration.
    Assigns role = COMPANY automatically.
    """

    permission_classes = [AllowAny]
    serializer_class = CompanyRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Company registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TPORegistrationView(generics.CreateAPIView):
    """
    Public TPO registration.
    """

    permission_classes = [AllowAny]
    serializer_class = TPORegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "TPO registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(views.APIView):
    """
    Login endpoint.

    Student:
        Can login using Email OR Student ID.

    Company:
        Can login using Email.

    TPO:
        Can login using Email.

    Returns:
        Access token
        Refresh token
        User information
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )


class CurrentUserView(generics.RetrieveAPIView):
    """
    Returns the currently logged-in user's information.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(views.APIView):
    """
    Request a password reset link.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        serializer = PasswordResetRequestSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        email = (
            serializer.validated_data["email"]
            .strip()
            .lower()
        )

        generic_message = (
            "If an account exists for this email, "
            "a password reset link has been sent."
        )

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if user and user.is_active:

            token = PasswordResetTokenGenerator().make_token(
                user
            )

            reset_url = (
                "http://127.0.0.1:5501/reset-password.html"
                f"?email={quote(email)}"
                f"&token={quote(token)}"
            )

            send_mail(
                subject=(
                    "College Placement Management System "
                    "- Password Reset"
                ),
                message=(
                    "You have requested a password reset.\n\n"
                    f"Reset your password here:\n{reset_url}\n\n"
                    "If you did not request this, "
                    "you can ignore this email."
                ),
                from_email=getattr(
                    settings,
                    "DEFAULT_FROM_EMAIL",
                    "no-reply@collegeplacement.local",
                ),
                recipient_list=[user.email],
                fail_silently=True,
            )

        return Response(
            {"detail": generic_message},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(views.APIView):
    """
    Confirm password reset token and set a new password.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        email = (
            request.data.get("email") or ""
        ).strip().lower()

        token = (
            request.data.get("token") or ""
        ).strip()

        password = request.data.get("password")

        password_confirm = request.data.get(
            "password_confirm"
        )

        if (
            not email
            or not token
            or not password
            or not password_confirm
        ):
            return Response(
                {
                    "detail": (
                        "A valid email, reset token, "
                        "and password are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if (
            not user
            or not PasswordResetTokenGenerator().check_token(
                user,
                token,
            )
        ):
            return Response(
                {
                    "detail": (
                        "This password reset link is "
                        "invalid or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password != password_confirm:
            return Response(
                {
                    "detail": "Passwords do not match."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(
                password,
                user=user,
            )

        except ValidationError as exc:

            return Response(
                {
                    "detail": exc.messages[0]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)

        user.save(
            update_fields=["password"]
        )

        return Response(
            {
                "detail": (
                    "Password reset successful. "
                    "You can now sign in."
                )
            },
            status=status.HTTP_200_OK,
        )