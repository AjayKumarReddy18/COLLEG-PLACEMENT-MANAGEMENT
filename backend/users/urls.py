from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CompanyRegistrationView,
    CurrentUserView,
    LoginView,
    StudentRegistrationView,
)

urlpatterns = [
    path(
        "auth/register/student/",
        StudentRegistrationView.as_view(),
        name="register-student",
    ),
    path(
        "auth/register/company/",
        CompanyRegistrationView.as_view(),
        name="register-company",
    ),
    path(
        "auth/login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "auth/me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
]
