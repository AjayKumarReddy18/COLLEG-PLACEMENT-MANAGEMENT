from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validate_instagram_url, validate_resume_file


class StudentProfile(models.Model):
    """
    Profile model for Students.
    Strictly linked 1:1 to a User with role STUDENT.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name="User Account",
    )
    department = models.CharField(
        max_length=100,
        help_text="Academic Department (e.g. Computer Science, Mechanical)",
    )
    course = models.CharField(
        max_length=100,
        help_text="Degree/Course (e.g. B.Tech, M.Tech, MCA)",
    )
    year = models.PositiveIntegerField(
        help_text="Current Year of Study or Graduation Year (e.g. 4 or 2026)",
    )
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("10.00"))],
        help_text="Cumulative Grade Point Average (0.00 - 10.00)",
    )
    skills = models.TextField(
        blank=True,
        help_text="Technical & professional skills (comma-separated or list)",
    )
    resume = models.FileField(
        upload_to="resumes/",
        null=True,
        blank=True,
        validators=[validate_resume_file],
        help_text="Upload resume in PDF, DOC, or DOCX format (Max 5MB)",
    )
    github_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="GitHub profile URL",
    )
    linkedin_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="LinkedIn profile URL",
    )
    instagram_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        validators=[validate_instagram_url],
        help_text="Instagram profile URL (Optional, e.g. https://www.instagram.com/username/)",
    )
    portfolio_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Personal Portfolio or Website URL",
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Date of Birth (Optional, YYYY-MM-DD)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.user and self.user.role != "STUDENT":
            raise ValidationError(
                {"user": "Only users with role 'STUDENT' can have a StudentProfile."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.full_name or self.user.email} - {self.course} ({self.department})"


class CompanyProfile(models.Model):
    """
    Profile model for Companies.
    Strictly linked 1:1 to a User with role COMPANY.
    Contains verification status controlled exclusively by TPOs.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_profile",
        verbose_name="User Account",
    )
    company_name = models.CharField(
        max_length=200,
        verbose_name="Company Name",
    )
    company_description = models.TextField(
        blank=True,
        verbose_name="Company Description",
    )
    industry = models.CharField(
        max_length=100,
        help_text="Industry sector (e.g. Information Technology, Finance, Healthcare)",
    )
    website = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Official company website",
    )
    location = models.CharField(
        max_length=200,
        help_text="Headquarters or branch location (e.g. Bengaluru, India)",
    )
    contact_email = models.EmailField(
        verbose_name="HR / Contact Email",
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Contact Phone",
    )
    company_size = models.CharField(
        max_length=50,
        blank=True,
        help_text="Number of employees (e.g. '1-50', '51-200', '201-1000', '1000+')",
    )
    logo = models.ImageField(
        upload_to="company_logos/",
        null=True,
        blank=True,
        help_text="Company logo image",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        verbose_name="Verification Status",
        help_text="TPO Verification Status (PENDING, APPROVED, REJECTED)",
    )
    verification_remarks = models.TextField(
        blank=True,
        verbose_name="Verification Remarks",
        help_text="Feedback or remarks by TPO during verification",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Profile"
        verbose_name_plural = "Company Profiles"
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.user and self.user.role != "COMPANY":
            raise ValidationError(
                {"user": "Only users with role 'COMPANY' can have a CompanyProfile."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company_name} ({self.get_verification_status_display()})"


class JobListing(models.Model):
    """
    Placement Drive / Job Posting created by a Company.
    Reviewed and approved by TPO before becoming visible to students.
    """

    class JobType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full Time"
        INTERNSHIP = "INTERNSHIP", "Internship"
        PART_TIME = "PART_TIME", "Part Time"

    class JobStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_TPO_APPROVAL = "PENDING_TPO_APPROVAL", "Pending TPO Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CLOSED = "CLOSED", "Closed"

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="job_listings",
        verbose_name="Company Profile",
    )
    job_title = models.CharField(
        max_length=200,
        verbose_name="Job Title",
    )
    description = models.TextField(
        verbose_name="Job Description",
    )
    job_type = models.CharField(
        max_length=50,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
        verbose_name="Job Type",
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Salary / CTC (in INR)",
        help_text="Annual CTC or monthly stipend in INR",
    )
    job_location = models.CharField(
        max_length=150,
        verbose_name="Job Location",
        help_text="e.g. Bengaluru, Remote, Hyderabad",
    )
    minimum_cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("10.00"))],
        verbose_name="Minimum CGPA",
        help_text="Minimum CGPA required to apply (0.00 - 10.00)",
    )
    eligible_departments = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Eligible Departments",
        help_text="List of eligible department names, e.g. ['CSE', 'IT']",
    )
    eligible_courses = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Eligible Courses",
        help_text="List of eligible degrees/courses, e.g. ['B.Tech', 'M.Tech']",
    )
    application_deadline = models.DateTimeField(
        verbose_name="Application Deadline",
    )
    status = models.CharField(
        max_length=30,
        choices=JobStatus.choices,
        default=JobStatus.PENDING_TPO_APPROVAL,
        verbose_name="Status",
    )
    approval_remarks = models.TextField(
        blank=True,
        default="",
        verbose_name="TPO Approval Remarks",
        help_text="Feedback or remarks from TPO during approval",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Job Listing"
        verbose_name_plural = "Job Listings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_title} @ {self.company.company_name} ({self.status})"


class JobApplication(models.Model):
    """
    Application submitted by a Student for an approved JobListing.
    """

    class ApplicationStatus(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        REJECTED = "REJECTED", "Rejected"
        SELECTED = "SELECTED", "Selected"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="Student",
    )
    job = models.ForeignKey(
        JobListing,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="Job Listing",
    )
    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.APPLIED,
        verbose_name="Application Status",
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Job Application"
        verbose_name_plural = "Job Applications"
        unique_together = ("student", "job")
        ordering = ["-applied_at"]

    def __str__(self):
        student_name = self.student.user.full_name or self.student.user.email
        return f"{student_name} -> {self.job.job_title} ({self.status})"


class Interview(models.Model):
    """
    Interview round scheduled by a Company for a shortlisted JobApplication.
    """

    class InterviewType(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        OFFLINE = "OFFLINE", "Offline"

    class InterviewStatus(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interviews",
        verbose_name="Job Application",
    )
    round = models.PositiveIntegerField(
        default=1,
        verbose_name="Interview Round Number",
    )
    interview_type = models.CharField(
        max_length=20,
        choices=InterviewType.choices,
        default=InterviewType.ONLINE,
        verbose_name="Interview Type",
    )
    scheduled_at = models.DateTimeField(
        verbose_name="Scheduled Date & Time",
    )
    venue = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Physical Venue",
        help_text="Required for OFFLINE interviews",
    )
    meeting_link = models.URLField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Online Meeting Link",
        help_text="Required for ONLINE interviews",
    )
    interviewer = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Interviewer Name / Panel",
    )
    status = models.CharField(
        max_length=20,
        choices=InterviewStatus.choices,
        default=InterviewStatus.SCHEDULED,
        verbose_name="Interview Status",
    )
    feedback = models.TextField(
        blank=True,
        default="",
        verbose_name="Interview Feedback / Assessment",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Interview"
        verbose_name_plural = "Interviews"
        unique_together = ("application", "round")
        ordering = ["round", "scheduled_at"]

    def __str__(self):
        return f"Round {self.round} ({self.interview_type}) for {self.application}"


class JobOffer(models.Model):
    """
    Formal job offer extended by a Company to a selected applicant.
    """

    class OfferStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="offer",
        verbose_name="Job Application",
    )
    offer_letter_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Offer Letter / Reference Number",
    )
    ctc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Annual CTC (in INR)",
    )
    joining_date = models.DateField(
        verbose_name="Expected Date of Joining",
    )
    offer_details = models.TextField(
        blank=True,
        default="",
        verbose_name="Offer Details / Terms",
    )
    status = models.CharField(
        max_length=20,
        choices=OfferStatus.choices,
        default=OfferStatus.PENDING,
        verbose_name="Offer Status",
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Job Offer"
        verbose_name_plural = "Job Offers"
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Offer {self.offer_letter_number} - {self.application} ({self.status})"


class PlacementRecord(models.Model):
    """
    Final placement record generated when a student accepts a job offer.
    Used for campus placement analytics and TPO reporting.
    """

    class PlacementStatus(models.TextChoices):
        PLACED = "PLACED", "Placed"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="placement_records",
        verbose_name="Student",
    )
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="placement_records",
        verbose_name="Company",
    )
    job = models.ForeignKey(
        JobListing,
        on_delete=models.CASCADE,
        related_name="placement_records",
        verbose_name="Job Listing",
    )
    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="placement_record",
        verbose_name="Job Application",
    )
    offer = models.OneToOneField(
        JobOffer,
        on_delete=models.CASCADE,
        related_name="placement_record",
        verbose_name="Job Offer",
    )
    placement_status = models.CharField(
        max_length=20,
        choices=PlacementStatus.choices,
        default=PlacementStatus.PLACED,
        verbose_name="Placement Status",
    )
    placed_at = models.DateTimeField(auto_now_add=True)
    joining_date = models.DateField(
        verbose_name="Joining Date",
    )
    ctc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Annual CTC (in INR)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Placement Record"
        verbose_name_plural = "Placement Records"
        ordering = ["-placed_at"]

    def __str__(self):
        student_name = self.student.user.full_name or self.student.user.email
        return f"{student_name} placed at {self.company.company_name} - CTC: {self.ctc}"


