from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count, Max, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, views
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsCompany, IsStudent, IsTPO

from .models import (
    CompanyProfile,
    Interview,
    JobApplication,
    JobListing,
    JobOffer,
    Notification,
    PlacementDrive,
    PlacementRecord,
    StudentProfile,
)
from .serializers import (
    ApplicationStatusUpdateSerializer,
    CompanyApplicationSerializer,
    CompanyProfileSerializer,
    CompanyVerificationSerializer,
    InterviewSerializer,
    InterviewUpdateSerializer,
    JobListingSerializer,
    JobOfferCreateSerializer,
    JobOfferSerializer,
    NotificationSerializer,
    OfferResponseSerializer,
    PlacementDriveSerializer,
    PlacementRecordSerializer,
    PlacementRecordStatusSerializer,
    StudentApplicationSerializer,
    StudentCompanySerializer,
    StudentInterviewSerializer,
    StudentJobListingSerializer,
    StudentProfileSerializer,
    TPOApplicationSerializer,
    TPOCompanySerializer,
    TPOInterviewSerializer,
    TPOJobListingSerializer,
    TPOJobVerifySerializer,
    TPOStudentSerializer,
)

User = get_user_model()


def create_notification(recipient, notification_type, title, message, **related_objects):
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        **related_objects,
    )


def notify_role(role, notification_type, title, message, **related_objects):
    return [
        create_notification(user, notification_type, title, message, **related_objects)
        for user in User.objects.filter(role=role, is_active=True)
    ]





class StudentProfileView(views.APIView):
    """
    Profile management endpoint for authenticated Students.
    Supports GET, POST, PUT, PATCH.
    """

    permission_classes = [IsAuthenticated, IsStudent]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = StudentProfileSerializer

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Student profile not found. Please create one using POST."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(
            request.user.student_profile,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Profile already exists for this student. Use PUT or PATCH to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            {
                "message": "Student profile created successfully.",
                "profile": self.serializer_class(profile, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Student profile not found. Please create one using POST."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(
            request.user.student_profile,
            data=request.data,
            partial=False,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            {
                "message": "Student profile updated successfully.",
                "profile": self.serializer_class(profile, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Student profile not found. Please create one using POST."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(
            request.user.student_profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            {
                "message": "Student profile updated successfully.",
                "profile": self.serializer_class(profile, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class CompanyProfileView(views.APIView):
    """
    Profile management endpoint for authenticated Companies.
    Supports GET, POST, PUT, PATCH.
    """

    permission_classes = [IsAuthenticated, IsCompany]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CompanyProfileSerializer

    def get(self, request):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found. Please create one using POST."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(
            request.user.company_profile,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Profile already exists for this company. Use PUT or PATCH to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            {
                "message": "Company profile created successfully.",
                "profile": self.serializer_class(profile, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def put(self, request):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found. Please create one using POST."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(
            request.user.company_profile,
            data=request.data,
            partial=False,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            {
                "message": "Company profile updated successfully.",
                "profile": self.serializer_class(profile, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found. Please create one using POST."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(
            request.user.company_profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(
            {
                "message": "Company profile updated successfully.",
                "profile": self.serializer_class(profile, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class TPOCompanyListView(views.APIView):
    """
    TPO-only endpoint to list all registered companies.
    Supports filtering by ?verification_status=PENDING | APPROVED | REJECTED.
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        status_filter = request.query_params.get("verification_status")
        queryset = CompanyProfile.objects.select_related("user").all()

        if status_filter:
            normalized = status_filter.strip().upper()
            valid_statuses = [choice[0] for choice in CompanyProfile.VerificationStatus.choices]
            if normalized not in valid_statuses:
                return Response(
                    {
                        "detail": f"Invalid verification_status '{status_filter}'. Allowed values: {', '.join(valid_statuses)}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(verification_status=normalized)

        serializer = TPOCompanySerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TPOCompanyDetailView(views.APIView):
    """
    TPO-only endpoint to view details of a specific registered company.
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request, pk):
        company = get_object_or_404(CompanyProfile.objects.select_related("user"), pk=pk)
        serializer = TPOCompanySerializer(company, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TPOCompanyVerifyView(views.APIView):
    """
    TPO-only endpoint to approve or reject a company profile.
    Accepts:
    {
        "verification_status": "APPROVED" | "REJECTED",
        "remarks": "Feedback or justification"
    }
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def patch(self, request, pk):
        company = get_object_or_404(CompanyProfile.objects.select_related("user"), pk=pk)
        serializer = CompanyVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_company = serializer.update(company, serializer.validated_data)
        return Response(
            {
                "message": f"Company verification status updated to '{updated_company.verification_status}'.",
                "company": TPOCompanySerializer(updated_company, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class TPOStudentListView(views.APIView):
    """
    TPO-only endpoint to view and filter student profiles.
    Supported filters:
    - ?department=... (case-insensitive substring match)
    - ?course=... (case-insensitive substring match)
    - ?min_cgpa=... (numeric decimal, e.g. 7.5 or 8)
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        queryset = StudentProfile.objects.select_related("user").all()

        dept = request.query_params.get("department")
        if dept:
            queryset = queryset.filter(department__icontains=dept.strip())

        course = request.query_params.get("course")
        if course:
            queryset = queryset.filter(course__icontains=course.strip())

        min_cgpa = request.query_params.get("min_cgpa")
        if min_cgpa:
            try:
                cgpa_val = Decimal(min_cgpa.strip())
                if cgpa_val < Decimal("0.00") or cgpa_val > Decimal("10.00"):
                    return Response(
                        {"detail": "min_cgpa must be between 0.00 and 10.00."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                queryset = queryset.filter(cgpa__gte=cgpa_val)
            except (InvalidOperation, ValueError):
                return Response(
                    {"detail": "Invalid min_cgpa format. Must be a numeric decimal (e.g. 7.5 or 8)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = TPOStudentSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# =============================================================================
# STAGE 5: JOB LISTING & APPLICATION VIEWS
# =============================================================================


class CompanyJobListView(views.APIView):
    """
    Endpoint for Company users to:
    - GET: List only their own job listings.
    - POST: Create a new job listing for their company.
    """

    permission_classes = [IsAuthenticated, IsCompany]

    def get(self, request):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Please create your company profile before managing jobs."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        jobs = JobListing.objects.filter(company=request.user.company_profile).order_by("-created_at")
        serializer = JobListingSerializer(jobs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Please create your company profile before posting jobs."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = JobListingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        notify_role(
            User.Role.TPO,
            Notification.NotificationType.JOB_REVIEW_REQUIRED,
            "Job awaiting review",
            f"{request.user.company_profile.company_name} submitted {job.job_title} for review.",
            job=job,
        )
        return Response(
            {
                "message": "Job listing created successfully.",
                "job": JobListingSerializer(job, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CompanyJobDetailView(views.APIView):
    """
    Endpoint for Company users to retrieve or update their own job listing.
    """

    permission_classes = [IsAuthenticated, IsCompany]

    def _get_job(self, request, pk):
        if not hasattr(request.user, "company_profile"):
            return None, Response(
                {"detail": "Company profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            job = JobListing.objects.get(pk=pk, company=request.user.company_profile)
            return job, None
        except JobListing.DoesNotExist:
            return None, Response(
                {"detail": "Job listing not found or you do not have permission to access it."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get(self, request, pk):
        job, err_res = self._get_job(request, pk)
        if err_res:
            return err_res
        serializer = JobListingSerializer(job, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        job, err_res = self._get_job(request, pk)
        if err_res:
            return err_res
        serializer = JobListingSerializer(job, data=request.data, partial=False, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_job = serializer.save()
        return Response(
            {
                "message": "Job listing updated successfully.",
                "job": JobListingSerializer(updated_job, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        job, err_res = self._get_job(request, pk)
        if err_res:
            return err_res
        serializer = JobListingSerializer(job, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_job = serializer.save()
        return Response(
            {
                "message": "Job listing updated successfully.",
                "job": JobListingSerializer(updated_job, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class CompanyJobApplicationsView(views.APIView):
    """
    Endpoint for a Company to view applicants to its own job listing.
    Strictly isolated: Company A cannot view applicants for Company B's job.
    """

    permission_classes = [IsAuthenticated, IsCompany]

    def get(self, request, pk):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        job = get_object_or_404(JobListing, pk=pk)
        if job.company != request.user.company_profile:
            return Response(
                {"detail": "You do not have permission to view applicants for this job listing."},
                status=status.HTTP_403_FORBIDDEN,
            )
        applications = job.applications.select_related("student__user").order_by("-applied_at")
        serializer = CompanyApplicationSerializer(applications, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TPOJobListView(views.APIView):
    """
    TPO endpoint to list all job listings across all companies.
    Supports filtering by ?status=PENDING_TPO_APPROVAL | APPROVED | REJECTED | DRAFT | CLOSED.
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        queryset = JobListing.objects.select_related("company__user").all().order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            norm_status = status_filter.strip().upper()
            valid_statuses = [choice[0] for choice in JobListing.JobStatus.choices]
            if norm_status not in valid_statuses:
                return Response(
                    {
                        "detail": f"Invalid status '{status_filter}'. Allowed values: {', '.join(valid_statuses)}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=norm_status)

        serializer = TPOJobListingSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TPOApplicationListView(views.APIView):
    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        applications = JobApplication.objects.select_related(
            "student__user", "job__company"
        ).order_by("-applied_at")
        serializer = TPOApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TPOInterviewListView(views.APIView):
    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        interviews = Interview.objects.select_related(
            "application__student__user",
            "application__job__company",
        ).order_by("scheduled_at")
        serializer = TPOInterviewSerializer(interviews, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
   
class TPOOfferListView(views.APIView):
    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        offers = JobOffer.objects.select_related(
            "application__student__user",
            "application__job__company",
        ).order_by("-issued_at")
        serializer = JobOfferSerializer(offers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TPOJobVerifyView(views.APIView):
    """
    TPO endpoint to approve or reject a job listing.
    Accepts:
    {
        "status": "APPROVED" | "REJECTED",
        "remarks": "Optional feedback"
    }
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def patch(self, request, pk):
        job = get_object_or_404(JobListing.objects.select_related("company"), pk=pk)
        serializer = TPOJobVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_job = serializer.update(job, serializer.validated_data)
        if updated_job.status == JobListing.JobStatus.APPROVED:
            student_users = User.objects.filter(
                role=User.Role.STUDENT,
                is_active=True,
                student_profile__isnull=False,
            )
            for student_user in student_users:
                create_notification(
                    student_user,
                    Notification.NotificationType.NEW_JOB,
                    "New job available",
                    f"{updated_job.job_title} at {updated_job.company.company_name} is now open.",
                    job=updated_job,
                )
        return Response(
            {
                "message": f"Job listing status updated to '{updated_job.status}'.",
                "job": TPOJobListingSerializer(updated_job, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class StudentCompanyListView(views.APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        companies = CompanyProfile.objects.filter(
            verification_status=CompanyProfile.VerificationStatus.APPROVED
        ).annotate(
            available_jobs=Count(
                "job_listings",
                filter=Q(
                    job_listings__status=JobListing.JobStatus.APPROVED,
                    job_listings__application_deadline__gt=timezone.now(),
                ),
                distinct=True,
            )
        ).order_by("company_name")
        serializer = StudentCompanySerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentJobListView(views.APIView):
    """
    Student endpoint to browse approved jobs only.
    DRAFT, PENDING_TPO_APPROVAL, and REJECTED jobs are strictly hidden.
    Computes dynamic eligibility flags for the authenticated student.
    """

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        jobs = JobListing.objects.filter(
            status=JobListing.JobStatus.APPROVED,
            application_deadline__gt=timezone.now(),
        ).select_related("company").order_by("-created_at")
        serializer = StudentJobListingSerializer(jobs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class StudentJobApplyView(views.APIView):
    """
    Student endpoint to apply for an approved job listing.
    Performs comprehensive backend eligibility checks:
    1. Authenticated Student with profile.
    2. Job exists and is APPROVED.
    3. Deadline has not expired.
    4. Student CGPA meets minimum requirement.
    5. Student department is eligible.
    6. Student course is eligible (if course restriction exists).
    7. Prevents duplicate applications.
    """

    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, pk):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Please create a student profile before applying for jobs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = request.user.student_profile

        job = get_object_or_404(JobListing, pk=pk)

        # 1. Job must be APPROVED
        if job.status != JobListing.JobStatus.APPROVED:
            return Response(
                {
                    "detail": (
                        "You can only apply to approved job listings. "
                        f"This job is currently '{job.get_status_display()}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 2. Deadline check
        if timezone.now() > job.application_deadline:
            return Response(
                {"detail": "The application deadline for this job has passed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. CGPA eligibility
        if student.cgpa < job.minimum_cgpa:
            return Response(
                {
                    "detail": f"You are not eligible for this job because your CGPA ({student.cgpa}) is below the required minimum of {job.minimum_cgpa}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Department eligibility
        if job.eligible_departments:
            s_dept = student.department.strip().lower()
            dept_match = any(
                s_dept == d.strip().lower() or d.strip().lower() in s_dept or s_dept in d.strip().lower()
                for d in job.eligible_departments
            )
            if not dept_match:
                return Response(
                    {
                        "detail": f"You are not eligible for this job because your department '{student.department}' is not in the eligible departments list ({', '.join(job.eligible_departments)})."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 5. Course eligibility
        if job.eligible_courses:
            s_course = student.course.strip().lower()
            course_match = any(
                s_course == c.strip().lower() or c.strip().lower() in s_course or s_course in c.strip().lower()
                for c in job.eligible_courses
            )
            if not course_match:
                return Response(
                    {
                        "detail": f"You are not eligible for this job because your course '{student.course}' is not in the eligible courses list ({', '.join(job.eligible_courses)})."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 6. Duplicate application check
        if JobApplication.objects.filter(student=student, job=job).exists():
            return Response(
                {"detail": "You have already applied for this job listing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application = JobApplication.objects.create(student=student, job=job)
        create_notification(
            student.user,
            Notification.NotificationType.APPLICATION_SUBMITTED,
            "Application submitted",
            f"Your application for {job.job_title} was submitted.",
            job=job,
            application=application,
        )
        create_notification(
            job.company.user,
            Notification.NotificationType.APPLICATION_SUBMITTED,
            "New job application",
            f"{student.user.full_name} applied for {job.job_title}.",
            job=job,
            application=application,
        )
        return Response(
            {
                "message": "Job application submitted successfully.",
                "application": StudentApplicationSerializer(application, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class StudentApplicationListView(views.APIView):
    """
    Student endpoint to list all their own submitted applications.
    Strictly isolated: a student cannot view another student's applications.
    """

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response([], status=status.HTTP_200_OK)
        applications = JobApplication.objects.filter(
            student=request.user.student_profile
        ).select_related("job__company").order_by("-applied_at")
        serializer = StudentApplicationSerializer(applications, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentDashboardStatsView(views.APIView):
    """
    Protected student-only endpoint that returns dashboard card counts
    and placement status derived from actual backend records.
    """

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        stats = {
            "available_jobs": 0,
            "applied_jobs": 0,
            "shortlisted": 0,
            "interviews": 0,
            "placement_status": "Not available",
        }

        if not hasattr(request.user, "student_profile"):
            return Response(stats, status=status.HTTP_200_OK)

        student = request.user.student_profile
        applications = JobApplication.objects.filter(student=student)
        approved_jobs_count = JobListing.objects.filter(
            status=JobListing.JobStatus.APPROVED,
            application_deadline__gt=timezone.now(),
        ).count()
        interviews_count = Interview.objects.filter(application__student=student).count()

        stats["available_jobs"] = approved_jobs_count
        stats["applied_jobs"] = applications.count()
        stats["shortlisted"] = applications.filter(
            status=JobApplication.ApplicationStatus.SHORTLISTED
        ).count()
        stats["interviews"] = interviews_count

        if PlacementRecord.objects.filter(
            student=student,
            placement_status=PlacementRecord.PlacementStatus.PLACED,
        ).exists():
            stats["placement_status"] = "Placed"
        elif PlacementRecord.objects.filter(
            student=student,
            placement_status=PlacementRecord.PlacementStatus.WITHDRAWN,
        ).exists():
            stats["placement_status"] = "Withdrawn"
        elif JobOffer.objects.filter(
            application__student=student,
            status=JobOffer.OfferStatus.ACCEPTED,
        ).exists():
            stats["placement_status"] = "Accepted"
        elif applications.filter(status=JobApplication.ApplicationStatus.SELECTED).exists():
            stats["placement_status"] = "Selected"
        elif student.cgpa and student.cgpa >= Decimal("8.00"):
            stats["placement_status"] = "Eligible"
        else:
            stats["placement_status"] = "Not Eligible"

        return Response(stats, status=status.HTTP_200_OK)


# =============================================================================
# STAGE 6: SHORTLISTING, INTERVIEWS, OFFERS & PLACEMENTS
# =============================================================================


class CompanyApplicationStatusView(views.APIView):
    """
    Endpoint for Company to update applicant status:
    PATCH /api/company/applications/<id>/status/
    Accepts: {"status": "SHORTLISTED" | "SELECTED" | "REJECTED"}
    """

    permission_classes = [IsAuthenticated, IsCompany]

    def patch(self, request, pk):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application = get_object_or_404(JobApplication.objects.select_related("job__company", "student__user"), pk=pk)
        if application.job.company != request.user.company_profile:
            return Response(
                {"detail": "You do not have permission to modify applications for another company's job."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ApplicationStatusUpdateSerializer(
            data=request.data,
            context={"application": application},
        )
        serializer.is_valid(raise_exception=True)
        updated_app = serializer.update(application, serializer.validated_data)
        if updated_app.status == JobApplication.ApplicationStatus.SHORTLISTED:
            create_notification(
                updated_app.student.user,
                Notification.NotificationType.APPLICATION_SHORTLISTED,
                "Application shortlisted",
                f"Your application for {updated_app.job.job_title} was shortlisted.",
                job=updated_app.job,
                application=updated_app,
            )
        return Response(
            {
                "message": f"Application status updated to '{updated_app.status}'.",
                "application": CompanyApplicationSerializer(updated_app, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class CompanyInterviewCreateListView(views.APIView):
    """
    Endpoint for Company to:
    - POST: Schedule an interview round for a shortlisted applicant.
    - GET: List all scheduled/completed interviews for an applicant.
    """

    permission_classes = [IsAuthenticated, IsCompany]

    def _get_application(self, request, pk):
        if not hasattr(request.user, "company_profile"):
            return None, Response(
                {"detail": "Company profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application = get_object_or_404(JobApplication.objects.select_related("job__company", "student__user"), pk=pk)
        if application.job.company != request.user.company_profile:
            return None, Response(
                {"detail": "You do not have permission to manage interviews for another company's applicant."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return application, None

    def post(self, request, pk):
        application, err_res = self._get_application(request, pk)
        if err_res:
            return err_res

        # Check application status
        if application.status == JobApplication.ApplicationStatus.APPLIED:
            return Response(
                {"detail": "Applicant must be SHORTLISTED before scheduling an interview."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if application.status == JobApplication.ApplicationStatus.REJECTED:
            return Response(
                {"detail": "Cannot schedule an interview for a rejected application."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        round_num = request.data.get("round", 1)
        if Interview.objects.filter(application=application, round=round_num).exists():
            return Response(
                {"detail": f"Interview round {round_num} is already scheduled for this application."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InterviewSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        interview = serializer.save(application=application)
        create_notification(
            application.student.user,
            Notification.NotificationType.INTERVIEW_SCHEDULED,
            "Interview scheduled",
            f"Round {interview.round} for {application.job.job_title} is scheduled for {interview.scheduled_at:%Y-%m-%d %H:%M}.",
            job=application.job,
            application=application,
            interview=interview,
        )
        return Response(
            {
                "message": f"Interview Round {interview.round} scheduled successfully.",
                "interview": InterviewSerializer(interview, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request, pk):
        application, err_res = self._get_application(request, pk)
        if err_res:
            return err_res
        interviews = application.interviews.all().order_by("round", "scheduled_at")
        serializer = InterviewSerializer(interviews, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyInterviewDetailView(views.APIView):
    """
    Endpoint for Company to update an interview record (feedback, completion status, rescheduling).
    PATCH /api/company/interviews/<id>/
    """

    permission_classes = [IsAuthenticated, IsCompany]

    def patch(self, request, pk):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        interview = get_object_or_404(
            Interview.objects.select_related("application__job__company"),
            pk=pk,
        )
        if interview.application.job.company != request.user.company_profile:
            return Response(
                {"detail": "You do not have permission to modify another company's interview."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = InterviewUpdateSerializer(interview, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_interview = serializer.save()
        return Response(
            {
                "message": "Interview updated successfully.",
                "interview": InterviewSerializer(updated_interview, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class StudentInterviewListView(views.APIView):
    """
    Endpoint for Student to view all their own scheduled & past interviews.
    GET /api/student/interviews/
    """

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response([], status=status.HTTP_200_OK)
        interviews = Interview.objects.filter(
            application__student=request.user.student_profile
        ).select_related("application__job__company").order_by("scheduled_at")
        serializer = StudentInterviewSerializer(interviews, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyOfferCreateView(views.APIView):
    """
    Endpoint for Company to generate an offer for a SELECTED applicant.
    GET/POST /api/company/applications/<id>/offer/
    """

    permission_classes = [IsAuthenticated, IsCompany]

    def get(self, request, pk):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application = get_object_or_404(
            JobApplication.objects.select_related("job__company", "student__user"),
            pk=pk,
        )
        if application.job.company != request.user.company_profile:
            return Response(
                {"detail": "You do not have permission to view an offer for another company's job."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            offer = application.offer
        except JobOffer.DoesNotExist:
            return Response({"detail": "No offer has been created for this application."}, status=status.HTTP_404_NOT_FOUND)

        return Response(JobOfferSerializer(offer, context={"request": request}).data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        if not hasattr(request.user, "company_profile"):
            return Response(
                {"detail": "Company profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application = get_object_or_404(
            JobApplication.objects.select_related("job__company", "student__user"),
            pk=pk,
        )
        if application.job.company != request.user.company_profile:
            return Response(
                {"detail": "You do not have permission to issue offers for another company's job."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if application.status != JobApplication.ApplicationStatus.SELECTED:
            return Response(
                {"detail": f"Cannot generate an offer for an applicant who is not SELECTED. Current status: '{application.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(application, "offer"):
            return Response(
                {"detail": "An offer has already been generated for this application."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = JobOfferCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        offer = serializer.save(application=application)
        create_notification(
            application.student.user,
            Notification.NotificationType.OFFER_ISSUED,
            "Job offer received",
            f"{application.job.company.company_name} issued an offer for {application.job.job_title}.",
            job=application.job,
            application=application,
            offer=offer,
        )
        return Response(
            {
                "message": "Job offer issued successfully.",
                "offer": JobOfferSerializer(offer, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class StudentOfferListView(views.APIView):
    """
    Endpoint for Student to view all job offers extended to them.
    GET /api/student/offers/
    """

    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response([], status=status.HTTP_200_OK)
        offers = JobOffer.objects.filter(
            application__student=request.user.student_profile
        ).select_related("application__job__company", "application__student__user").order_by("-issued_at")
        serializer = JobOfferSerializer(offers, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentOfferRespondView(views.APIView):
    """
    Endpoint for Student to accept or reject an offer:
    PATCH /api/student/offers/<id>/respond/
    Accepts: {"status": "ACCEPTED" | "REJECTED"}
    When ACCEPTED, transactionally creates a final PlacementRecord.
    """

    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request, pk):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Student profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        offer = get_object_or_404(
            JobOffer.objects.select_related("application__student", "application__job__company"),
            pk=pk,
        )
        if offer.application.student != request.user.student_profile:
            return Response(
                {"detail": "You do not have permission to respond to another student's offer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if offer.status != JobOffer.OfferStatus.PENDING:
            return Response(
                {"detail": f"You have already responded to this offer. Current status: '{offer.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OfferResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        with transaction.atomic():
            offer.status = new_status
            offer.responded_at = timezone.now()
            offer.save()

            if new_status == JobOffer.OfferStatus.ACCEPTED:
                # Ensure no duplicate placement record exists
                placement_record, created = PlacementRecord.objects.get_or_create(
                    application=offer.application,
                    offer=offer,
                    defaults={
                        "student": offer.application.student,
                        "company": offer.application.job.company,
                        "job": offer.application.job,
                        "ctc": offer.ctc,
                        "joining_date": offer.joining_date,
                        "placement_status": PlacementRecord.PlacementStatus.PLACED,
                    },
                )
                if created:
                    create_notification(
                        request.user,
                        Notification.NotificationType.PLACEMENT_CONFIRMED,
                        "Placement confirmed",
                        f"Your placement with {offer.application.job.company.company_name} has been confirmed.",
                        job=offer.application.job,
                        application=offer.application,
                        offer=offer,
                        placement_record=placement_record,
                    )
                    create_notification(
                        offer.application.job.company.user,
                        Notification.NotificationType.PLACEMENT_CONFIRMED,
                        "Student placement confirmed",
                        f"{offer.application.student.user.full_name} accepted the offer for {offer.application.job.job_title}.",
                        job=offer.application.job,
                        application=offer.application,
                        offer=offer,
                        placement_record=placement_record,
                    )
                    notify_role(
                        User.Role.TPO,
                        Notification.NotificationType.PLACEMENT_CONFIRMED,
                        "Placement confirmed",
                        f"{offer.application.student.user.full_name} was placed with {offer.application.job.company.company_name}.",
                        job=offer.application.job,
                        application=offer.application,
                        offer=offer,
                        placement_record=placement_record,
                    )

        return Response(
            {
                "message": f"Offer response recorded as '{new_status}'.",
                "offer": JobOfferSerializer(offer, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class TPOPlacementListView(views.APIView):
    """
    Endpoint for TPO to view final student placement records.
    GET /api/tpo/placements/
    Supports filtering by ?department=, ?company=, ?placement_status=
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        queryset = PlacementRecord.objects.select_related(
            "student__user",
            "company",
            "job",
            "offer",
        ).all().order_by("-placed_at")

        dept = request.query_params.get("department")
        if dept:
            queryset = queryset.filter(student__department__icontains=dept.strip())

        comp = request.query_params.get("company")
        if comp:
            queryset = queryset.filter(company__company_name__icontains=comp.strip())

        p_status = request.query_params.get("placement_status")
        if p_status:
            queryset = queryset.filter(placement_status=p_status.strip().upper())

        serializer = PlacementRecordSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TPOPlacementSummaryView(views.APIView):
    """
    Endpoint for TPO to view placement metrics and analytics summary.
    GET /api/tpo/placements/summary/
    """

    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        records = PlacementRecord.objects.filter(
            placement_status=PlacementRecord.PlacementStatus.PLACED
        )
        total_students_placed = records.values("student").distinct().count()
        total_placements = records.count()
        total_companies = records.values("company").distinct().count()
        stats = records.aggregate(avg_ctc=Avg("ctc"), max_ctc=Max("ctc"))

        dept_counts = list(
            records.values("student__department")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return Response(
            {
                "total_students_placed": total_students_placed,
                "total_placements": total_placements,
                "total_companies": total_companies,
                "average_ctc": round(stats["avg_ctc"], 2) if stats["avg_ctc"] is not None else 0.0,
                "highest_ctc": stats["max_ctc"] if stats["max_ctc"] is not None else 0.0,
                "department_wise": [
                    {"department": item["student__department"], "count": item["count"]}
                    for item in dept_counts
                ],
            },
            status=status.HTTP_200_OK,
        )


class TPOPlacementRecordUpdateView(views.APIView):
    permission_classes = [IsAuthenticated, IsTPO]

    def patch(self, request, pk):
        record = get_object_or_404(
            PlacementRecord.objects.select_related("student__user", "company", "job"),
            pk=pk,
        )
        serializer = PlacementRecordStatusSerializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_record = serializer.save()
        create_notification(
            updated_record.student.user,
            Notification.NotificationType.PLACEMENT_STATUS_UPDATED,
            "Placement status updated",
            f"Your placement status for {updated_record.job.job_title} is now {updated_record.placement_status}.",
            placement_record=updated_record,
        )
        create_notification(
            updated_record.company.user,
            Notification.NotificationType.PLACEMENT_STATUS_UPDATED,
            "Student placement status updated",
            f"{updated_record.student.user.full_name}'s placement status for {updated_record.job.job_title} is now {updated_record.placement_status}.",
            placement_record=updated_record,
        )
        return Response(
            {
                "message": "Placement status updated successfully.",
                "placement": PlacementRecordSerializer(updated_record).data,
            },
            status=status.HTTP_200_OK,
        )


class TPOPlacementDriveListCreateView(views.APIView):
    permission_classes = [IsAuthenticated, IsTPO]

    def get(self, request):
        drives = PlacementDrive.objects.select_related("company", "job").all()
        serializer = PlacementDriveSerializer(drives, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PlacementDriveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        drive = serializer.save()
        return Response(
            {"message": "Placement drive created successfully.", "drive": PlacementDriveSerializer(drive).data},
            status=status.HTTP_201_CREATED,
        )


class TPOPlacementDriveDetailView(views.APIView):
    permission_classes = [IsAuthenticated, IsTPO]

    def patch(self, request, pk):
        drive = get_object_or_404(PlacementDrive.objects.select_related("company", "job"), pk=pk)
        serializer = PlacementDriveSerializer(drive, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        drive = serializer.save()
        return Response(
            {"message": "Placement drive updated successfully.", "drive": PlacementDriveSerializer(drive).data},
            status=status.HTTP_200_OK,
        )


class NotificationListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user)
        return Response(
            {
                "notifications": NotificationSerializer(notifications, many=True).data,
                "unread_count": notifications.filter(is_read=False).count(),
            },
            status=status.HTTP_200_OK,
        )


class NotificationReadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)


class NotificationReadAllView(views.APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"message": "Notifications marked as read."}, status=status.HTTP_200_OK)
