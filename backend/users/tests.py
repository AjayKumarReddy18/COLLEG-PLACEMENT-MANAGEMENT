from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_student_user(self):
        """Test creating a student user with valid role and password hashing."""
        student = User.objects.create_user(
            email="student1@college.edu",
            password="StrongPassword123!",
            student_id="STU2026001",
            first_name="Rahul",
            last_name="Sharma",
            phone_number="9876543210",
            role=User.Role.STUDENT,
        )
        self.assertEqual(student.email, "student1@college.edu")
        self.assertEqual(student.student_id, "STU2026001")
        self.assertEqual(student.role, "STUDENT")
        self.assertTrue(student.is_active)
        self.assertFalse(student.is_staff)
        # Password must NOT be plain text
        self.assertNotEqual(student.password, "StrongPassword123!")
        self.assertTrue(student.check_password("StrongPassword123!"))
        self.assertFalse(student.check_password("WrongPassword"))

    def test_create_company_user(self):
        """Test creating a company user."""
        company = User.objects.create_user(
            email="hr@techcorp.com",
            password="CompanyPassword123!",
            first_name="TechCorp",
            last_name="HR",
            phone_number="9123456780",
            role=User.Role.COMPANY,
        )
        self.assertEqual(company.role, "COMPANY")
        self.assertIsNone(company.student_id)
        self.assertTrue(company.check_password("CompanyPassword123!"))

    def test_create_tpo_user(self):
        """Test creating a TPO user."""
        tpo = User.objects.create_user(
            email="tpo@college.edu",
            password="TpoPassword123!",
            first_name="Placement",
            last_name="Officer",
            phone_number="9000000000",
            role=User.Role.TPO,
        )
        self.assertEqual(tpo.role, "TPO")
        self.assertTrue(tpo.check_password("TpoPassword123!"))

    def test_invalid_role_rejected(self):
        """Test that invalid roles such as 'ADMIN' are rejected."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="admin@college.edu",
                password="AdminPassword123!",
                first_name="Admin",
                last_name="User",
                role="ADMIN",  # Invalid role - Only STUDENT, COMPANY, TPO are allowed
            )

    def test_duplicate_email_rejected(self):
        """Test that duplicate email addresses raise an IntegrityError."""
        User.objects.create_user(
            email="duplicate@college.edu",
            password="Pass1",
            first_name="User",
            last_name="One",
            role=User.Role.STUDENT,
        )
        with self.assertRaises(IntegrityError):
            User.objects.create(
                email="duplicate@college.edu",
                first_name="User",
                last_name="Two",
                role=User.Role.STUDENT,
            )

    def test_superuser_creation(self):
        """Test superuser creation for Django Admin staff access."""
        admin_user = User.objects.create_superuser(
            email="tpo_lead@college.edu",
            password="SuperPassword123!",
            first_name="Lead",
            last_name="TPO",
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, User.Role.TPO)
