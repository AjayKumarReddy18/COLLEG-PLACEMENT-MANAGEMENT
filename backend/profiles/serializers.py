from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import (
    CompanyProfile,
    Interview,
    JobApplication,
    JobListing,
    JobOffer,
    PlacementRecord,
    StudentProfile,
)

from .validators import validate_instagram_url, validate_resume_file



class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentProfile.
    Includes user details, resume file upload, and optional Instagram URL.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    student_id = serializers.CharField(source="user.student_id", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    instagram_url = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True,
        validators=[validate_instagram_url],
    )
    resume = serializers.FileField(
        required=False,
        allow_null=True,
        validators=[validate_resume_file],
    )

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "user_email",
            "student_id",
            "first_name",
            "last_name",
            "department",
            "course",
            "year",
            "cgpa",
            "skills",
            "resume",
            "github_url",
            "linkedin_url",
            "instagram_url",
            "portfolio_url",
            "date_of_birth",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate_instagram_url(self, value):
        if not value:
            return None
        return value.strip()

    def create(self, validated_data):
        user = self.context["request"].user
        # Prevent duplicate profile creation
        if hasattr(user, "student_profile"):
            raise serializers.ValidationError(
                {"detail": "Profile already exists for this student. Use PUT or PATCH to update."}
            )
        validated_data["user"] = user
        return super().create(validated_data)


class CompanyProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for CompanyProfile.
    Verification status is strictly read-only and cannot be altered by the company.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "user",
            "user_email",
            "company_name",
            "company_description",
            "industry",
            "website",
            "location",
            "contact_email",
            "contact_phone",
            "company_size",
            "logo",
            "verification_status",
            "verification_remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "verification_status",
            "verification_remarks",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        # Prevent duplicate profile creation
        if hasattr(user, "company_profile"):
            raise serializers.ValidationError(
                {"detail": "Profile already exists for this company. Use PUT or PATCH to update."}
            )
        # Ensure company cannot approve itself or write remarks
        validated_data.pop("verification_status", None)
        validated_data.pop("verification_remarks", None)
        validated_data["user"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Ignore any attempt to modify verification_status or remarks
        validated_data.pop("verification_status", None)
        validated_data.pop("verification_remarks", None)
        return super().update(instance, validated_data)


class TPOCompanySerializer(serializers.ModelSerializer):
    """
    Serializer for TPO viewing company profiles.
    Includes user account details, company details, verification status, and remarks.
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    user_phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "user_id",
            "user_email",
            "user_first_name",
            "user_last_name",
            "user_phone_number",
            "company_name",
            "company_description",
            "industry",
            "website",
            "location",
            "contact_email",
            "contact_phone",
            "company_size",
            "logo",
            "verification_status",
            "verification_remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CompanyVerificationSerializer(serializers.Serializer):
    """
    Serializer for TPO approving or rejecting a company profile.
    Accepts:
    - verification_status: strictly 'APPROVED' or 'REJECTED'
    - remarks (optional string feedback)
    """

    verification_status = serializers.ChoiceField(
        choices=["APPROVED", "REJECTED"],
        error_messages={
            "invalid_choice": "Verification status must be either 'APPROVED' or 'REJECTED'."
        },
    )
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def update(self, instance, validated_data):
        instance.verification_status = validated_data["verification_status"]
        if "remarks" in validated_data:
            instance.verification_remarks = validated_data["remarks"]
        instance.save()
        return instance


class TPOStudentSerializer(serializers.ModelSerializer):
    """
    Serializer for TPO viewing student profiles.
    Provides complete academic, skill, and contact information.
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    student_id = serializers.CharField(source="user.student_id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user_id",
            "student_id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "department",
            "course",
            "year",
            "cgpa",
            "skills",
            "resume",
            "github_url",
            "linkedin_url",
            "instagram_url",
            "portfolio_url",
            "date_of_birth",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class JobListingSerializer(serializers.ModelSerializer):
    """
    Serializer for Company creating, viewing, and updating its own Job Listings.
    Enforces that companies can only submit jobs for themselves and cannot self-approve.
    """

    company_name = serializers.CharField(source="company.company_name", read_only=True)
    company_id = serializers.IntegerField(source="company.id", read_only=True)

    class Meta:
        model = JobListing
        fields = [
            "id",
            "company_id",
            "company_name",
            "job_title",
            "description",
            "job_type",
            "salary",
            "job_location",
            "minimum_cgpa",
            "eligible_departments",
            "eligible_courses",
            "application_deadline",
            "status",
            "approval_remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "company_id", "company_name", "approval_remarks", "created_at", "updated_at"]

    def validate_minimum_cgpa(self, value):
        if value < Decimal("0.00") or value > Decimal("10.00"):
            raise serializers.ValidationError("Minimum CGPA must be between 0.00 and 10.00.")
        return value

    def validate_application_deadline(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Application deadline must be a future date and time.")
        return value

    def validate_status(self, value):
        allowed_company_statuses = [
            JobListing.JobStatus.DRAFT,
            JobListing.JobStatus.PENDING_TPO_APPROVAL,
        ]
        if value not in allowed_company_statuses:
            raise serializers.ValidationError(
                f"Companies can only set status to 'DRAFT' or 'PENDING_TPO_APPROVAL'. Cannot set '{value}'."
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "company_profile"):
            raise serializers.ValidationError(
                {"detail": "You must create a company profile before posting job drives."}
            )
        validated_data["company"] = user.company_profile
        if "status" not in validated_data:
            validated_data["status"] = JobListing.JobStatus.PENDING_TPO_APPROVAL
        return super().create(validated_data)


class TPOJobListingSerializer(serializers.ModelSerializer):
    """
    Serializer for TPO viewing job listings.
    Includes full company overview and approval status.
    """

    company_id = serializers.IntegerField(source="company.id", read_only=True)
    company_name = serializers.CharField(source="company.company_name", read_only=True)
    company_email = serializers.EmailField(source="company.contact_email", read_only=True)
    company_location = serializers.CharField(source="company.location", read_only=True)
    company_industry = serializers.CharField(source="company.industry", read_only=True)

    class Meta:
        model = JobListing
        fields = [
            "id",
            "company_id",
            "company_name",
            "company_email",
            "company_location",
            "company_industry",
            "job_title",
            "description",
            "job_type",
            "salary",
            "job_location",
            "minimum_cgpa",
            "eligible_departments",
            "eligible_courses",
            "application_deadline",
            "status",
            "approval_remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TPOJobVerifySerializer(serializers.Serializer):
    """
    Serializer for TPO approving or rejecting a job listing.
    """

    status = serializers.ChoiceField(
        choices=["APPROVED", "REJECTED"],
        error_messages={
            "invalid_choice": "Status must be either 'APPROVED' or 'REJECTED'."
        },
    )
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        if "remarks" in validated_data:
            instance.approval_remarks = validated_data["remarks"]
        instance.save()
        return instance


class StudentJobListingSerializer(serializers.ModelSerializer):
    """
    Serializer for Students browsing approved job listings.
    Computes eligibility status for the requesting student dynamically.
    """

    company_name = serializers.CharField(source="company.company_name", read_only=True)
    company_website = serializers.URLField(source="company.website", read_only=True)
    is_eligible = serializers.SerializerMethodField()
    eligibility_reasons = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()

    class Meta:
        model = JobListing
        fields = [
            "id",
            "company_name",
            "company_website",
            "job_title",
            "description",
            "job_type",
            "salary",
            "job_location",
            "minimum_cgpa",
            "eligible_departments",
            "eligible_courses",
            "application_deadline",
            "status",
            "is_eligible",
            "eligibility_reasons",
            "has_applied",
            "created_at",
        ]
        read_only_fields = fields

    def _check_eligibility(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request.user, "student_profile"):
            return False, ["Student profile not found."]
        student = request.user.student_profile
        reasons = []

        if student.cgpa < obj.minimum_cgpa:
            reasons.append(f"Your CGPA ({student.cgpa}) is below required minimum of {obj.minimum_cgpa}.")

        if obj.eligible_departments:
            s_dept = student.department.strip().lower()
            match = any(
                s_dept == d.strip().lower() or d.strip().lower() in s_dept or s_dept in d.strip().lower()
                for d in obj.eligible_departments
            )
            if not match:
                reasons.append(
                    f"Your department '{student.department}' is not in eligible departments ({', '.join(obj.eligible_departments)})."
                )

        if obj.eligible_courses:
            s_course = student.course.strip().lower()
            c_match = any(
                s_course == c.strip().lower() or c.strip().lower() in s_course or s_course in c.strip().lower()
                for c in obj.eligible_courses
            )
            if not c_match:
                reasons.append(
                    f"Your course '{student.course}' is not in eligible courses ({', '.join(obj.eligible_courses)})."
                )

        if timezone.now() > obj.application_deadline:
            reasons.append("Application deadline has passed.")

        return len(reasons) == 0, reasons

    def get_is_eligible(self, obj):
        is_eligible, _ = self._check_eligibility(obj)
        return is_eligible

    def get_eligibility_reasons(self, obj):
        _, reasons = self._check_eligibility(obj)
        return reasons

    def get_has_applied(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request.user, "student_profile"):
            return False
        return obj.applications.filter(student=request.user.student_profile).exists()


class StudentApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for Students viewing their own job applications.
    """

    job_id = serializers.IntegerField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    company_name = serializers.CharField(source="job.company.company_name", read_only=True)
    job_location = serializers.CharField(source="job.job_location", read_only=True)
    salary = serializers.DecimalField(source="job.salary", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "job_id",
            "job_title",
            "company_name",
            "job_location",
            "salary",
            "status",
            "applied_at",
            "updated_at",
        ]
        read_only_fields = fields


class CompanyApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for Companies viewing applicants to their job listing.
    """

    student_id = serializers.CharField(source="student.user.student_id", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    email = serializers.EmailField(source="student.user.email", read_only=True)
    phone_number = serializers.CharField(source="student.user.phone_number", read_only=True)
    department = serializers.CharField(source="student.department", read_only=True)
    course = serializers.CharField(source="student.course", read_only=True)
    year = serializers.IntegerField(source="student.year", read_only=True)
    cgpa = serializers.DecimalField(source="student.cgpa", max_digits=4, decimal_places=2, read_only=True)
    skills = serializers.CharField(source="student.skills", read_only=True)
    resume = serializers.FileField(source="student.resume", read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "student_id",
            "student_name",
            "email",
            "phone_number",
            "department",
            "course",
            "year",
            "cgpa",
            "skills",
            "resume",
            "status",
            "applied_at",
            "updated_at",
        ]
        read_only_fields = fields


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for Company updating application status.
    Enforces valid workflow status transitions:
    - APPLIED -> SHORTLISTED | REJECTED
    - SHORTLISTED -> SELECTED | REJECTED
    - SELECTED -> REJECTED
    - REJECTED cannot transition to anything
    """

    status = serializers.ChoiceField(
        choices=[
            JobApplication.ApplicationStatus.SHORTLISTED,
            JobApplication.ApplicationStatus.SELECTED,
            JobApplication.ApplicationStatus.REJECTED,
        ],
        error_messages={
            "invalid_choice": "Allowed status updates are 'SHORTLISTED', 'SELECTED', or 'REJECTED'."
        },
    )

    def validate_status(self, new_status):
        instance = self.context.get("application")
        if not instance:
            return new_status

        current_status = instance.status

        if current_status == new_status:
            raise serializers.ValidationError(
                f"Application is already marked as '{current_status}'."
            )

        if current_status == JobApplication.ApplicationStatus.REJECTED:
            raise serializers.ValidationError(
                "Cannot alter status: this application has already been rejected."
            )

        if current_status == JobApplication.ApplicationStatus.APPLIED:
            if new_status not in [JobApplication.ApplicationStatus.SHORTLISTED, JobApplication.ApplicationStatus.REJECTED]:
                raise serializers.ValidationError(
                    f"Invalid transition: Cannot transition from 'APPLIED' directly to '{new_status}'. You must shortlist the applicant first."
                )

        elif current_status == JobApplication.ApplicationStatus.SHORTLISTED:
            if new_status not in [JobApplication.ApplicationStatus.SELECTED, JobApplication.ApplicationStatus.REJECTED]:
                raise serializers.ValidationError(
                    f"Invalid transition: Cannot transition from 'SHORTLISTED' to '{new_status}'."
                )

        elif current_status == JobApplication.ApplicationStatus.SELECTED:
            if new_status != JobApplication.ApplicationStatus.REJECTED:
                raise serializers.ValidationError(
                    f"Invalid transition: A selected candidate can only transition to 'REJECTED' if revoked, cannot revert to '{new_status}'."
                )

        return new_status

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.save()
        return instance


class InterviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Company scheduling and managing Interviews.
    """

    application_id = serializers.IntegerField(source="application.id", read_only=True)
    job_title = serializers.CharField(source="application.job.job_title", read_only=True)
    student_name = serializers.CharField(source="application.student.user.full_name", read_only=True)
    student_id = serializers.CharField(source="application.student.user.student_id", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "application_id",
            "job_title",
            "student_id",
            "student_name",
            "round",
            "interview_type",
            "scheduled_at",
            "venue",
            "meeting_link",
            "interviewer",
            "status",
            "feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "application_id", "job_title", "student_id", "student_name", "created_at", "updated_at"]

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Interview must be scheduled for a future date and time.")
        return value

    def validate(self, attrs):
        interview_type = attrs.get("interview_type", Interview.InterviewType.ONLINE)
        venue = attrs.get("venue", "").strip()
        meeting_link = attrs.get("meeting_link", "").strip()

        if interview_type == Interview.InterviewType.ONLINE:
            if not meeting_link:
                raise serializers.ValidationError(
                    {"meeting_link": "A meeting link is required for online interviews."}
                )
        elif interview_type == Interview.InterviewType.OFFLINE:
            if not venue:
                raise serializers.ValidationError(
                    {"venue": "A physical venue is required for offline interviews."}
                )

        return attrs


class InterviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Company updating an existing interview (status, feedback, rescheduled time, link/venue).
    """

    class Meta:
        model = Interview
        fields = [
            "id",
            "round",
            "interview_type",
            "scheduled_at",
            "venue",
            "meeting_link",
            "interviewer",
            "status",
            "feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        interview_type = attrs.get(
            "interview_type",
            self.instance.interview_type if self.instance else Interview.InterviewType.ONLINE,
        )
        venue = attrs.get("venue", self.instance.venue if self.instance else "").strip()
        meeting_link = attrs.get("meeting_link", self.instance.meeting_link if self.instance else "").strip()

        if interview_type == Interview.InterviewType.ONLINE and not meeting_link:
            raise serializers.ValidationError(
                {"meeting_link": "A meeting link is required for online interviews."}
            )
        elif interview_type == Interview.InterviewType.OFFLINE and not venue:
            raise serializers.ValidationError(
                {"venue": "A physical venue is required for offline interviews."}
            )

        return attrs


class StudentInterviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Students viewing their scheduled and completed interviews.
    """

    company_name = serializers.CharField(source="application.job.company.company_name", read_only=True)
    job_title = serializers.CharField(source="application.job.job_title", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "company_name",
            "job_title",
            "round",
            "interview_type",
            "scheduled_at",
            "venue",
            "meeting_link",
            "interviewer",
            "status",
            "feedback",
            "created_at",
        ]
        read_only_fields = fields


class JobOfferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for Company extending an offer to a selected applicant.
    """

    class Meta:
        model = JobOffer
        fields = [
            "id",
            "offer_letter_number",
            "ctc",
            "joining_date",
            "offer_details",
            "status",
            "issued_at",
        ]
        read_only_fields = ["id", "status", "issued_at"]

    def validate_ctc(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("CTC must be a positive number greater than 0.")
        return value

    def validate_joining_date(self, value):
        if value <= timezone.now().date():
            raise serializers.ValidationError("Joining date must be in the future.")
        return value


class JobOfferSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing Job Offers (Student and Company).
    """

    application_id = serializers.IntegerField(source="application.id", read_only=True)
    job_title = serializers.CharField(source="application.job.job_title", read_only=True)
    company_name = serializers.CharField(source="application.job.company.company_name", read_only=True)
    student_id = serializers.CharField(source="application.student.user.student_id", read_only=True)
    student_name = serializers.CharField(source="application.student.user.full_name", read_only=True)

    class Meta:
        model = JobOffer
        fields = [
            "id",
            "application_id",
            "job_title",
            "company_name",
            "student_id",
            "student_name",
            "offer_letter_number",
            "ctc",
            "joining_date",
            "offer_details",
            "status",
            "issued_at",
            "responded_at",
        ]
        read_only_fields = fields


class OfferResponseSerializer(serializers.Serializer):
    """
    Serializer for Student responding to an offer (ACCEPTED or REJECTED).
    """

    status = serializers.ChoiceField(
        choices=["ACCEPTED", "REJECTED"],
        error_messages={
            "invalid_choice": "Status response must be either 'ACCEPTED' or 'REJECTED'."
        },
    )


class PlacementRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for TPO viewing final placement records.
    """

    student_id = serializers.CharField(source="student.user.student_id", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    email = serializers.EmailField(source="student.user.email", read_only=True)
    department = serializers.CharField(source="student.department", read_only=True)
    course = serializers.CharField(source="student.course", read_only=True)
    company_name = serializers.CharField(source="company.company_name", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    offer_letter_number = serializers.CharField(source="offer.offer_letter_number", read_only=True)

    class Meta:
        model = PlacementRecord
        fields = [
            "id",
            "student_id",
            "student_name",
            "email",
            "department",
            "course",
            "company_name",
            "job_title",
            "offer_letter_number",
            "ctc",
            "joining_date",
            "placement_status",
            "placed_at",
        ]
        read_only_fields = fields



