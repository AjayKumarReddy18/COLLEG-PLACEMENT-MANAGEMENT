from django.urls import path

from .views import (
    CompanyApplicationStatusView,
    CompanyInterviewCreateListView,
    CompanyInterviewDetailView,
    CompanyJobApplicationsView,
    CompanyJobDetailView,
    CompanyJobListView,
    CompanyOfferCreateView,
    CompanyProfileView,
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    StudentApplicationListView,
    StudentCompanyListView,
    StudentDashboardStatsView,
    StudentInterviewListView,
    StudentJobApplyView,
    StudentJobListView,
    StudentOfferListView,
    StudentOfferRespondView,
    StudentProfileView,
    TPOCompanyDetailView,
    TPOCompanyListView,
    TPOCompanyVerifyView,
    TPOApplicationListView,
    TPOInterviewListView,
    TPOJobListView,
    TPOOfferListView,
    TPOJobVerifyView,
    TPOPlacementListView,
    TPOPlacementDriveDetailView,
    TPOPlacementDriveListCreateView,
    TPOPlacementRecordUpdateView,
    TPOPlacementSummaryView,
    TPOStudentListView,
)

urlpatterns = [
    # Stage 3: Self-profile management
    path("student/profile/", StudentProfileView.as_view(), name="student-profile"),
    path("student/dashboard-stats/", StudentDashboardStatsView.as_view(), name="student-dashboard-stats"),
    path("student/companies/", StudentCompanyListView.as_view(), name="student-company-list"),
    path("company/profile/", CompanyProfileView.as_view(), name="company-profile"),

    # Stage 4: TPO Company & Student management
    path("tpo/companies/", TPOCompanyListView.as_view(), name="tpo-company-list"),
    path("tpo/companies/<int:pk>/", TPOCompanyDetailView.as_view(), name="tpo-company-detail"),
    path("tpo/companies/<int:pk>/verify/", TPOCompanyVerifyView.as_view(), name="tpo-company-verify"),
    path("tpo/students/", TPOStudentListView.as_view(), name="tpo-student-list"),

    # Stage 5: Company Job Management
    path("company/jobs/", CompanyJobListView.as_view(), name="company-job-list"),
    path("company/jobs/<int:pk>/", CompanyJobDetailView.as_view(), name="company-job-detail"),
    path("company/jobs/<int:pk>/applications/", CompanyJobApplicationsView.as_view(), name="company-job-applications"),

    # Stage 5: TPO Job Verification & Listing
    path("tpo/jobs/", TPOJobListView.as_view(), name="tpo-job-list"),
    path("tpo/applications/", TPOApplicationListView.as_view(), name="tpo-application-list"),
    path("tpo/interviews/", TPOInterviewListView.as_view(), name="tpo-interview-list"),
    path("tpo/offers/", TPOOfferListView.as_view(), name="tpo-offer-list"),
    path("tpo/jobs/<int:pk>/verify/", TPOJobVerifyView.as_view(), name="tpo-job-verify"),
    path("tpo/jobs/<int:pk>/approve/", TPOJobVerifyView.as_view(), name="tpo-job-approve"),

    # Stage 5: Student Job Browsing & Application Pipeline
    path("student/jobs/", StudentJobListView.as_view(), name="student-job-list"),
    path("student/jobs/<int:pk>/apply/", StudentJobApplyView.as_view(), name="student-job-apply"),
    path("student/applications/", StudentApplicationListView.as_view(), name="student-application-list"),

    # Stage 6: Company Shortlisting & Application Status Updates
    path("company/applications/<int:pk>/status/", CompanyApplicationStatusView.as_view(), name="company-application-status"),

    # Stage 6: Interview Management
    path("company/applications/<int:pk>/interviews/", CompanyInterviewCreateListView.as_view(), name="company-application-interviews"),
    path("company/interviews/<int:pk>/", CompanyInterviewDetailView.as_view(), name="company-interview-detail"),
    path("student/interviews/", StudentInterviewListView.as_view(), name="student-interview-list"),

    # Stage 6: Job Offer Workflow
    path("company/applications/<int:pk>/offer/", CompanyOfferCreateView.as_view(), name="company-application-offer"),
    path("student/offers/", StudentOfferListView.as_view(), name="student-offer-list"),
    path("student/offers/<int:pk>/respond/", StudentOfferRespondView.as_view(), name="student-offer-respond"),

    # Stage 6: TPO Placements & Analytics
    path("tpo/placements/", TPOPlacementListView.as_view(), name="tpo-placement-list"),
    path("tpo/placements/<int:pk>/", TPOPlacementRecordUpdateView.as_view(), name="tpo-placement-update"),
    path("tpo/placements/summary/", TPOPlacementSummaryView.as_view(), name="tpo-placement-summary"),
    path("tpo/placement-drives/", TPOPlacementDriveListCreateView.as_view(), name="tpo-placement-drive-list"),
    path("tpo/placement-drives/<int:pk>/", TPOPlacementDriveDetailView.as_view(), name="tpo-placement-drive-detail"),
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/read-all/", NotificationReadAllView.as_view(), name="notification-read-all"),
    path("notifications/<int:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
]



