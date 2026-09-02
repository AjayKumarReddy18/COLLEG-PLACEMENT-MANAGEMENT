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

### ⏳ Stage 2: Authentication APIs & JWT Setup (Upcoming)
- [ ] User Registration API:
  - Student Registration (requires `student_id`, `email`, `first_name`, `last_name`, `phone_number`, `password`).
  - Company Registration (requires `email`, `first_name`, `last_name`, `phone_number`, `password`).
  - TPO Registration.
- [ ] Custom JWT Authentication & Login API:
  - **Student Login**:
    - `Student ID + Password`
    - *OR*
    - `Email + Password`
  - **Company Login**:
    - `Email + Password`
  - **TPO Login**:
    - `Email + Password`
- [ ] Custom Authentication Backend (supports resolving either `student_id` or `email` as login identifier).
- [ ] User Profile endpoints & Role-based permission classes (`IsStudent`, `IsCompany`, `IsTPO`).

---

### ⏳ Stage 3: Student Profile & Company Profile Modules
- [ ] Student Profile (academic details, CGPA, branch, graduation year, resume upload).
- [ ] Company Profile (company name, website, description, HR contact details, approval status).

---

### ⏳ Stage 4: TPO Approval Workflows & Management
- [ ] TPO company verification and approval system.
- [ ] TPO job listing review and approval.

---

### ⏳ Stage 5: Job Posting & Application Pipeline
- [ ] Company job posting with eligibility criteria (minimum CGPA, allowed branches).
- [ ] Student application system with automatic eligibility checks.

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
