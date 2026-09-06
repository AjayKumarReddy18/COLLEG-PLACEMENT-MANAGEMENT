import io
import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import CompanyProfile, StudentProfile

User = get_user_model()

# Use a temporary directory for media files during tests
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def _get_token(client, identifier, password):
    """Helper to login and return Bearer access token."""
    res = client.post(
        reverse("login"),
        {"identifier": identifier, "password": password},
    )
    return res.data["access"]


def _create_pdf_file(name="resume.pdf"):
    """Create a minimal fake PDF file for testing."""
    content = b"%PDF-1.4 test content"
    return SimpleUploadedFile(name, content, content_type="application/pdf")


def _create_docx_file(name="resume.docx"):
    """Create a minimal fake DOCX file for testing."""
    content = b"PK\x03\x04 fake docx content"
    return SimpleUploadedFile(
        name, content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


def _create_invalid_file(name="malware.exe"):
    """Create an invalid file type for testing."""
    content = b"MZ fake executable content"
    return SimpleUploadedFile(name, content, content_type="application/x-msdownload")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StudentProfileAPITests(TestCase):
    """Tests for GET/POST/PUT/PATCH /api/student/profile/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("student-profile")

        # Create student user and get token
        self.student = User.objects.create_user(
            email="student@college.edu",
            student_id="23CS001",
            password="StudentPass123!",
            first_name="Rahul",
            last_name="Sharma",
            phone_number="9876543210",
            role=User.Role.STUDENT,
        )
        self.student_token = _get_token(self.client, "23CS001", "StudentPass123!")

        # Create another student for isolation tests
        self.student2 = User.objects.create_user(
            email="student2@college.edu",
            student_id="23CS002",
            password="StudentPass123!",
            first_name="Priya",
            last_name="Patel",
            role=User.Role.STUDENT,
        )
        self.student2_token = _get_token(self.client, "23CS002", "StudentPass123!")

        # Create a company user
        self.company = User.objects.create_user(
            email="hr@company.com",
            password="CompanyPass123!",
            first_name="TechCorp",
            last_name="HR",
            role=User.Role.COMPANY,
        )
        self.company_token = _get_token(self.client, "hr@company.com", "CompanyPass123!")

        self.profile_payload = {
            "department": "Computer Science",
            "course": "B.Tech",
            "year": 4,
            "cgpa": "8.50",
            "skills": "Python, Django, React",
        }

    def test_student_create_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        response = self.client.post(self.url, self.profile_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("profile", response.data)
        self.assertEqual(response.data["profile"]["department"], "Computer Science")
        self.assertEqual(response.data["profile"]["course"], "B.Tech")
        self.assertEqual(response.data["profile"]["year"], 4)
        self.assertEqual(response.data["profile"]["cgpa"], "8.50")

    def test_student_get_own_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["department"], "Computer Science")
        self.assertEqual(response.data["student_id"], "23CS001")

    def test_student_update_profile_put(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        updated = self.profile_payload.copy()
        updated["cgpa"] = "9.00"
        updated["skills"] = "Python, Django, React, Docker"
        response = self.client.put(self.url, updated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profile"]["cgpa"], "9.00")

    def test_student_update_profile_patch(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.patch(self.url, {"skills": "Python, Machine Learning"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profile"]["skills"], "Python, Machine Learning")

    def test_student_add_instagram_url(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.patch(
            self.url, {"instagram_url": "https://www.instagram.com/rahul_sharma/"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["profile"]["instagram_url"],
            "https://www.instagram.com/rahul_sharma/",
        )

    def test_student_update_instagram_url(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        payload = self.profile_payload.copy()
        payload["instagram_url"] = "https://www.instagram.com/rahul_old/"
        self.client.post(self.url, payload)
        response = self.client.patch(
            self.url, {"instagram_url": "https://www.instagram.com/rahul_new/"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["profile"]["instagram_url"],
            "https://www.instagram.com/rahul_new/",
        )

    def test_student_remove_instagram_url(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        payload = self.profile_payload.copy()
        payload["instagram_url"] = "https://www.instagram.com/rahul/"
        self.client.post(self.url, payload)
        response = self.client.patch(self.url, {"instagram_url": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["profile"]["instagram_url"])

    def test_student_upload_valid_pdf_resume(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        resume_file = _create_pdf_file()
        response = self.client.patch(self.url, {"resume": resume_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resume", response.data["profile"])
        self.assertIsNotNone(response.data["profile"]["resume"])

    def test_student_upload_valid_docx_resume(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        resume_file = _create_docx_file()
        response = self.client.patch(self.url, {"resume": resume_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["profile"]["resume"])

    def test_student_invalid_resume_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        bad_file = _create_invalid_file()
        response = self.client.patch(self.url, {"resume": bad_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_access_company_profile_api(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        response = self.client.get(reverse("company-profile"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_student_profile_request(self):
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_access_other_student_profile(self):
        """Student A creates a profile. Student B should only see their own (or 404)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)

        # Student B tries GET: should get 404 (no profile for student2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student2_token}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_profile_creation_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.post(self.url, self.profile_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_profile_not_found_before_creation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CompanyProfileAPITests(TestCase):
    """Tests for GET/POST/PUT/PATCH /api/company/profile/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("company-profile")

        # Create company user and get token
        self.company = User.objects.create_user(
            email="hr@techcorp.com",
            password="CompanyPass123!",
            first_name="TechCorp",
            last_name="HR",
            phone_number="9123456789",
            role=User.Role.COMPANY,
        )
        self.company_token = _get_token(self.client, "hr@techcorp.com", "CompanyPass123!")

        # Another company for isolation
        self.company2 = User.objects.create_user(
            email="hr@othercorp.com",
            password="CompanyPass123!",
            first_name="OtherCorp",
            last_name="HR",
            role=User.Role.COMPANY,
        )
        self.company2_token = _get_token(self.client, "hr@othercorp.com", "CompanyPass123!")

        # Student for cross-role test
        self.student = User.objects.create_user(
            email="stu@college.edu",
            student_id="23CS099",
            password="StudentPass123!",
            first_name="Stu",
            last_name="Dent",
            role=User.Role.STUDENT,
        )
        self.student_token = _get_token(self.client, "stu@college.edu", "StudentPass123!")

        # TPO for cross-role test
        self.tpo = User.objects.create_user(
            email="tpo@college.edu",
            password="TpoPass123!",
            first_name="Officer",
            last_name="TPO",
            role=User.Role.TPO,
        )
        self.tpo_token = _get_token(self.client, "tpo@college.edu", "TpoPass123!")

        self.profile_payload = {
            "company_name": "TechCorp Pvt Ltd",
            "company_description": "Leading tech company",
            "industry": "Information Technology",
            "website": "https://techcorp.com",
            "location": "Bengaluru, India",
            "contact_email": "careers@techcorp.com",
            "contact_phone": "9123456789",
            "company_size": "201-1000",
        }

    def test_company_create_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        response = self.client.post(self.url, self.profile_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("profile", response.data)
        self.assertEqual(response.data["profile"]["company_name"], "TechCorp Pvt Ltd")
        self.assertEqual(response.data["profile"]["verification_status"], "PENDING")

    def test_company_get_own_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company_name"], "TechCorp Pvt Ltd")

    def test_company_update_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.patch(
            self.url, {"company_description": "Updated description"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["profile"]["company_description"], "Updated description"
        )

    def test_company_cannot_change_verification_status(self):
        """Company tries to set verification_status=APPROVED – must remain PENDING."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        payload = self.profile_payload.copy()
        payload["verification_status"] = "APPROVED"
        self.client.post(self.url, payload)
        profile = CompanyProfile.objects.get(user=self.company)
        self.assertEqual(profile.verification_status, "PENDING")

    def test_company_cannot_update_verification_status(self):
        """Company PATCH tries to change verification_status – must stay PENDING."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.patch(
            self.url, {"verification_status": "APPROVED"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = CompanyProfile.objects.get(user=self.company)
        self.assertEqual(profile.verification_status, "PENDING")

    def test_company_cannot_access_student_profile_api(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        response = self.client.get(reverse("student-profile"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_company_profile_request(self):
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_company_cannot_access_other_company_profile(self):
        """Company A creates profile. Company B only sees their own (or 404)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        self.client.post(self.url, self.profile_payload)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company2_token}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_company_profile_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token}")
        self.client.post(self.url, self.profile_payload)
        response = self.client.post(self.url, self.profile_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tpo_cannot_access_company_self_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_cannot_access_student_self_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(reverse("student-profile"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
