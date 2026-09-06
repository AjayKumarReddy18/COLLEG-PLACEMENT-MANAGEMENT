from django.contrib import admin
from .models import (
    CompanyProfile,
    Interview,
    JobApplication,
    JobListing,
    JobOffer,
    PlacementRecord,
    StudentProfile,
)



@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "get_student_id",
        "get_full_name",
        "department",
        "course",
        "year",
        "cgpa",
        "has_resume",
        "created_at",
    )
    list_filter = ("department", "course", "year")
    search_fields = (
        "user__student_id",
        "user__email",
        "user__first_name",
        "user__last_name",
        "department",
        "skills",
    )
    ordering = ("-created_at",)

    @admin.display(description="Student ID", ordering="user__student_id")
    def get_student_id(self, obj):
        return obj.user.student_id

    @admin.display(description="Name", ordering="user__first_name")
    def get_full_name(self, obj):
        return obj.user.full_name

    @admin.display(boolean=True, description="Resume Uploaded")
    def has_resume(self, obj):
        return bool(obj.resume)


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "get_user_email",
        "industry",
        "location",
        "verification_status",
        "created_at",
    )
    list_filter = ("verification_status", "industry")
    search_fields = (
        "company_name",
        "user__email",
        "industry",
        "location",
    )
    list_editable = ("verification_status",)
    ordering = ("-created_at",)

    @admin.display(description="Account Email", ordering="user__email")
    def get_user_email(self, obj):
        return obj.user.email


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = (
        "job_title",
        "get_company_name",
        "job_type",
        "salary",
        "job_location",
        "minimum_cgpa",
        "status",
        "application_deadline",
        "created_at",
    )
    list_filter = ("status", "job_type", "created_at")
    search_fields = ("job_title", "company__company_name", "job_location", "description")
    ordering = ("-created_at",)

    @admin.display(description="Company", ordering="company__company_name")
    def get_company_name(self, obj):
        return obj.company.company_name


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "get_student_name",
        "get_job_title",
        "get_company_name",
        "status",
        "applied_at",
    )
    list_filter = ("status", "applied_at")
    search_fields = (
        "student__user__student_id",
        "student__user__first_name",
        "student__user__last_name",
        "job__job_title",
        "job__company__company_name",
    )
    ordering = ("-applied_at",)

    @admin.display(description="Student", ordering="student__user__first_name")
    def get_student_name(self, obj):
        return obj.student.user.full_name or obj.student.user.email

    @admin.display(description="Job", ordering="job__job_title")
    def get_job_title(self, obj):
        return obj.job.job_title

    @admin.display(description="Company", ordering="job__company__company_name")
    def get_company_name(self, obj):
        return obj.job.company.company_name


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "round",
        "interview_type",
        "scheduled_at",
        "status",
        "interviewer",
    )
    list_filter = ("status", "interview_type", "round")
    search_fields = (
        "application__student__user__first_name",
        "application__student__user__last_name",
        "application__job__job_title",
        "application__job__company__company_name",
        "interviewer",
    )
    ordering = ["-scheduled_at"]


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = (
        "offer_letter_number",
        "get_student_name",
        "get_company_name",
        "ctc",
        "joining_date",
        "status",
        "issued_at",
    )
    list_filter = ("status", "joining_date")
    search_fields = (
        "offer_letter_number",
        "application__student__user__first_name",
        "application__student__user__last_name",
        "application__job__company__company_name",
    )
    ordering = ["-issued_at"]

    @admin.display(description="Student")
    def get_student_name(self, obj):
        return obj.application.student.user.full_name

    @admin.display(description="Company")
    def get_company_name(self, obj):
        return obj.application.job.company.company_name


@admin.register(PlacementRecord)
class PlacementRecordAdmin(admin.ModelAdmin):
    list_display = (
        "get_student_name",
        "get_company_name",
        "get_job_title",
        "ctc",
        "joining_date",
        "placement_status",
        "placed_at",
    )
    list_filter = ("placement_status", "placed_at")
    search_fields = (
        "student__user__first_name",
        "student__user__last_name",
        "student__user__student_id",
        "company__company_name",
        "job__job_title",
    )
    ordering = ["-placed_at"]

    @admin.display(description="Student")
    def get_student_name(self, obj):
        return obj.student.user.full_name

    @admin.display(description="Company")
    def get_company_name(self, obj):
        return obj.company.company_name

    @admin.display(description="Job")
    def get_job_title(self, obj):
        return obj.job.job_title


