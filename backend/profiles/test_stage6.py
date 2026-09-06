from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import (
    CompanyProfile,
    Interview,
    JobApplication,
    JobListing,
    JobOffer,
    PlacementRecord,
    StudentProfile,
)

User = get_user_model()


def _get_token(client, identifier, password):
    """Helper to login and return Bearer access token."""
    res = client.post(
        reverse("login"),
        {"identifier": identifier, "password": password},
    )
    return res.data["access"]


class Stage6WorkflowAPITests(TestCase):
    """
    Comprehensive automated test suite for Stage 6:
    - Application Status Updates & Transition Rules
    - Interview Scheduling, Management & Student Viewing
    - Job Offer Issuance, Viewing & Response
    - Automatic Placement Record Creation
    - TPO Placements Directory & Placement Analytics Summary
    - Strict Security, Role, and Data Isolation
    """

    def setUp(self):
        self.client = APIClient()

        # 1. TPO User
        self.tpo_user = User.objects.create_user(
            email="tpo@college.edu",
            password="TpoPassword123!",
            first_name="Placement",
            last_name="Director",
            role=User.Role.TPO,
        )
        self.tpo_token = _get_token(self.client, "tpo@college.edu", "TpoPassword123!")

        # 2. Company A (Apex Corp)
        self.company_user_a = User.objects.create_user(
            email="hr@apex.com",
            password="CompanyPass123!",
            first_name="Apex",
            last_name="HR",
            role=User.Role.COMPANY,
        )
        self.company_token_a = _get_token(self.client, "hr@apex.com", "CompanyPass123!")
        self.company_profile_a = CompanyProfile.objects.create(
            user=self.company_user_a,
            company_name="Apex Corp",
            industry="Software",
            location="Bengaluru",
            contact_email="hr@apex.com",
            verification_status=CompanyProfile.VerificationStatus.APPROVED,
        )

        # 3. Company B (Beacon Systems)
        self.company_user_b = User.objects.create_user(
            email="hr@beacon.com",
            password="CompanyPass123!",
            first_name="Beacon",
            last_name="HR",
            role=User.Role.COMPANY,
        )
        self.company_token_b = _get_token(self.client, "hr@beacon.com", "CompanyPass123!")
        self.company_profile_b = CompanyProfile.objects.create(
            user=self.company_user_b,
            company_name="Beacon Systems",
            industry="Finance",
            location="Mumbai",
            contact_email="hr@beacon.com",
            verification_status=CompanyProfile.VerificationStatus.APPROVED,
        )

        # 4. Student 1 (Aditi - Computer Science, 9.20 CGPA)
        self.student_user_1 = User.objects.create_user(
            email="aditi@college.edu",
            student_id="23CS010",
            password="StudentPass123!",
            first_name="Aditi",
            last_name="Rao",
            role=User.Role.STUDENT,
        )
        self.student_token_1 = _get_token(self.client, "23CS010", "StudentPass123!")
        self.student_profile_1 = StudentProfile.objects.create(
            user=self.student_user_1,
            department="Computer Science",
            course="B.Tech",
            year=4,
            cgpa=Decimal("9.20"),
            skills="Python, Django, Machine Learning",
        )

        # 5. Student 2 (Rohan - Mechanical, 8.10 CGPA)
        self.student_user_2 = User.objects.create_user(
            email="rohan@college.edu",
            student_id="23ME020",
            password="StudentPass123!",
            first_name="Rohan",
            last_name="Gupta",
            role=User.Role.STUDENT,
        )
        self.student_token_2 = _get_token(self.client, "23ME020", "StudentPass123!")
        self.student_profile_2 = StudentProfile.objects.create(
            user=self.student_user_2,
            department="Mechanical Engineering",
            course="B.Tech",
            year=4,
            cgpa=Decimal("8.10"),
            skills="SolidWorks, MATLAB",
        )

        # 6. Job for Company A
        self.job_a = JobListing.objects.create(
            company=self.company_profile_a,
            job_title="Software Development Engineer",
            description="Core backend developer role",
            job_type=JobListing.JobType.FULL_TIME,
            salary=Decimal("1500000.00"),
            job_location="Bengaluru",
            minimum_cgpa=Decimal("7.00"),
            eligible_departments=["Computer Science"],
            application_deadline=timezone.now() + timedelta(days=30),
            status=JobListing.JobStatus.APPROVED,
        )

        # 7. Job for Company B
        self.job_b = JobListing.objects.create(
            company=self.company_profile_b,
            job_title="Robotics Design Engineer",
            description="Hardware automation role",
            job_type=JobListing.JobType.FULL_TIME,
            salary=Decimal("1200000.00"),
            job_location="Pune",
            minimum_cgpa=Decimal("7.00"),
            eligible_departments=["Mechanical Engineering"],
            application_deadline=timezone.now() + timedelta(days=30),
            status=JobListing.JobStatus.APPROVED,
        )

        # 8. Applications
        self.app_1 = JobApplication.objects.create(
            student=self.student_profile_1,
            job=self.job_a,
            status=JobApplication.ApplicationStatus.APPLIED,
        )
        self.app_2 = JobApplication.objects.create(
            student=self.student_profile_2,
            job=self.job_b,
            status=JobApplication.ApplicationStatus.APPLIED,
        )

    # =========================================================================
    # TASK 1, 2, 3: APPLICATION STATUS & TRANSITION RULES
    # =========================================================================

    def test_company_can_shortlist_applicant(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-status", kwargs={"pk": self.app_1.id})
        response = self.client.patch(url, {"status": "SHORTLISTED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app_1.refresh_from_db()
        self.assertEqual(self.app_1.status, JobApplication.ApplicationStatus.SHORTLISTED)

    def test_company_can_reject_applicant(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-status", kwargs={"pk": self.app_1.id})
        response = self.client.patch(url, {"status": "REJECTED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app_1.refresh_from_db()
        self.assertEqual(self.app_1.status, JobApplication.ApplicationStatus.REJECTED)

    def test_company_cannot_select_directly_from_applied(self):
        """Must shortlist before selecting."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-status", kwargs={"pk": self.app_1.id})
        response = self.client.patch(url, {"status": "SELECTED"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shortlist", response.data["status"][0].lower())

    def test_company_can_select_shortlisted_applicant(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-status", kwargs={"pk": self.app_1.id})
        response = self.client.patch(url, {"status": "SELECTED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app_1.refresh_from_db()
        self.assertEqual(self.app_1.status, JobApplication.ApplicationStatus.SELECTED)

    def test_rejected_application_cannot_be_modified(self):
        self.app_1.status = JobApplication.ApplicationStatus.REJECTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-status", kwargs={"pk": self.app_1.id})
        response = self.client.patch(url, {"status": "SHORTLISTED"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rejected", response.data["status"][0].lower())

    def test_company_cannot_modify_another_company_application(self):
        # Company A tries to alter Company B's application (app_2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-status", kwargs={"pk": self.app_2.id})
        response = self.client.patch(url, {"status": "SHORTLISTED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_modify_application_status(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        url = reverse("company-application-status", kwargs={"pk": self.app_1.id})
        response = self.client.patch(url, {"status": "SELECTED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_cannot_modify_application_status_via_company_endpoint(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("company-application-status", kwargs={"pk": self.app_1.id})
        response = self.client.patch(url, {"status": "SHORTLISTED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # TASK 4, 5, 6, 7, 8: INTERVIEWS
    # =========================================================================

    def test_company_can_schedule_online_interview(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-interviews", kwargs={"pk": self.app_1.id})
        future_time = timezone.now() + timedelta(days=5)
        payload = {
            "round": 1,
            "interview_type": "ONLINE",
            "scheduled_at": future_time.isoformat(),
            "meeting_link": "https://meet.google.com/xyz-abc-def",
            "interviewer": "Engineering Panel A",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["interview"]["round"], 1)
        self.assertEqual(response.data["interview"]["interview_type"], "ONLINE")

    def test_company_can_schedule_offline_interview(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-interviews", kwargs={"pk": self.app_1.id})
        future_time = timezone.now() + timedelta(days=7)
        payload = {
            "round": 1,
            "interview_type": "OFFLINE",
            "scheduled_at": future_time.isoformat(),
            "venue": "Campus Block C, Auditorium 1",
            "interviewer": "HR Director",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["interview"]["venue"], "Campus Block C, Auditorium 1")

    def test_cannot_schedule_interview_for_unshortlisted_applicant(self):
        # app_1 is still in APPLIED status
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-interviews", kwargs={"pk": self.app_1.id})
        future_time = timezone.now() + timedelta(days=5)
        payload = {
            "round": 1,
            "interview_type": "ONLINE",
            "scheduled_at": future_time.isoformat(),
            "meeting_link": "https://meet.google.com/xyz-abc-def",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SHORTLISTED", response.data["detail"])

    def test_online_interview_requires_meeting_link(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-interviews", kwargs={"pk": self.app_1.id})
        future_time = timezone.now() + timedelta(days=5)
        payload = {
            "round": 1,
            "interview_type": "ONLINE",
            "scheduled_at": future_time.isoformat(),
            "meeting_link": "",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("meeting_link", response.data)

    def test_offline_interview_requires_venue(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-interviews", kwargs={"pk": self.app_1.id})
        future_time = timezone.now() + timedelta(days=5)
        payload = {
            "round": 1,
            "interview_type": "OFFLINE",
            "scheduled_at": future_time.isoformat(),
            "venue": "",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("venue", response.data)

    def test_past_interview_time_rejected(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-interviews", kwargs={"pk": self.app_1.id})
        past_time = timezone.now() - timedelta(hours=2)
        payload = {
            "round": 1,
            "interview_type": "ONLINE",
            "scheduled_at": past_time.isoformat(),
            "meeting_link": "https://meet.google.com/test",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_interview_round_prevented(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        Interview.objects.create(
            application=self.app_1,
            round=1,
            interview_type=Interview.InterviewType.ONLINE,
            scheduled_at=timezone.now() + timedelta(days=3),
            meeting_link="https://meet.google.com/one",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-interviews", kwargs={"pk": self.app_1.id})
        payload = {
            "round": 1,
            "interview_type": "ONLINE",
            "scheduled_at": (timezone.now() + timedelta(days=4)).isoformat(),
            "meeting_link": "https://meet.google.com/duplicate",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already scheduled", response.data["detail"])

    def test_company_can_complete_interview_and_record_feedback(self):
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        interview = Interview.objects.create(
            application=self.app_1,
            round=1,
            interview_type=Interview.InterviewType.ONLINE,
            scheduled_at=timezone.now() + timedelta(days=3),
            meeting_link="https://meet.google.com/one",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-interview-detail", kwargs={"pk": interview.id})
        payload = {
            "status": "COMPLETED",
            "feedback": "Outstanding technical problem-solving and systems design understanding.",
        }
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        interview.refresh_from_db()
        self.assertEqual(interview.status, Interview.InterviewStatus.COMPLETED)
        self.assertIn("Outstanding", interview.feedback)

    def test_student_can_view_only_own_interviews(self):
        # Interview for Student 1
        Interview.objects.create(
            application=self.app_1,
            round=1,
            interview_type=Interview.InterviewType.ONLINE,
            scheduled_at=timezone.now() + timedelta(days=2),
            meeting_link="https://meet.google.com/student1",
        )
        # Interview for Student 2
        Interview.objects.create(
            application=self.app_2,
            round=1,
            interview_type=Interview.InterviewType.OFFLINE,
            scheduled_at=timezone.now() + timedelta(days=4),
            venue="Lab 201",
        )

        # Student 1 logs in
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        url = reverse("student-interview-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["company_name"], "Apex Corp")
        self.assertEqual(response.data[0]["meeting_link"], "https://meet.google.com/student1")

    # =========================================================================
    # TASK 9, 10, 11, 12: OFFERS & RESPONSES
    # =========================================================================

    def test_company_can_issue_offer_for_selected_applicant(self):
        self.app_1.status = JobApplication.ApplicationStatus.SELECTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-offer", kwargs={"pk": self.app_1.id})
        joining_date = (timezone.now() + timedelta(days=60)).date().isoformat()
        payload = {
            "offer_letter_number": "APEX-2026-SDE-001",
            "ctc": "1500000.00",
            "joining_date": joining_date,
            "offer_details": "Software Development Engineer - Bengaluru Headquarters",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["offer"]["offer_letter_number"], "APEX-2026-SDE-001")
        self.assertEqual(response.data["offer"]["status"], "PENDING")

    def test_cannot_issue_offer_for_unselected_applicant(self):
        # app_1 is SHORTLISTED, not SELECTED
        self.app_1.status = JobApplication.ApplicationStatus.SHORTLISTED
        self.app_1.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-offer", kwargs={"pk": self.app_1.id})
        joining_date = (timezone.now() + timedelta(days=60)).date().isoformat()
        payload = {
            "offer_letter_number": "APEX-2026-SDE-002",
            "ctc": "1500000.00",
            "joining_date": joining_date,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SELECTED", response.data["detail"])

    def test_cannot_issue_offer_for_another_company_applicant(self):
        self.app_2.status = JobApplication.ApplicationStatus.SELECTED
        self.app_2.save()

        # Company A tries to issue offer to Company B's applicant
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-offer", kwargs={"pk": self.app_2.id})
        joining_date = (timezone.now() + timedelta(days=60)).date().isoformat()
        payload = {
            "offer_letter_number": "HIJACK-001",
            "ctc": "1000000.00",
            "joining_date": joining_date,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_issue_duplicate_offer(self):
        self.app_1.status = JobApplication.ApplicationStatus.SELECTED
        self.app_1.save()

        JobOffer.objects.create(
            application=self.app_1,
            offer_letter_number="FIRST-OFFER-001",
            ctc=Decimal("1500000.00"),
            joining_date=(timezone.now() + timedelta(days=30)).date(),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        url = reverse("company-application-offer", kwargs={"pk": self.app_1.id})
        payload = {
            "offer_letter_number": "SECOND-OFFER-002",
            "ctc": "1600000.00",
            "joining_date": (timezone.now() + timedelta(days=40)).date().isoformat(),
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been generated", response.data["detail"])

    def test_student_can_view_own_offers(self):
        self.app_1.status = JobApplication.ApplicationStatus.SELECTED
        self.app_1.save()

        offer = JobOffer.objects.create(
            application=self.app_1,
            offer_letter_number="APEX-OFFER-101",
            ctc=Decimal("1500000.00"),
            joining_date=(timezone.now() + timedelta(days=45)).date(),
            offer_details="Joining bonus included",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        url = reverse("student-offer-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["offer_letter_number"], "APEX-OFFER-101")
        self.assertEqual(response.data[0]["company_name"], "Apex Corp")

    def test_student_can_accept_offer_and_creates_placement_record(self):
        self.app_1.status = JobApplication.ApplicationStatus.SELECTED
        self.app_1.save()

        joining_date = (timezone.now() + timedelta(days=45)).date()
        offer = JobOffer.objects.create(
            application=self.app_1,
            offer_letter_number="APEX-ACCEPT-01",
            ctc=Decimal("1500000.00"),
            joining_date=joining_date,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        url = reverse("student-offer-respond", kwargs={"pk": offer.id})
        response = self.client.patch(url, {"status": "ACCEPTED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["offer"]["status"], "ACCEPTED")

        # Verify DB state of offer
        offer.refresh_from_db()
        self.assertEqual(offer.status, JobOffer.OfferStatus.ACCEPTED)
        self.assertIsNotNone(offer.responded_at)

        # Verify PlacementRecord was created transactionally
        placement = PlacementRecord.objects.get(offer=offer)
        self.assertEqual(placement.student, self.student_profile_1)
        self.assertEqual(placement.company, self.company_profile_a)
        self.assertEqual(placement.job, self.job_a)
        self.assertEqual(placement.ctc, Decimal("1500000.00"))
        self.assertEqual(placement.joining_date, joining_date)
        self.assertEqual(placement.placement_status, PlacementRecord.PlacementStatus.PLACED)

    def test_student_can_reject_offer(self):
        self.app_1.status = JobApplication.ApplicationStatus.SELECTED
        self.app_1.save()

        offer = JobOffer.objects.create(
            application=self.app_1,
            offer_letter_number="APEX-REJECT-01",
            ctc=Decimal("1500000.00"),
            joining_date=(timezone.now() + timedelta(days=45)).date(),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        url = reverse("student-offer-respond", kwargs={"pk": offer.id})
        response = self.client.patch(url, {"status": "REJECTED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["offer"]["status"], "REJECTED")

        offer.refresh_from_db()
        self.assertEqual(offer.status, JobOffer.OfferStatus.REJECTED)

        # Verify NO placement record created on rejection
        self.assertFalse(PlacementRecord.objects.filter(offer=offer).exists())

    def test_student_cannot_respond_to_another_student_offer(self):
        self.app_2.status = JobApplication.ApplicationStatus.SELECTED
        self.app_2.save()

        offer_b = JobOffer.objects.create(
            application=self.app_2,
            offer_letter_number="BEACON-OFFER-01",
            ctc=Decimal("1200000.00"),
            joining_date=(timezone.now() + timedelta(days=30)).date(),
        )

        # Student 1 attempts to respond to Student 2's offer
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        url = reverse("student-offer-respond", kwargs={"pk": offer_b.id})
        response = self.client.patch(url, {"status": "ACCEPTED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_respond_twice(self):
        self.app_1.status = JobApplication.ApplicationStatus.SELECTED
        self.app_1.save()

        offer = JobOffer.objects.create(
            application=self.app_1,
            offer_letter_number="APEX-TWICE-01",
            ctc=Decimal("1500000.00"),
            joining_date=(timezone.now() + timedelta(days=45)).date(),
            status=JobOffer.OfferStatus.ACCEPTED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        url = reverse("student-offer-respond", kwargs={"pk": offer.id})
        response = self.client.patch(url, {"status": "REJECTED"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already responded", response.data["detail"])

    # =========================================================================
    # TASK 13, 14, 15, 16: TPO PLACEMENTS & ANALYTICS SUMMARY
    # =========================================================================

    def test_tpo_can_view_placements_and_filter(self):
        # Create Placement 1
        offer_1 = JobOffer.objects.create(
            application=self.app_1,
            offer_letter_number="TPO-OFFER-1",
            ctc=Decimal("1500000.00"),
            joining_date=(timezone.now() + timedelta(days=30)).date(),
            status=JobOffer.OfferStatus.ACCEPTED,
        )
        PlacementRecord.objects.create(
            student=self.student_profile_1,
            company=self.company_profile_a,
            job=self.job_a,
            application=self.app_1,
            offer=offer_1,
            ctc=offer_1.ctc,
            joining_date=offer_1.joining_date,
            placement_status=PlacementRecord.PlacementStatus.PLACED,
        )

        # Create Placement 2
        offer_2 = JobOffer.objects.create(
            application=self.app_2,
            offer_letter_number="TPO-OFFER-2",
            ctc=Decimal("1200000.00"),
            joining_date=(timezone.now() + timedelta(days=40)).date(),
            status=JobOffer.OfferStatus.ACCEPTED,
        )
        PlacementRecord.objects.create(
            student=self.student_profile_2,
            company=self.company_profile_b,
            job=self.job_b,
            application=self.app_2,
            offer=offer_2,
            ctc=offer_2.ctc,
            joining_date=offer_2.joining_date,
            placement_status=PlacementRecord.PlacementStatus.PLACED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-placement-list")

        # 1. View all
        res_all = self.client.get(url)
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data), 2)

        # 2. Filter by department = Computer Science
        res_dept = self.client.get(f"{url}?department=Computer")
        self.assertEqual(res_dept.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_dept.data), 1)
        self.assertEqual(res_dept.data[0]["student_name"], "Aditi Rao")

        # 3. Filter by company = Beacon
        res_comp = self.client.get(f"{url}?company=Beacon")
        self.assertEqual(res_comp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_comp.data), 1)
        self.assertEqual(res_comp.data[0]["student_name"], "Rohan Gupta")

    def test_tpo_placement_summary_calculations(self):
        # Student 1: 15.0 LPA
        offer_1 = JobOffer.objects.create(
            application=self.app_1,
            offer_letter_number="STAT-OFFER-1",
            ctc=Decimal("1500000.00"),
            joining_date=(timezone.now() + timedelta(days=30)).date(),
            status=JobOffer.OfferStatus.ACCEPTED,
        )
        PlacementRecord.objects.create(
            student=self.student_profile_1,
            company=self.company_profile_a,
            job=self.job_a,
            application=self.app_1,
            offer=offer_1,
            ctc=offer_1.ctc,
            joining_date=offer_1.joining_date,
            placement_status=PlacementRecord.PlacementStatus.PLACED,
        )

        # Student 2: 12.0 LPA
        offer_2 = JobOffer.objects.create(
            application=self.app_2,
            offer_letter_number="STAT-OFFER-2",
            ctc=Decimal("1200000.00"),
            joining_date=(timezone.now() + timedelta(days=40)).date(),
            status=JobOffer.OfferStatus.ACCEPTED,
        )
        PlacementRecord.objects.create(
            student=self.student_profile_2,
            company=self.company_profile_b,
            job=self.job_b,
            application=self.app_2,
            offer=offer_2,
            ctc=offer_2.ctc,
            joining_date=offer_2.joining_date,
            placement_status=PlacementRecord.PlacementStatus.PLACED,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        url = reverse("tpo-placement-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["total_students_placed"], 2)
        self.assertEqual(data["total_placements"], 2)
        self.assertEqual(data["total_companies"], 2)
        # Avg of 1500000 and 1200000 is 1350000
        self.assertEqual(Decimal(str(data["average_ctc"])), Decimal("1350000.00"))
        self.assertEqual(Decimal(str(data["highest_ctc"])), Decimal("1500000.00"))
        self.assertEqual(len(data["department_wise"]), 2)

    def test_student_and_company_cannot_access_tpo_placements(self):
        url = reverse("tpo-placement-list")
        url_summary = reverse("tpo-placement-summary")

        # Student attempt
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token_1}")
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(url_summary).status_code, status.HTTP_403_FORBIDDEN)

        # Company attempt
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.company_token_a}")
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(url_summary).status_code, status.HTTP_403_FORBIDDEN)

        # Unauthenticated attempt
        self.client.credentials()
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(url_summary).status_code, status.HTTP_401_UNAUTHORIZED)
