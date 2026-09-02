# College Placement Management System

Welcome to the **College Placement Management System** backend and frontend repository.

---

## 🛠️ Technology Stack

* **Backend**: Django 6.1 + Django REST Framework 3.18
* **Frontend**: React.js (To be built in upcoming stages)
* **Database**: MySQL (with SQLite fallback for local development)
* **Authentication**: Django Custom Authentication + JWT

---

## 👥 User Roles (Strictly 3 Roles)

1. **STUDENT**
2. **COMPANY**
3. **TPO (Training & Placement Officer)**

*(Note: There is NO ADMIN role in the system.)*

---

## 🚀 Getting Started (Stage 1)

### 1. Prerequisites
- Python 3.10+ installed
- MySQL Server (optional for Stage 1; SQLite works out of the box for quick testing)

### 2. Backend Setup

Open a terminal in the `backend/` directory:

```bash
cd backend
```

### 3. Database Configuration (MySQL)

To connect to your MySQL database:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Update `.env` with your MySQL database details:
   ```ini
   DB_ENGINE=mysql
   DB_NAME=college_placement_db
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

*(If you leave `DB_ENGINE=sqlite` or omit `.env`, the project automatically uses the local SQLite database for effortless development).*

### 4. Apply Migrations

```bash
python manage.py makemigrations users
python manage.py migrate
```

### 5. Create a Superuser (For Django Admin Access)

```bash
python manage.py createsuperuser
```

### 6. Run Unit Tests

```bash
python manage.py test users
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Django Admin URL: `http://127.0.0.1:8000/admin/`
