import os, sys, unittest
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import (check_email, check_phone, validate_faculty, validate_marks_entry,
                              validate_notice, validate_password, validate_student, validate_subject)

GOOD_STUDENT = dict(name="Keshav Kumar", roll_no="CSE24010", gender="Male", date_of_birth=date(2005, 3, 14),
                    department_id=1, semester=5, email="keshav@example.com", phone="9876543210",
                    address="Nawabganj, Bareilly", admission_year=2024)


class TestValidators(unittest.TestCase):
    def test_email_phone(self):
        self.assertIsNone(check_email("a.b@college.edu"))
        self.assertIsNotNone(check_email("not-an-email"))
        self.assertIsNone(check_phone("9876543210"))
        self.assertIsNotNone(check_phone("1234567890"))   # must start with 6-9
        self.assertIsNotNone(check_phone("98765"))

    def test_valid_student(self):
        self.assertEqual(validate_student(GOOD_STUDENT), [])

    def test_invalid_student_fields(self):
        bad = dict(GOOD_STUDENT, name="12", email="x", phone="1", semester=9, admission_year=1990,
                   date_of_birth=date(2020, 1, 1))
        self.assertGreaterEqual(len(validate_student(bad)), 6)

    def test_faculty_and_subject_and_notice(self):
        self.assertEqual(validate_faculty(dict(name="Dr. A Kumar", email="a@x.com", phone="9000000001",
                                               department_id=1, designation="Professor",
                                               joining_date=date(2020, 1, 1))), [])
        self.assertTrue(validate_faculty(dict(name="A", email="", phone="", department_id=None,
                                              designation="", joining_date=date(2999, 1, 1))))
        self.assertEqual(validate_subject(dict(subject_code="CS501", subject_name="DBMS", department_id=1,
                                               semester=5, credits=4)), [])
        self.assertTrue(validate_subject(dict(subject_code="!!", subject_name="", department_id=1,
                                              semester=9, credits=9)))
        self.assertEqual(validate_notice(dict(title="Holiday", description="College closed.", priority="Normal")), [])
        self.assertTrue(validate_notice(dict(title="", description="", priority="Huge")))

    def test_marks_and_password(self):
        self.assertIsNone(validate_marks_entry(25, 30))
        self.assertIsNotNone(validate_marks_entry(31, 30))
        self.assertIsNotNone(validate_marks_entry(-1, 30))
        self.assertEqual(validate_password("abc12345"), [])
        self.assertTrue(validate_password("short1"))
        self.assertTrue(validate_password("onlyletters"))


if __name__ == "__main__":
    unittest.main()
