from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import CompanyProfile, JobApplication, JobListing, StudentProfile

User = get_user_model()


def _get_token(client, identifier, password):
    """Helper to login and return Bearer access token."""
    res = client.post(
        reverse("login"),
        {"identifier": identifier, "password": password},
    )
    return res.data["access"]


class Stage5JobAndApplicationAPITests(TestCase):
    """
    Comprehensive tests for Stage 5:
    - Company Job Posting & Management
    - TPO Job Review & Verification
    - Student Job Browsing
    - Automated Backend Eligibility Engine
    - Student Application Submission & Isolation
    - Company Applicant Review
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Setup TPO
        self.tpo_user = User.objects.create_user(
            email="tpo@college.edu",
            password="TpoPassword123!",
            first_name="College",
            last_name="TPO",
            role=User.Role.TPO,
        )
        self.tpo_token = _get_token(self.client, "tpo@college.edu", "TpoPassword123!")

        # 2. Setup Company A (TechCorp)
        self.company_user_a = User.objects.create_user(
            email="hr@techcorp.com",
            password="CompanyPass123!",
            first_name="TechCorp",
            last_name="HR",
            role=User.Role.COMPANY,
        )
        self.company_token_a = _get_token(self.client, "hr@techcorp.com", "CompanyPass123!")
        self.company_profile_a = CompanyProfile.objects.create(
            user=self.company_user_a,
            company_name="TechCorp Inc.",
            industry="IT",
            location="Bengaluru",
            contact_email="hr@techcorp.com",
            verification_status=CompanyProfile.VerificationStatus.APPROVED,
        )

        # 3. Setup Company B (FinanceHub)
        self.company_user_b = User.objects.create_user(
            email="recruiter@financehub.com",
            password="CompanyPass123!",
            first_name="FinanceHub",
            last_name="Lead",
            role=User.Role.COMPANY,
        )
        self.company_token_b = _get_token(self.client, "recruiter@financehub.com", "CompanyPass123!")
        self.company_profile_b = CompanyProfile.objects.create(
            user=self.company_user_b,
            company_name="FinanceHub LLC",
            industry="Finance",
            location="Mumbai",
            contact_email="recruiter@financehub.com",
            verification_status=CompanyProfile.VerificationStatus.APPROVED,
        )

        # 4. Setup Eligible Student (Computer Science, 8.5 CGPA)
        self.student_user_1 = User.objects.create_user(
            email="student1@college.edu",
            student_id="23CS001",
            password="StudentPass123!",
            first_name="Rahul",
            last_name="Sharma",
            role=User.Role.STUDENT,
        )
        self.student_token_1 = _get_token(self.client, "23CS001", "StudentPass123!")
        self.student_profile_1 = StudentProfile.objects.create(
            user=self.student_user_1,
            department="Computer Science",
            course="B.Tech",
            year=4,
            cgpa=Decimal("8.50"),
            skills="Python, Django, React",
        )

        # 5. Setup Ineligible Student (Mechanical, 6.5 CGPA)
        self.student_user_2 = User.objects.create_user(
            email="student2@college.edu",
            student_id="23ME002",
            password="StudentPass123!",
            first_name="Vikas",
            last_name="Verma",
            role=User.Role.STUDENT,
        )
        self.student_token_2 = _get_token(self.client, "23ME002", "StudentPass123!")
        self.student_profile_2 = StudentProfile.objects.create(
            user=self.student_user_2,
            department="Mechanical Engineering",
            course="B.Tech",
            year=4,
            cgpa=Decimal("6.50"),
            skills="AutoCAD",
        )

        # 6. Future deadline helper
        self.future_deadline = timezone.now() + timedelta(days=30)
        self.past_deadline = timezone.now() - timedelta(days=5)

        # 7. Common endpoints
        self.company_jobs_url = reverse("company-job-list")
        self.tpo_jobs_url = reverse("tpo-job-list")
        self.student_jobs_url = reverse("student-job-list")
        self.student_apps_url = reverse("student-application-list")

    # =========================================================================
    # TASK 2 & 13: COMPANY JOB CREATION TESTS
    # =========================================================================

    def test_company_can_create_job(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        payload = {
            "job_title": "Software Engineer",
            "description": "Python & Django Backend Role",
            "job_type": "FULL_TIME",
            "salary": "1200000.00",
            "job_location": "Bengaluru",
            "minimum_cgpa": "7.50",
            "eligible_departments": ["Computer Science", "Information Technology"],
            "application_deadline": self.future_deadline.isoformat(),
        }
        response = self.client.post(self.company_jobs_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["job"]["job_title"], "Software Engineer")
        self.assertEqual(response.data["job"]["company_name"], "TechCorp Inc.")
        # Status defaults to PENDING_TPO_APPROVAL
        self.assertEqual(response.data["job"]["status"], "PENDING_TPO_APPROVAL")

    def test_student_cannot_create_job(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        payload = {
            "job_title": "Hacker",
            "description": "Unauthorized creation",
            "job_location": "Remote",
            "application_deadline": self.future_deadline.isoformat(),
        }
        response = self.client.post(self.company_jobs_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_cannot_create_company_job(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.post(self.company_jobs_url, {"job_title": "Test"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_job(self):
        response = self.client.post(self.company_jobs_url, {"job_title": "Test"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_company_cannot_directly_create_approved_job(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        payload = {
            "job_title": "Sneaky Job",
            "description": "Trying to bypass TPO approval",
            "job_location": "Bengaluru",
            "application_deadline": self.future_deadline.isoformat(),
            "status": "APPROVED",
        }
        response = self.client.post(self.company_jobs_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_job_creation_validates_future_deadline(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        payload = {
            "job_title": "Expired Job",
            "description": "Deadlines in the past are rejected",
            "job_location": "Delhi",
            "application_deadline": self.past_deadline.isoformat(),
        }
        response = self.client.post(self.company_jobs_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_job_creation_validates_cgpa_bounds(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        payload = {
            "job_title": "Out of bounds CGPA",
            "description": "Invalid CGPA",
            "job_location": "Hyderabad",
            "minimum_cgpa": "15.00",
            "application_deadline": self.future_deadline.isoformat(),
        }
        response = self.client.post(self.company_jobs_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # TASK 3 & 13: COMPANY JOB MANAGEMENT & DATA ISOLATION
    # =========================================================================

    def test_company_can_list_only_its_own_jobs(self):
        # Create 1 job for Company A and 1 job for Company B
        job_a = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="DevOps Engineer",
            description="Docker & K8s",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
        )
        JobListing.objects.create(
            company=self.company_profile_b,
            job_title="Financial Analyst",
            description="Valuation & Modeling",
            job_location="Mumbai",
            application_deadline=self.future_deadline,
        )

        # Company A lists jobs
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        response = self.client.get(self.company_jobs_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["job_title"], "DevOps Engineer")

    def test_company_cannot_access_another_company_job_detail(self):
        job_b = JobListing.objects.create(
            company=self.company_profile_b,
            job_title="Risk Manager",
            description="Secret job",
            job_location="Mumbai",
            application_deadline=self.future_deadline,
        )

        # Company A attempts to view Company B's job detail
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-job-detail", kwargs={"pk": job_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_company_can_update_its_own_job(self):
        job_a = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="QA Intern",
            description="Testing web apps",
            job_location="Remote",
            application_deadline=self.future_deadline,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-job-detail", kwargs={"pk": job_a.id})
        response = self.client.patch(url, {"job_title": "Lead QA Engineer"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job"]["job_title"], "Lead QA Engineer")

    def test_company_cannot_approve_its_own_job_on_update(self):
        job_a = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Junior Dev",
            description="Needs TPO signoff",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.PENDING_TPO_APPROVAL,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-job-detail", kwargs={"pk": job_a.id})
        response = self.client.patch(url, {"status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # TASK 4, 5 & 13: TPO JOB MANAGEMENT & APPROVAL TESTS
    # =========================================================================

    def test_tpo_can_list_and_filter_jobs(self):
        JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Pending Job 1",
            description="Pending description",
            job_location="Pune",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.PENDING_TPO_APPROVAL,
        )
        JobListing.objects.create(
            company=self.company_profile_b,
            job_title="Approved Job 2",
            description="Approved description",
            job_location="Delhi",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")

        # List all
        res_all = self.client.get(self.tpo_jobs_url)
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data), 2)

        # Filter by PENDING_TPO_APPROVAL
        res_pending = self.client.get(f"{self.tpo_jobs_url}?status=PENDING_TPO_APPROVAL")
        self.assertEqual(res_pending.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_pending.data), 1)
        self.assertEqual(res_pending.data[0]["job_title"], "Pending Job 1")

    def test_tpo_can_approve_job(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Backend Intern",
            description="Needs verification",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.PENDING_TPO_APPROVAL,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-job-verify", kwargs={"pk": job.id})
        payload = {
            "status": "APPROVED",
            "remarks": "Job compensation and requirements verified.",
        }
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job"]["status"], "APPROVED")
        self.assertEqual(response.data["job"]["approval_remarks"], "Job compensation and requirements verified.")

        job.refresh_from_db()
        self.assertEqual(job.status, JobListing.JobStatus.APPROVED)

    def test_tpo_can_reject_job(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Suspicious Role",
            description="Bad details",
            job_location="Nowhere",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.PENDING_TPO_APPROVAL,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-job-verify", kwargs={"pk": job.id})
        payload = {
            "status": "REJECTED",
            "remarks": "Role details violate campus hiring policy.",
        }
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job.refresh_from_db()
        self.assertEqual(job.status, JobListing.JobStatus.REJECTED)

    def test_student_and_company_cannot_approve_jobs(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Security Audit Role",
            description="Test",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
        )
        url = reverse("tpo-job-verify", kwargs={"pk": job.id})

        # Student attempt
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        self.assertEqual(self.client.patch(url, {"status": "APPROVED"}).status_code, status.HTTP_403_FORBIDDEN)

        # Company attempt
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        self.assertEqual(self.client.patch(url, {"status": "APPROVED"}).status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # TASK 6, 7 & 13: STUDENT JOB BROWSING & ELIGIBILITY ENGINE
    # =========================================================================

    def test_student_can_only_see_approved_jobs(self):
        # 1 Approved, 1 Pending, 1 Rejected
        JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Approved Cloud Role",
            description="Good job",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )
        JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Pending Draft",
            description="Draft",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.PENDING_TPO_APPROVAL,
        )
        JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Rejected Role",
            description="Rejected",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.REJECTED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        response = self.client.get(self.student_jobs_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["job_title"], "Approved Cloud Role")

    def test_eligibility_computation_in_student_job_listing(self):
        # Job requires 8.0 CGPA and CSE department
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="SDE-1",
            description="Top tier role",
            job_location="Bengaluru",
            minimum_cgpa=Decimal("8.00"),
            eligible_departments=["Computer Science"],
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        # Student 1 (CS, 8.5 CGPA) -> Eligible
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        res1 = self.client.get(self.student_jobs_url)
        self.assertTrue(res1.data[0]["is_eligible"])
        self.assertEqual(len(res1.data[0]["eligibility_reasons"]), 0)

        # Student 2 (Mech, 6.5 CGPA) -> Ineligible (both CGPA and Dept)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_2}")
        res2 = self.client.get(self.student_jobs_url)
        self.assertFalse(res2.data[0]["is_eligible"])
        self.assertEqual(len(res2.data[0]["eligibility_reasons"]), 2)

    # =========================================================================
    # TASK 8, 9, 10, 11 & 13: APPLICATION PIPELINE & VALIDATIONS
    # =========================================================================

    def test_eligible_student_can_apply_successfully(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Software Developer",
            description="Python stack",
            job_location="Bengaluru",
            minimum_cgpa=Decimal("7.00"),
            eligible_departments=["Computer Science"],
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        apply_url = reverse("student-job-apply", kwargs={"pk": job.id})
        response = self.client.post(apply_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["application"]["job_title"], "Software Developer")
        self.assertEqual(response.data["application"]["company_name"], "TechCorp Inc.")
        self.assertEqual(response.data["application"]["status"], "APPLIED")

    def test_student_cannot_apply_with_insufficient_cgpa(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Elite Quant",
            description="Requires 9.0 CGPA",
            job_location="Mumbai",
            minimum_cgpa=Decimal("9.00"),  # Student 1 only has 8.50
            eligible_departments=["Computer Science"],
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        apply_url = reverse("student-job-apply", kwargs={"pk": job.id})
        response = self.client.post(apply_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("CGPA", response.data["detail"])

    def test_student_cannot_apply_with_ineligible_department(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Design Engineer",
            description="Mechanical role only",
            job_location="Chennai",
            minimum_cgpa=Decimal("6.00"),
            eligible_departments=["Mechanical Engineering"],
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        # Student 1 is in Computer Science
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        apply_url = reverse("student-job-apply", kwargs={"pk": job.id})
        response = self.client.post(apply_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("department", response.data["detail"])

    def test_student_cannot_apply_after_deadline_expired(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Past Deadline Job",
            description="Expired",
            job_location="Bengaluru",
            minimum_cgpa=Decimal("6.00"),
            application_deadline=self.past_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        apply_url = reverse("student-job-apply", kwargs={"pk": job.id})
        response = self.client.post(apply_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("deadline", response.data["detail"])

    def test_student_cannot_apply_to_unapproved_job(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Pending Job",
            description="Not approved yet",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.PENDING_TPO_APPROVAL,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        apply_url = reverse("student-job-apply", kwargs={"pk": job.id})
        response = self.client.post(apply_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("approved", response.data["detail"])

    def test_student_cannot_apply_twice_to_same_job(self):
        job = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Single Application Role",
            description="Apply once only",
            job_location="Bengaluru",
            minimum_cgpa=Decimal("6.00"),
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        apply_url = reverse("student-job-apply", kwargs={"pk": job.id})

        # First application succeeds
        res1 = self.client.post(apply_url)
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second application rejected
        res2 = self.client.post(apply_url)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already applied", res2.data["detail"])

    def test_student_can_list_own_applications_with_isolation(self):
        job_1 = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Job One",
            description="Description",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )
        job_2 = JobListing.objects.create(
            company=self.company_profile_b,
            job_title="Job Two",
            description="Description",
            job_location="Mumbai",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )

        # Student 1 applies to Job 1
        JobApplication.objects.create(student=self.student_profile_1, job=job_1)
        # Student 2 applies to Job 2
        JobApplication.objects.create(student=self.student_profile_2, job=job_2)

        # Student 1 checks applications
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        res = self.client.get(self.student_apps_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["job_title"], "Job One")

    def test_company_can_view_applicants_for_own_job_only(self):
        job_a = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Company A Role",
            description="Test",
            job_location="Bengaluru",
            application_deadline=self.future_deadline,
            status=JobListing.JobStatus.APPROVED,
        )
        JobApplication.objects.create(student=self.student_profile_1, job=job_a)

        applicants_url = reverse("company-job-applications", kwargs={"pk": job_a.id})

        # Company A views its applicants -> Success
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        res_a = self.client.get(applicants_url)
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_a.data), 1)
        self.assertEqual(res_a.data[0]["student_id"], "23CS001")
        self.assertEqual(res_a.data[0]["student_name"], "Rahul Sharma")

        # Company B tries to view Company A's applicants -> 403 Forbidden
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_b}")
        res_b = self.client.get(applicants_url)
        self.assertEqual(res_b.status_code, status.HTTP_403_FORBIDDEN)

        # Student tries to view company applicants -> 403 Forbidden
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        res_s = self.client.get(applicants_url)
        self.assertEqual(res_s.status_code, status.HTTP_403_FORBIDDEN)
