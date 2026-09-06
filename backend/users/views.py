from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    CompanyRegistrationSerializer,
    LoginSerializer,
    StudentRegistrationSerializer,
    UserSerializer,
)


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


class LoginView(views.APIView):
    """
    Public authentication endpoint supporting:
    - Student login via either Email OR Student ID
    - Company / TPO login via Email
    Returns JWT access and refresh tokens along with user information.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveAPIView):
    """
    Protected endpoint to retrieve details of the currently authenticated user.
    Strictly isolated: users can only view their own profile.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
