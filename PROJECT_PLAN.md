# College Placement Management System - Project Plan

A modern, role-based College Placement Management System built with **React.js**, **Django REST Framework**, and **MySQL**.

---

## 👥 User Roles (Strictly 3 Roles - No ADMIN Role)
1. **STUDENT**: Registers, builds profile, browses approved jobs, applies, receives interview schedules and offers.
2. **COMPANY**: Registers, gets approved by TPO, posts job drives, shortlists applicants, schedules interviews, issues offers.
3. **TPO (Training & Placement Officer)**: Approves companies, approves job listings, monitors placement drives, and tracks campus analytics.

---

## 🔄 System Workflow
```
Student Registration
    └── Student Profile
Company Registration
    └── TPO Approves Company
         └── Company Posts Job
              └── TPO Approves Job
                   └── Student Applies
                        └── Company Shortlists Student
                             └── Interview Scheduling
                                  └── Job Offer Issued
                                       └── Student Accepts Offer
                                            └── Final Placement Recorded
```

---

## 📋 Implementation Stages

### ✅ Stage 1: Authentication & User Model Foundation (Completed)
- [x] Initial workspace inspection and clean project structure setup (`backend/`).
- [x] Custom Django `User` model with strict role choices (`STUDENT`, `COMPANY`, `TPO`).
- [x] Secure password hashing using Django authentication framework.
- [x] Fields for `student_id` (College ID), `email`, `first_name`, `last_name`, `phone_number`, `role`, timestamps.
- [x] Database configuration supporting MySQL (via PyMySQL) and environment variables (`.env`).
- [x] Django Admin registration for development and testing inspection.
- [x] Initial migrations created and 100% verified with unit tests.

---

### ✅ Stage 2: Authentication APIs & JWT Setup (Completed)
- [x] SimpleJWT integration with access and refresh tokens (`djangorestframework-simplejwt`).
- [x] Public Student Registration API (`POST /api/auth/register/student/`):
  - Requires `email`, `password`, `password_confirm`, `student_id`, `first_name`, `last_name`, `phone_number`.
  - Enforces unique email and student ID, password complexity, and auto-assigns `role = STUDENT`.
- [x] Public Company Registration API (`POST /api/auth/register/company/`):
  - Requires `email`, `password`, `password_confirm`, `first_name`, `last_name`, `phone_number`.
  - Enforces unique email, password complexity, and auto-assigns `role = COMPANY`.
- [x] Secure TPO Creation:
  - Intentionally no public registration endpoint; managed via `createsuperuser` or management scripts.
- [x] Unified Login API (`POST /api/auth/login/`):
  - Student Login supports `Student ID + Password` OR `Email + Password`.
  - Company & TPO Login supports `Email + Password`.
  - Issues JWT access token, refresh token, and sanitized user object.
- [x] Token Refresh API (`POST /api/auth/token/refresh/`).
- [x] Current Authenticated User API (`GET /api/auth/me/`).
- [x] Role-Based Permission Classes (`IsStudent`, `IsCompany`, `IsTPO` in `backend/users/permissions.py`).
- [x] 100% test coverage with 30 automated unit tests covering models, serializers, views, tokens, and permissions.

---

### ✅ Stage 3: Student Profile & Company Profile Modules (Completed)
- [x] Dedicated `profiles` app created with clean separation from `users` (authentication).
- [x] `StudentProfile` model (OneToOne to User):
  - Fields: `department`, `course`, `year`, `cgpa`, `skills`, `resume` (PDF/DOC/DOCX upload), `github_url`, `linkedin_url`, `instagram_url`, `portfolio_url`, `date_of_birth`, timestamps.
  - Resume file validation (PDF, DOC, DOCX only; max 5MB).
  - Instagram URL validation (optional, can be added/updated/removed).
- [x] `CompanyProfile` model (OneToOne to User):
  - Fields: `company_name`, `company_description`, `industry`, `website`, `location`, `contact_email`, `contact_phone`, `company_size`, `logo`, `verification_status`, timestamps.
  - Verification status (`PENDING`/`APPROVED`/`REJECTED`) is read-only in company API – controlled only by future TPO workflow.
- [x] REST APIs:
  - `GET/POST/PUT/PATCH /api/student/profile/` — Student self-profile management.
  - `GET/POST/PUT/PATCH /api/company/profile/` — Company self-profile management.
- [x] Role-based access enforcement using existing `IsStudent`, `IsCompany` permissions.
- [x] Django Admin registration for both profile models.
- [x] Comprehensive test suite covering profile CRUD, resume upload, Instagram URL, verification status protection, cross-role and data isolation.

---

### ✅ Stage 4: TPO Approval Workflows & Management (Completed)
- [x] `verification_remarks` field added to `CompanyProfile` with migration for TPO feedback.
- [x] TPO Company List API (`GET /api/tpo/companies/`):
  - Accessible strictly by authenticated TPO users (`IsTPO`).
  - Returns registered companies with account details and verification status.
  - Supports query parameter filtering: `?verification_status=PENDING | APPROVED | REJECTED`.
- [x] TPO Company Detail API (`GET /api/tpo/companies/<id>/`):
  - Detailed company overview, user metadata, current verification status, and remarks.
- [x] TPO Company Verification API (`PATCH /api/tpo/companies/<id>/verify/`):
  - Allows TPO to `APPROVE` or `REJECT` company registration.
  - Validates allowed statuses and saves official feedback/remarks.
  - Strictly denies self-approval by companies or modification by students.
- [x] TPO Student Management API (`GET /api/tpo/students/`):
  - Accessible strictly by authenticated TPO users (`IsTPO`).
  - Full academic and contact directory for placement coordination.
  - Filtering by `department` (case-insensitive search), `course`, and `min_cgpa` threshold.
- [x] Fast test suite execution via `MD5PasswordHasher` configuration for unit tests.
- [x] 100% automated test suite with 26 new tests (82 tests passing project-wide in ~2 seconds).


---

### ✅ Stage 5: Job Posting & Application Pipeline (Completed)
- [x] `JobListing` model with fields for title, description, job type, salary/CTC, location, minimum CGPA, eligible departments/courses, deadline, status choices (`DRAFT`, `PENDING_TPO_APPROVAL`, `APPROVED`, `REJECTED`, `CLOSED`), and TPO approval remarks.
- [x] `JobApplication` model with student reference, job reference, status choices (`APPLIED`, `SHORTLISTED`, `REJECTED`, `SELECTED`), timestamps, and unique composite constraint preventing duplicate applications.
- [x] Company Job Creation API (`POST /api/company/jobs/`):
  - Requires company profile; prevents self-approval or assigning other companies; validates future deadline and CGPA bounds.
- [x] Company Job Management APIs (`GET /api/company/jobs/`, `GET/PUT/PATCH /api/company/jobs/<id>/`):
  - Strict isolation: companies only see and manage their own jobs; cannot self-approve.
- [x] Company Applicant Review API (`GET /api/company/jobs/<id>/applications/`):
  - Accessible only by the job's owning company; returns detailed student academic and resume info.
- [x] TPO Job Review & Verification APIs (`GET /api/tpo/jobs/`, `PATCH /api/tpo/jobs/<id>/verify/`):
  - Filtering by status; approves or rejects jobs with official remarks.
- [x] Student Job Browsing API (`GET /api/student/jobs/`):
  - Strictly surfaces approved jobs; calculates real-time eligibility (`is_eligible`, `eligibility_reasons`, `has_applied`).
- [x] Student Application API (`POST /api/student/jobs/<id>/apply/`):
  - Robust backend eligibility engine verifying CGPA, department match, course match, active deadline, approval status, and duplicate prevention.
- [x] Student Application History API (`GET /api/student/applications/`):
  - Isolated student application dashboard.
- [x] 100% automated test suite with 25 new tests (107 tests passing project-wide in ~2.4 seconds).


---

### ⏳ Stage 6: Shortlisting, Interviews & Offer Workflow
- [ ] Company application review & shortlisting.
- [ ] Interview scheduling & status updates.
- [ ] Offer generation & Student acceptance/rejection.

---

### ⏳ Stage 7: React Frontend - Design System & Dashboards
- [ ] Modern UI/UX with responsive layouts.
- [ ] Student Dashboard, Company Dashboard, TPO Dashboard.

---

### ⏳ Stage 8: Analytics, Notifications & Final Polish
- [ ] Placement analytics & reporting.
- [ ] Notifications system for interview calls and status updates.
