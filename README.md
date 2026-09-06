# College Placement Management System

Welcome to the **College Placement Management System** repository.

---

## 🛠️ Technology Stack

* **Backend**: Django 6.1 + Django REST Framework 3.18
* **Authentication**: SimpleJWT (`djangorestframework-simplejwt`)
* **Frontend**: React.js (To be built in upcoming stages)
* **Database**: MySQL (with SQLite fallback for local development)

---

## 👥 User Roles (Strictly 3 Roles)

1. **STUDENT**: Registers, builds academic profile, browses drives, applies, receives offers.
2. **COMPANY**: Registers, gets approved by TPO, posts jobs, shortlists students, schedules interviews, issues offers.
3. **TPO (Training & Placement Officer)**: Manages campus placement, verifies companies and jobs, views reports and analytics.

*(Note: There is **NO generic ADMIN role** in the system. Superusers default to the `TPO` role.)*

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- MySQL Server (optional; SQLite works out of the box for quick testing)

### 2. Backend Setup & Dependencies

Open a terminal in the `backend/` directory:

```bash
cd backend
python -m pip install -r requirements.txt
```

### 3. Database Configuration (MySQL / SQLite)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. For MySQL, update `.env` with your database credentials:
   ```ini
   DB_ENGINE=mysql
   DB_NAME=college_placement_db
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```
*(If you omit `.env` or set `DB_ENGINE=sqlite`, the application defaults to local SQLite automatically).*

### 4. Apply Migrations

```bash
python manage.py migrate
```

### 5. Create a TPO Account (Superuser)

Since TPO registration is intentionally not public, create a TPO user using:

```bash
python manage.py createsuperuser
```

### 6. Run the Test Suite

```bash
python manage.py test users
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

---

## 🔐 Stage 2: Authentication & JWT Endpoints

### Endpoint Summary

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/student/` | Public | Register a new student (assigns `role=STUDENT`) |
| `POST` | `/api/auth/register/company/` | Public | Register a new company (assigns `role=COMPANY`) |
| `POST` | `/api/auth/login/` | Public | Login using email/student_id + password |
| `POST` | `/api/auth/token/refresh/` | Public | Exchange refresh token for a new access token |
| `GET`  | `/api/auth/me/` | Authenticated | Retrieve currently logged-in user profile |

---

### Request & Response Examples

#### 1. Student Registration
`POST /api/auth/register/student/`

**Request Body:**
```json
{
  "email": "rahul.sharma@college.edu",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!",
  "student_id": "23CS001",
  "first_name": "Rahul",
  "last_name": "Sharma",
  "phone_number": "9876543210"
}
```

**Response (`201 Created`):**
```json
{
  "message": "Student registered successfully.",
  "user": {
    "id": 1,
    "email": "rahul.sharma@college.edu",
    "student_id": "23CS001",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "phone_number": "9876543210",
    "role": "STUDENT",
    "created_at": "2026-09-03T14:30:00Z"
  }
}
```

---

#### 2. Company Registration
`POST /api/auth/register/company/`

**Request Body:**
```json
{
  "email": "recruiter@techcorp.com",
  "password": "CompanyPassword123!",
  "password_confirm": "CompanyPassword123!",
  "first_name": "TechCorp",
  "last_name": "HR",
  "phone_number": "9123456780"
}
```

**Response (`201 Created`):**
```json
{
  "message": "Company registered successfully.",
  "user": {
    "id": 2,
    "email": "recruiter@techcorp.com",
    "student_id": null,
    "first_name": "TechCorp",
    "last_name": "HR",
    "phone_number": "9123456780",
    "role": "COMPANY",
    "created_at": "2026-09-03T14:32:00Z"
  }
}
```

---

#### 3. Student Login (Using Student ID or Email)
`POST /api/auth/login/`

**Request Body (Using Student ID):**
```json
{
  "identifier": "23CS001",
  "password": "StrongPassword123!"
}
```

*OR using Email:*
```json
{
  "identifier": "rahul.sharma@college.edu",
  "password": "StrongPassword123!"
}
```

**Response (`200 OK`):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "rahul.sharma@college.edu",
    "student_id": "23CS001",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "phone_number": "9876543210",
    "role": "STUDENT",
    "created_at": "2026-09-03T14:30:00Z"
  }
}
```

---

#### 4. Current User Profile (`/me/`)
`GET /api/auth/me/`

**Header:**
```http
Authorization: Bearer <access_token>
```

**Response (`200 OK`):**
```json
{
  "id": 1,
  "email": "rahul.sharma@college.edu",
  "student_id": "23CS001",
  "first_name": "Rahul",
  "last_name": "Sharma",
  "phone_number": "9876543210",
  "role": "STUDENT",
  "created_at": "2026-09-03T14:30:00Z"
}
```

---

#### 5. Refresh JWT Token
`POST /api/auth/token/refresh/`

**Request Body:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Response (`200 OK`):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 🛡️ Role-Based Permissions

Located in `backend/users/permissions.py`:
* `IsStudent`: Ensures `request.user.role == 'STUDENT'`.
* `IsCompany`: Ensures `request.user.role == 'COMPANY'`.
* `IsTPO`: Ensures `request.user.role == 'TPO'`.

All permission classes enforce authentication first and return `401 Unauthorized` for unauthenticated requests and `403 Forbidden` for role mismatches.

---

## 🧪 Testing with PowerShell & cURL

### 1. Register a Student (PowerShell)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/register/student/" -Method Post -ContentType "application/json" -Body (@{
    email = "stu@college.edu"
    student_id = "23CS101"
    first_name = "Amit"
    last_name = "Kumar"
    phone_number = "9876543210"
    password = "StudentPassword123!"
    password_confirm = "StudentPassword123!"
} | ConvertTo-Json)
```

### 2. Login as Student (PowerShell)
```powershell
$res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method Post -ContentType "application/json" -Body (@{
    identifier = "23CS101"
    password = "StudentPassword123!"
} | ConvertTo-Json)

$token = $res.access
```

### 3. Fetch Profile `/me/` (PowerShell)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/me/" -Method Get -Headers @{ Authorization = "Bearer $token" }
```

---

## 👤 Stage 3: Student & Company Profile Modules

### Endpoint Summary

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/student/profile/` | Student Only | Retrieve authenticated student's academic profile |
| `POST` | `/api/student/profile/` | Student Only | Create student profile (one profile per student) |
| `PUT` | `/api/student/profile/` | Student Only | Full update of student profile |
| `PATCH` | `/api/student/profile/` | Student Only | Partial update of student profile (e.g. resume, links) |
| `GET` | `/api/company/profile/` | Company Only | Retrieve authenticated company profile & status |
| `POST` | `/api/company/profile/` | Company Only | Create company profile (one profile per company) |
| `PUT` | `/api/company/profile/` | Company Only | Full update of company profile |
| `PATCH` | `/api/company/profile/` | Company Only | Partial update of company profile |

### Permissions & Data Isolation Rules
* **Strict Role Segregation**: A student cannot query or modify `/api/company/profile/` (`403 Forbidden`), and a company cannot touch `/api/student/profile/` (`403 Forbidden`).
* **Profile Isolation**: Each student/company can only access their own profile. Profile endpoints operate on `request.user` rather than arbitrary ID parameters, preventing cross-user data leakage.
* **Verification Protection**: `verification_status` and `verification_remarks` on `CompanyProfile` are read-only to companies. Any attempt to write or alter verification fields is stripped on save.

---

### Request & Response Examples (Stage 3)

#### 1. Create Student Profile
`POST /api/student/profile/`

**Headers:**
```http
Authorization: Bearer <student_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "department": "Computer Science",
  "course": "B.Tech",
  "year": 4,
  "cgpa": "8.75",
  "skills": "Python, Django, React, MySQL, Docker",
  "github_url": "https://github.com/rahul-sharma",
  "linkedin_url": "https://linkedin.com/in/rahul-sharma",
  "instagram_url": "https://www.instagram.com/rahul_dev/",
  "portfolio_url": "https://rahulsharma.dev",
  "date_of_birth": "2003-05-15"
}
```

**Response (`201 Created`):**
```json
{
  "message": "Student profile created successfully.",
  "profile": {
    "id": 1,
    "user_email": "rahul.sharma@college.edu",
    "student_id": "23CS001",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "department": "Computer Science",
    "course": "B.Tech",
    "year": 4,
    "cgpa": "8.75",
    "skills": "Python, Django, React, MySQL, Docker",
    "resume": null,
    "github_url": "https://github.com/rahul-sharma",
    "linkedin_url": "https://linkedin.com/in/rahul-sharma",
    "instagram_url": "https://www.instagram.com/rahul_dev/",
    "portfolio_url": "https://rahulsharma.dev",
    "date_of_birth": "2003-05-15",
    "created_at": "2026-09-04T05:00:00Z",
    "updated_at": "2026-09-04T05:00:00Z"
  }
}
```

---

#### 2. Upload Student Resume (`multipart/form-data`)
`PATCH /api/student/profile/`

**Headers:**
```http
Authorization: Bearer <student_access_token>
Content-Type: multipart/form-data
```

**Form Data:**
* `resume`: `[Attach file: resume.pdf / resume.docx]` *(PDF, DOC, DOCX up to 5MB)*

**PowerShell Example:**
```powershell
$filePath = "C:\path\to\resume.pdf"
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes)

$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = (
    "--$boundary",
    'Content-Disposition: form-data; name="resume"; filename="resume.pdf"',
    'Content-Type: application/pdf',
    '',
    $fileContent,
    "--$boundary--"
) -join $LF

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/student/profile/" `
    -Method Patch `
    -Headers @{ Authorization = "Bearer $token" } `
    -ContentType "multipart/form-data; boundary=$boundary" `
    -Body $bodyLines
```

---

#### 3. Create Company Profile
`POST /api/company/profile/`

**Headers:**
```http
Authorization: Bearer <company_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "company_name": "TechCorp Inc.",
  "company_description": "Global enterprise software solutions and cloud infrastructure.",
  "industry": "Information Technology",
  "website": "https://techcorp.com",
  "location": "Bengaluru, India",
  "contact_email": "recruiter@techcorp.com",
  "contact_phone": "9876543210",
  "company_size": "201-1000"
}
```

**Response (`201 Created`):**
```json
{
  "message": "Company profile created successfully.",
  "profile": {
    "id": 1,
    "user_email": "recruiter@techcorp.com",
    "company_name": "TechCorp Inc.",
    "company_description": "Global enterprise software solutions and cloud infrastructure.",
    "industry": "Information Technology",
    "website": "https://techcorp.com",
    "location": "Bengaluru, India",
    "contact_email": "recruiter@techcorp.com",
    "contact_phone": "9876543210",
    "company_size": "201-1000",
    "logo": null,
    "verification_status": "PENDING",
    "verification_remarks": "",
    "created_at": "2026-09-04T05:10:00Z",
    "updated_at": "2026-09-04T05:10:00Z"
  }
}
```

---

## 🏛️ Stage 4: TPO Management & Verification Endpoints

The TPO (Training & Placement Officer) oversees the entire campus placement ecosystem, verifies company credentials, and reviews student profiles.

### Endpoint Summary

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tpo/companies/` | TPO Only | List registered companies (with `?verification_status=` filter) |
| `GET` | `/api/tpo/companies/<id>/` | TPO Only | Retrieve detailed company profile and user contact details |
| `PATCH` | `/api/tpo/companies/<id>/verify/` | TPO Only | Approve or Reject company profile with remarks/feedback |
| `GET` | `/api/tpo/students/` | TPO Only | List student profiles (with `department`, `course`, `min_cgpa` filters) |

### TPO Authentication & Authorization
* **Strict Role Gate**: All TPO endpoints are secured with `[IsAuthenticated, IsTPO]`.
* **Access Control Matrix**:
  * `TPO`: Full access to company verification, company overview, and student directory.
  * `STUDENT`: `403 Forbidden` on all `/api/tpo/*` endpoints.
  * `COMPANY`: `403 Forbidden` on all `/api/tpo/*` endpoints (companies cannot view competitor data or self-approve).
  * `Unauthenticated`: `401 Unauthorized`.

---

### Request & Response Examples (Stage 4)

#### 1. List Companies (Filtered by Verification Status)
`GET /api/tpo/companies/?verification_status=PENDING`

**Headers:**
```http
Authorization: Bearer <tpo_access_token>
```

**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "user_id": 3,
    "user_email": "recruiter@techcorp.com",
    "user_first_name": "TechCorp",
    "user_last_name": "HR",
    "user_phone_number": "9876543210",
    "company_name": "TechCorp Inc.",
    "company_description": "Global enterprise software solutions.",
    "industry": "Information Technology",
    "website": "https://techcorp.com",
    "location": "Bengaluru, India",
    "contact_email": "recruiter@techcorp.com",
    "contact_phone": "9876543210",
    "company_size": "201-1000",
    "logo": null,
    "verification_status": "PENDING",
    "verification_remarks": "",
    "created_at": "2026-09-04T05:10:00Z",
    "updated_at": "2026-09-04T05:10:00Z"
  }
]
```

---

#### 2. Get Company Detail
`GET /api/tpo/companies/1/`

**Headers:**
```http
Authorization: Bearer <tpo_access_token>
```

**Response (`200 OK`):**
```json
{
  "id": 1,
  "user_id": 3,
  "user_email": "recruiter@techcorp.com",
  "user_first_name": "TechCorp",
  "user_last_name": "HR",
  "user_phone_number": "9876543210",
  "company_name": "TechCorp Inc.",
  "company_description": "Global enterprise software solutions.",
  "industry": "Information Technology",
  "website": "https://techcorp.com",
  "location": "Bengaluru, India",
  "contact_email": "recruiter@techcorp.com",
  "contact_phone": "9876543210",
  "company_size": "201-1000",
  "logo": null,
  "verification_status": "PENDING",
  "verification_remarks": "",
  "created_at": "2026-09-04T05:10:00Z",
  "updated_at": "2026-09-04T05:10:00Z"
}
```

---

#### 3. Verify Company (Approve / Reject)
`PATCH /api/tpo/companies/1/verify/`

**Headers:**
```http
Authorization: Bearer <tpo_access_token>
Content-Type: application/json
```

**Approve Request Body:**
```json
{
  "verification_status": "APPROVED",
  "remarks": "Corporate credentials and MCA registration verified."
}
```

*OR Reject Request Body:*
```json
{
  "verification_status": "REJECTED",
  "remarks": "Company registration documents could not be verified."
}
```

**Response (`200 OK`):**
```json
{
  "message": "Company verification status updated to 'APPROVED'.",
  "company": {
    "id": 1,
    "user_id": 3,
    "user_email": "recruiter@techcorp.com",
    "company_name": "TechCorp Inc.",
    "verification_status": "APPROVED",
    "verification_remarks": "Corporate credentials and MCA registration verified.",
    "updated_at": "2026-09-04T05:25:00Z"
  }
}
```

---

#### 4. List & Filter Students
`GET /api/tpo/students/?department=Computer Science&course=B.Tech&min_cgpa=8.0`

**Headers:**
```http
Authorization: Bearer <tpo_access_token>
```

**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "student_id": "23CS001",
    "email": "rahul.sharma@college.edu",
    "first_name": "Rahul",
    "last_name": "Sharma",
    "phone_number": "9876543210",
    "department": "Computer Science",
    "course": "B.Tech",
    "year": 4,
    "cgpa": "8.75",
    "skills": "Python, Django, React, Docker",
    "resume": "/media/resumes/resume.pdf",
    "github_url": "https://github.com/rahul-sharma",
    "linkedin_url": "https://linkedin.com/in/rahul-sharma",
    "instagram_url": "https://www.instagram.com/rahul_dev/",
    "portfolio_url": "https://rahulsharma.dev",
    "date_of_birth": "2003-05-15",
    "created_at": "2026-09-04T05:00:00Z",
    "updated_at": "2026-09-04T05:15:00Z"
  }
]
```

---

### 🧪 TPO Testing with PowerShell

```powershell
# 1. Login as TPO
$res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method Post -ContentType "application/json" -Body (@{
    identifier = "tpo@college.edu"
    password = "TpoPassword123!"
} | ConvertTo-Json)

$tpoToken = $res.access

# 2. View all pending companies
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tpo/companies/?verification_status=PENDING" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $tpoToken" }

# 3. Approve a company (ID = 1)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tpo/companies/1/verify/" `
    -Method Patch `
    -Headers @{ Authorization = "Bearer $tpoToken" } `
    -ContentType "application/json" `
    -Body (@{
        verification_status = "APPROVED"
        remarks = "Company registration verified successfully."
    } | ConvertTo-Json)

# 4. Search eligible students (CGPA >= 8.0 in Computer Science)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tpo/students/?department=Computer&min_cgpa=8.0" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $tpoToken" }
```

---

## 💼 Stage 5: Job Posting & Application Pipeline

Stage 5 connects companies, TPO, and students into a unified campus recruitment drive pipeline with automated eligibility checks and role isolation.

```
Company Creates Job
    └── Status: PENDING_TPO_APPROVAL
         └── TPO Reviews & Approves (Status: APPROVED)
              └── Visible to Students (GET /api/student/jobs/)
                   └── Student Applies (POST /api/student/jobs/<id>/apply/)
                        ├── 1. CGPA >= Minimum CGPA
                        ├── 2. Department in Eligible Departments
                        ├── 3. Course in Eligible Courses (if set)
                        ├── 4. Deadline Not Passed
                        └── 5. No Duplicate Application
                             └── Company Reviews Applicants (GET /api/company/jobs/<id>/applications/)
```

---

### Endpoint Summary (Stage 5)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/company/jobs/` | Company Only | Post a new placement drive / job listing |
| `GET` | `/api/company/jobs/` | Company Only | List authenticated company's own job drives |
| `GET` | `/api/company/jobs/<id>/` | Company Only | Retrieve company's own job listing |
| `PUT/PATCH` | `/api/company/jobs/<id>/` | Company Only | Update company's own job listing (cannot self-approve) |
| `GET` | `/api/company/jobs/<id>/applications/` | Company Only | View applicant roster and resumes for company's job |
| `GET` | `/api/tpo/jobs/` | TPO Only | List all campus jobs across companies (supports `?status=`) |
| `PATCH` | `/api/tpo/jobs/<id>/verify/` | TPO Only | Approve or reject job listing with remarks (alias: `/approve/`) |
| `GET` | `/api/student/jobs/` | Student Only | Browse approved jobs with real-time eligibility evaluation |
| `POST` | `/api/student/jobs/<id>/apply/` | Student Only | Submit job application with automated eligibility verification |
| `GET` | `/api/student/applications/` | Student Only | List student's own application history and statuses |

---

### Strict Security & Permission Rules

1. **Company Isolation**:
   * A company can only create jobs for its own account.
   * A company can only view and edit its own jobs (`GET/PUT/PATCH /api/company/jobs/<id>/`). Attempting to access another company's job yields `404 Not Found`.
   * A company **cannot self-approve** jobs. Any attempt to set `status = "APPROVED"` yields `400 Bad Request`.
   * A company can only view applicant profiles for **its own jobs**. Accessing another company's applicant list yields `403 Forbidden`.
2. **TPO Authority**:
   * Only TPO can approve or reject job listings.
   * TPO can view jobs across all companies and filter by status.
3. **Student Protection**:
   * Students can only browse jobs that are strictly `APPROVED`. Unapproved jobs (`DRAFT`, `PENDING_TPO_APPROVAL`, `REJECTED`, `CLOSED`) are completely invisible.
   * Students can only view their own applications.

---

### Request & Response Examples (Stage 5)

#### 1. Company Creates Job Listing
`POST /api/company/jobs/`

**Headers:**
```http
Authorization: Bearer <company_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "job_title": "Software Engineer (Backend)",
  "description": "Develop scalable APIs with Python, Django, and MySQL.",
  "job_type": "FULL_TIME",
  "salary": "1400000.00",
  "job_location": "Bengaluru, India",
  "minimum_cgpa": "7.50",
  "eligible_departments": ["Computer Science", "Information Technology"],
  "eligible_courses": ["B.Tech", "M.Tech"],
  "application_deadline": "2026-11-30T23:59:59Z"
}
```

**Response (`201 Created`):**
```json
{
  "message": "Job listing created successfully.",
  "job": {
    "id": 1,
    "company_id": 1,
    "company_name": "TechCorp Inc.",
    "job_title": "Software Engineer (Backend)",
    "description": "Develop scalable APIs with Python, Django, and MySQL.",
    "job_type": "FULL_TIME",
    "salary": "1400000.00",
    "job_location": "Bengaluru, India",
    "minimum_cgpa": "7.50",
    "eligible_departments": ["Computer Science", "Information Technology"],
    "eligible_courses": ["B.Tech", "M.Tech"],
    "application_deadline": "2026-11-30T23:59:59Z",
    "status": "PENDING_TPO_APPROVAL",
    "approval_remarks": "",
    "created_at": "2026-09-04T05:30:00Z",
    "updated_at": "2026-09-04T05:30:00Z"
  }
}
```

---

#### 2. TPO Approves Job Listing
`PATCH /api/tpo/jobs/1/verify/`

**Headers:**
```http
Authorization: Bearer <tpo_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "APPROVED",
  "remarks": "Role compensation and eligibility verified for campus drive."
}
```

**Response (`200 OK`):**
```json
{
  "message": "Job listing status updated to 'APPROVED'.",
  "job": {
    "id": 1,
    "company_id": 1,
    "company_name": "TechCorp Inc.",
    "company_email": "recruiter@techcorp.com",
    "company_location": "Bengaluru, India",
    "company_industry": "Information Technology",
    "job_title": "Software Engineer (Backend)",
    "status": "APPROVED",
    "approval_remarks": "Role compensation and eligibility verified for campus drive.",
    "updated_at": "2026-09-04T05:35:00Z"
  }
}
```

---

#### 3. Student Browses Approved Jobs
`GET /api/student/jobs/`

**Headers:**
```http
Authorization: Bearer <student_access_token>
```

**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "company_name": "TechCorp Inc.",
    "company_website": "https://techcorp.com",
    "job_title": "Software Engineer (Backend)",
    "description": "Develop scalable APIs with Python, Django, and MySQL.",
    "job_type": "FULL_TIME",
    "salary": "1400000.00",
    "job_location": "Bengaluru, India",
    "minimum_cgpa": "7.50",
    "eligible_departments": ["Computer Science", "Information Technology"],
    "eligible_courses": ["B.Tech", "M.Tech"],
    "application_deadline": "2026-11-30T23:59:59Z",
    "status": "APPROVED",
    "is_eligible": true,
    "eligibility_reasons": [],
    "has_applied": false,
    "created_at": "2026-09-04T05:30:00Z"
  }
]
```

*(If student CGPA or department does not match, `is_eligible` is `false` and `eligibility_reasons` clearly explains why).*

---

#### 4. Student Applies for Job
`POST /api/student/jobs/1/apply/`

**Headers:**
```http
Authorization: Bearer <student_access_token>
```

**Response (`201 Created`):**
```json
{
  "message": "Job application submitted successfully.",
  "application": {
    "id": 1,
    "job_id": 1,
    "job_title": "Software Engineer (Backend)",
    "company_name": "TechCorp Inc.",
    "job_location": "Bengaluru, India",
    "salary": "1400000.00",
    "status": "APPLIED",
    "applied_at": "2026-09-04T05:40:00Z",
    "updated_at": "2026-09-04T05:40:00Z"
  }
}
```

**Eligibility Rejection Example (`400 Bad Request`):**
```json
{
  "detail": "You are not eligible for this job because your CGPA (6.80) is below the required minimum of 7.50."
}
```

**Duplicate Application Rejection Example (`400 Bad Request`):**
```json
{
  "detail": "You have already applied for this job listing."
}
```

---

#### 5. Company Views Applicants
`GET /api/company/jobs/1/applications/`

**Headers:**
```http
Authorization: Bearer <company_access_token>
```

**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "student_id": "23CS001",
    "student_name": "Rahul Sharma",
    "email": "rahul.sharma@college.edu",
    "phone_number": "9876543210",
    "department": "Computer Science",
    "course": "B.Tech",
    "year": 4,
    "cgpa": "8.75",
    "skills": "Python, Django, React, MySQL, Docker",
    "resume": "/media/resumes/resume.pdf",
    "status": "APPLIED",
    "applied_at": "2026-09-04T05:40:00Z",
    "updated_at": "2026-09-04T05:40:00Z"
  }
]
```

---

### 🧪 Stage 5 Testing with PowerShell

```powershell
# 1. Company creates a job
$jobRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/company/jobs/" `
    -Method Post `
    -Headers @{ Authorization = "Bearer $companyToken" } `
    -ContentType "application/json" `
    -Body (@{
        job_title = "Data Engineer"
        description = "ETL pipeline and SQL development"
        job_type = "FULL_TIME"
        salary = "1100000.00"
        job_location = "Hyderabad"
        minimum_cgpa = "7.00"
        eligible_departments = @("Computer Science", "Information Technology")
        application_deadline = "2026-12-31T23:59:59Z"
    } | ConvertTo-Json)

$jobId = $jobRes.job.id

# 2. TPO approves the job
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tpo/jobs/$jobId/verify/" `
    -Method Patch `
    -Headers @{ Authorization = "Bearer $tpoToken" } `
    -ContentType "application/json" `
    -Body (@{
        status = "APPROVED"
        remarks = "Verified and approved for placement drive."
    } | ConvertTo-Json)

# 3. Student browses approved jobs
$jobs = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/student/jobs/" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $studentToken" }

# 4. Student applies
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/student/jobs/$jobId/apply/" `
    -Method Post `
    -Headers @{ Authorization = "Bearer $studentToken" }

# 5. Company reviews applicants
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/company/jobs/$jobId/applications/" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $companyToken" }
```


