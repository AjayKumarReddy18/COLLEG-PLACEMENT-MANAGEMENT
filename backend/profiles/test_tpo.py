from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import CompanyProfile, StudentProfile

User = get_user_model()


def _get_token(client, identifier, password):
    """Helper to login and return Bearer access token."""
    res = client.post(
        reverse("login"),
        {"identifier": identifier, "password": password},
    )
    return res.data["access"]


class TPOMigratedAPITests(TestCase):
    """
    Comprehensive tests for Stage 4 TPO Management APIs:
    - Permissions (TPO vs Student vs Company vs Unauthenticated)
    - Company list & detail
    - Company verification & remarks
    - Student management & filtering
    """

    def setUp(self):
        self.client = APIClient()

        # Create TPO User
        self.tpo_user = User.objects.create_user(
            email="tpo@college.edu",
            password="TpoPassword123!",
            first_name="Admin",
            last_name="TPO",
            role=User.Role.TPO,
        )
        self.tpo_token = _get_token(self.client, "tpo@college.edu", "TpoPassword123!")

        # Create Student User & Profile
        self.student_user = User.objects.create_user(
            email="student@college.edu",
            student_id="23CS001",
            password="StudentPass123!",
            first_name="Rahul",
            last_name="Sharma",
            role=User.Role.STUDENT,
        )
        self.student_token = _get_token(self.client, "23CS001", "StudentPass123!")
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            department="Computer Science",
            course="B.Tech",
            year=4,
            cgpa=Decimal("8.50"),
            skills="Python, Django, React",
        )

        # Create Second Student (for filtering tests)
        self.student2_user = User.objects.create_user(
            email="student2@college.edu",
            student_id="23ME002",
            password="StudentPass123!",
            first_name="Vikas",
            last_name="Verma",
            role=User.Role.STUDENT,
        )
        self.student2_token = _get_token(self.client, "23ME002", "StudentPass123!")
        self.student2_profile = StudentProfile.objects.create(
            user=self.student2_user,
            department="Mechanical Engineering",
            course="Diploma",
            year=3,
            cgpa=Decimal("6.75"),
            skills="AutoCAD, SolidWorks",
        )

        # Create Company User & Profile
        self.company_user = User.objects.create_user(
            email="hr@techcorp.com",
            password="CompanyPass123!",
            first_name="TechCorp",
            last_name="HR",
            role=User.Role.COMPANY,
        )
        self.company_token = _get_token(self.client, "hr@techcorp.com", "CompanyPass123!")
        self.company_profile = CompanyProfile.objects.create(
            user=self.company_user,
            company_name="TechCorp Inc.",
            company_description="Leading IT Solutions",
            industry="Information Technology",
            website="https://techcorp.com",
            location="Bengaluru",
            contact_email="hr@techcorp.com",
            verification_status=CompanyProfile.VerificationStatus.PENDING,
        )

        # Create Second Company (Approved)
        self.company2_user = User.objects.create_user(
            email="contact@financehub.com",
            password="CompanyPass123!",
            first_name="FinanceHub",
            last_name="Recruiter",
            role=User.Role.COMPANY,
        )
        self.company2_profile = CompanyProfile.objects.create(
            user=self.company2_user,
            company_name="FinanceHub LLC",
            company_description="Global Investment Bank",
            industry="Finance",
            website="https://financehub.com",
            location="Mumbai",
            contact_email="contact@financehub.com",
            verification_status=CompanyProfile.VerificationStatus.APPROVED,
        )

        # Endpoint URLs
        self.company_list_url = reverse("tpo-company-list")
        self.student_list_url = reverse("tpo-student-list")

    # =========================================================================
    # PERMISSION TESTS
    # =========================================================================

    def test_unauthenticated_cannot_access_tpo_company_list(self):
        response = self.client.get(self.company_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_access_tpo_company_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        response = self.client.get(self.company_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_company_cannot_access_tpo_company_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        response = self.client.get(self.company_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_can_access_tpo_company_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(self.company_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_unauthenticated_cannot_access_tpo_company_detail(self):
        url = reverse("tpo-company-detail", kwargs={"pk": self.company_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_access_tpo_company_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        url = reverse("tpo-company-detail", kwargs={"pk": self.company_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_company_cannot_access_tpo_company_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        url = reverse("tpo-company-detail", kwargs={"pk": self.company_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_can_access_tpo_company_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-company-detail", kwargs={"pk": self.company_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company_name"], "TechCorp Inc.")
        self.assertEqual(response.data["user_email"], "hr@techcorp.com")
        self.assertEqual(response.data["verification_status"], "PENDING")

    def test_company_cannot_verify_itself(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        url = reverse("tpo-company-verify", kwargs={"pk": self.company_profile.id})
        response = self.client.patch(url, {"verification_status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_verify_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        url = reverse("tpo-company-verify", kwargs={"pk": self.company_profile.id})
        response = self.client.patch(url, {"verification_status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_tpo_students(self):
        response = self.client.get(self.student_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_access_tpo_students(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        response = self.client.get(self.student_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_company_cannot_access_tpo_students(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        response = self.client.get(self.student_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_can_access_tpo_students(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(self.student_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # =========================================================================
    # COMPANY VERIFICATION TESTS
    # =========================================================================

    def test_tpo_can_approve_pending_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-company-verify", kwargs={"pk": self.company_profile.id})
        payload = {
            "verification_status": "APPROVED",
            "remarks": "Company documentation is verified and authentic.",
        }
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company"]["verification_status"], "APPROVED")
        self.assertEqual(
            response.data["company"]["verification_remarks"],
            "Company documentation is verified and authentic.",
        )

        # Verify DB persistence
        self.company_profile.refresh_from_db()
        self.assertEqual(self.company_profile.verification_status, "APPROVED")
        self.assertEqual(
            self.company_profile.verification_remarks,
            "Company documentation is verified and authentic.",
        )

    def test_tpo_can_reject_pending_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-company-verify", kwargs={"pk": self.company_profile.id})
        payload = {
            "verification_status": "REJECTED",
            "remarks": "Registration documents are invalid or unverifiable.",
        }
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company"]["verification_status"], "REJECTED")

        # Verify DB persistence
        self.company_profile.refresh_from_db()
        self.assertEqual(self.company_profile.verification_status, "REJECTED")
        self.assertEqual(
            self.company_profile.verification_remarks,
            "Registration documents are invalid or unverifiable.",
        )

    def test_invalid_verification_status_is_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-company-verify", kwargs={"pk": self.company_profile.id})

        # Test PENDING is rejected in verify API (can only APPROVE or REJECT)
        response = self.client.patch(url, {"verification_status": "PENDING"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test arbitrary status string
        response = self.client.patch(url, {"verification_status": "CONFIRMED"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_nonexistent_company_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-company-verify", kwargs={"pk": 99999})
        response = self.client.patch(url, {"verification_status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_nonexistent_company_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-company-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # COMPANY FILTERING TESTS
    # =========================================================================

    def test_filter_companies_by_verification_status_pending(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(f"{self.company_list_url}?verification_status=PENDING")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["company_name"], "TechCorp Inc.")

    def test_filter_companies_by_verification_status_approved(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(f"{self.company_list_url}?verification_status=approved")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["company_name"], "FinanceHub LLC")

    def test_filter_companies_by_invalid_status_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(f"{self.company_list_url}?verification_status=INVALID_STATUS")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # STUDENT MANAGEMENT & FILTERING TESTS
    # =========================================================================

    def test_filter_students_by_department(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(f"{self.student_list_url}?department=Computer")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["student_id"], "23CS001")

    def test_filter_students_by_course(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(f"{self.student_list_url}?course=Diploma")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["student_id"], "23ME002")

    def test_filter_students_by_min_cgpa(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")

        # min_cgpa=8.0 should only return Rahul (8.50)
        response = self.client.get(f"{self.student_list_url}?min_cgpa=8.0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["student_id"], "23CS001")

        # min_cgpa=6.0 should return both Rahul (8.50) and Vikas (6.75)
        response = self.client.get(f"{self.student_list_url}?min_cgpa=6.0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # min_cgpa=9.0 should return empty list
        response = self.client.get(f"{self.student_list_url}?min_cgpa=9.0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filter_students_by_invalid_cgpa_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")

        # Non-numeric
        response = self.client.get(f"{self.student_list_url}?min_cgpa=high")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Out of bounds (>10)
        response = self.client.get(f"{self.student_list_url}?min_cgpa=15.0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
