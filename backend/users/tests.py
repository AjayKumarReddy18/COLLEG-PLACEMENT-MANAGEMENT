from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from users.permissions import IsCompany, IsStudent, IsTPO

User = get_user_model()


class UserModelTests(TestCase):
    """Preserved Stage 1 unit tests for custom User model."""

    def test_create_student_user(self):
        """Test creating a student user with valid role and password hashing."""
        student = User.objects.create_user(
            email="student1@college.edu",
            password="StrongPassword123!",
            student_id="STU2026001",
            first_name="Rahul",
            last_name="Sharma",
            phone_number="9876543210",
            role=User.Role.STUDENT,
        )
        self.assertEqual(student.email, "student1@college.edu")
        self.assertEqual(student.student_id, "STU2026001")
        self.assertEqual(student.role, "STUDENT")
        self.assertTrue(student.is_active)
        self.assertFalse(student.is_staff)
        # Password must NOT be plain text
        self.assertNotEqual(student.password, "StrongPassword123!")
        self.assertTrue(student.check_password("StrongPassword123!"))
        self.assertFalse(student.check_password("WrongPassword"))

    def test_create_company_user(self):
        """Test creating a company user."""
        company = User.objects.create_user(
            email="hr@techcorp.com",
            password="CompanyPassword123!",
            first_name="TechCorp",
            last_name="HR",
            phone_number="9123456780",
            role=User.Role.COMPANY,
        )
        self.assertEqual(company.role, "COMPANY")
        self.assertIsNone(company.student_id)
        self.assertTrue(company.check_password("CompanyPassword123!"))

    def test_create_tpo_user(self):
        """Test creating a TPO user."""
        tpo = User.objects.create_user(
            email="tpo@college.edu",
            password="TpoPassword123!",
            first_name="Placement",
            last_name="Officer",
            phone_number="9000000000",
            role=User.Role.TPO,
        )
        self.assertEqual(tpo.role, "TPO")
        self.assertTrue(tpo.check_password("TpoPassword123!"))

    def test_invalid_role_rejected(self):
        """Test that invalid roles such as 'ADMIN' are rejected."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="admin@college.edu",
                password="AdminPassword123!",
                first_name="Admin",
                last_name="User",
                role="ADMIN",  # Invalid role - Only STUDENT, COMPANY, TPO are allowed
            )

    def test_duplicate_email_rejected(self):
        """Test that duplicate email addresses raise an IntegrityError."""
        User.objects.create_user(
            email="duplicate@college.edu",
            password="Pass1",
            first_name="User",
            last_name="One",
            role=User.Role.STUDENT,
        )
        with self.assertRaises(IntegrityError):
            User.objects.create(
                email="duplicate@college.edu",
                first_name="User",
                last_name="Two",
                role=User.Role.STUDENT,
            )

    def test_superuser_creation(self):
        """Test superuser creation for Django Admin staff access."""
        admin_user = User.objects.create_superuser(
            email="tpo_lead@college.edu",
            password="SuperPassword123!",
            first_name="Lead",
            last_name="TPO",
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, User.Role.TPO)


class StudentRegistrationAPITests(TestCase):
    """Tests for POST /api/auth/register/student/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("register-student")
        self.valid_payload = {
            "email": "student@college.edu",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "student_id": "23CS001",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "9876543210",
        }

    def test_student_registration_success(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["role"], "STUDENT")
        self.assertEqual(response.data["user"]["email"], "student@college.edu")
        self.assertEqual(response.data["user"]["student_id"], "23CS001")
        # Ensure password is NOT returned in response
        self.assertNotIn("password", response.data["user"])

        # Check DB state and password hashing
        user = User.objects.get(email="student@college.edu")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertNotEqual(user.password, "SecurePassword123!")
        self.assertTrue(user.check_password("SecurePassword123!"))

    def test_duplicate_email_rejected(self):
        self.client.post(self.url, self.valid_payload)
        payload = self.valid_payload.copy()
        payload["student_id"] = "23CS002"  # Different ID, same email
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_duplicate_student_id_rejected(self):
        self.client.post(self.url, self.valid_payload)
        payload = self.valid_payload.copy()
        payload["email"] = "student2@college.edu"  # Different email, same ID
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("student_id", response.data)

    def test_password_confirmation_mismatch(self):
        payload = self.valid_payload.copy()
        payload["password_confirm"] = "DifferentPassword123!"
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_weak_password_rejected(self):
        payload = self.valid_payload.copy()
        payload["password"] = "123"
        payload["password_confirm"] = "123"
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_cannot_assign_tpo_role(self):
        payload = self.valid_payload.copy()
        payload["role"] = "TPO"
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="student@college.edu")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertNotEqual(user.role, "TPO")


class CompanyRegistrationAPITests(TestCase):
    """Tests for POST /api/auth/register/company/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("register-company")
        self.valid_payload = {
            "email": "hr@innovate.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "first_name": "Innovate",
            "last_name": "Tech",
            "phone_number": "9123456789",
        }

    def test_company_registration_success(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["role"], "COMPANY")
        self.assertEqual(response.data["user"]["email"], "hr@innovate.com")
        self.assertIsNone(response.data["user"]["student_id"])
        self.assertNotIn("password", response.data["user"])

        user = User.objects.get(email="hr@innovate.com")
        self.assertEqual(user.role, User.Role.COMPANY)
        self.assertTrue(user.check_password("SecurePassword123!"))

    def test_company_duplicate_email_rejected(self):
        self.client.post(self.url, self.valid_payload)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_company_cannot_assign_tpo_role_or_student_id(self):
        payload = self.valid_payload.copy()
        payload["role"] = "TPO"
        payload["student_id"] = "STU999"
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="hr@innovate.com")
        self.assertEqual(user.role, User.Role.COMPANY)
        self.assertIsNone(user.student_id)


class LoginAPITests(TestCase):
    """Tests for POST /api/auth/login/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")

        # Setup Student
        self.student = User.objects.create_user(
            email="student@college.edu",
            student_id="23CS101",
            password="StudentPass123!",
            first_name="Jane",
            last_name="Doe",
            role=User.Role.STUDENT,
        )

        # Setup Company
        self.company = User.objects.create_user(
            email="recruiter@company.com",
            password="CompanyPass123!",
            first_name="Recruiter",
            last_name="One",
            role=User.Role.COMPANY,
        )

        # Setup TPO
        self.tpo = User.objects.create_user(
            email="tpo@college.edu",
            password="TpoPass123!",
            first_name="Officer",
            last_name="Lead",
            role=User.Role.TPO,
        )

    def test_student_login_with_student_id(self):
        response = self.client.post(
            self.url,
            {"identifier": "23CS101", "password": "StudentPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["role"], "STUDENT")
        self.assertEqual(response.data["user"]["student_id"], "23CS101")
        self.assertNotIn("password", response.data["user"])

    def test_student_login_with_email(self):
        response = self.client.post(
            self.url,
            {"identifier": "student@college.edu", "password": "StudentPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["role"], "STUDENT")
        self.assertEqual(response.data["user"]["email"], "student@college.edu")

    def test_company_login_with_email(self):
        response = self.client.post(
            self.url,
            {"identifier": "recruiter@company.com", "password": "CompanyPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["role"], "COMPANY")

    def test_tpo_login_with_email(self):
        response = self.client.post(
            self.url,
            {"identifier": "tpo@college.edu", "password": "TpoPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["role"], "TPO")

    def test_incorrect_password_rejected(self):
        response = self.client.post(
            self.url,
            {"identifier": "23CS101", "password": "WrongPassword!"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_identifier_rejected(self):
        response = self.client.post(
            self.url,
            {"identifier": "nonexistent@college.edu", "password": "AnyPassword!"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_rejected(self):
        self.student.is_active = False
        self.student.save()
        response = self.client.post(
            self.url,
            {"identifier": "23CS101", "password": "StudentPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAndCurrentUserAPITests(TestCase):
    """Tests for JWT token refresh and GET /api/auth/me/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="student_jwt@college.edu",
            student_id="23CS201",
            password="ValidPassword123!",
            first_name="Alice",
            last_name="Smith",
            phone_number="9876543210",
            role=User.Role.STUDENT,
        )
        login_res = self.client.post(
            reverse("login"),
            {"identifier": "23CS201", "password": "ValidPassword123!"},
        )
        self.access_token = login_res.data["access"]
        self.refresh_token = login_res.data["refresh"]

    def test_current_user_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "student_jwt@college.edu")
        self.assertEqual(response.data["student_id"], "23CS201")
        self.assertEqual(response.data["role"], "STUDENT")
        self.assertNotIn("password", response.data)

    def test_current_user_unauthenticated(self):
        self.client.credentials()  # No credentials
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_xyz")
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        response = self.client.post(
            reverse("token-refresh"),
            {"refresh": self.refresh_token},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class RolePermissionTests(TestCase):
    """Tests for IsStudent, IsCompany, and IsTPO permission classes."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.student = User.objects.create_user(
            email="stu_perm@college.edu",
            student_id="PERM01",
            password="Password123!",
            role=User.Role.STUDENT,
        )
        self.company = User.objects.create_user(
            email="comp_perm@company.com",
            password="Password123!",
            role=User.Role.COMPANY,
        )
        self.tpo = User.objects.create_user(
            email="tpo_perm@college.edu",
            password="Password123!",
            role=User.Role.TPO,
        )

        self.is_student = IsStudent()
        self.is_company = IsCompany()
        self.is_tpo = IsTPO()

    def test_student_permissions(self):
        request = self.factory.get("/")
        request.user = self.student
        self.assertTrue(self.is_student.has_permission(request, None))
        self.assertFalse(self.is_company.has_permission(request, None))
        self.assertFalse(self.is_tpo.has_permission(request, None))

    def test_company_permissions(self):
        request = self.factory.get("/")
        request.user = self.company
        self.assertFalse(self.is_student.has_permission(request, None))
        self.assertTrue(self.is_company.has_permission(request, None))
        self.assertFalse(self.is_tpo.has_permission(request, None))

    def test_tpo_permissions(self):
        request = self.factory.get("/")
        request.user = self.tpo
        self.assertFalse(self.is_student.has_permission(request, None))
        self.assertFalse(self.is_company.has_permission(request, None))
        self.assertTrue(self.is_tpo.has_permission(request, None))

    def test_unauthenticated_permissions(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.is_student.has_permission(request, None))
        self.assertFalse(self.is_company.has_permission(request, None))
        self.assertFalse(self.is_tpo.has_permission(request, None))
