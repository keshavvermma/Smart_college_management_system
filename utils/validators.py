"""
utils/validators.py - input validation.

Every validate_* function returns a LIST of error messages.
An empty list means the data is valid. Pages show the messages with st.error().
"""
import re
from datetime import date

import config

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^[6-9]\d{9}$")                 # Indian 10-digit mobile number
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,99}$")
ROLL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-/]{3,19}$")
SUBJECT_CODE_RE = re.compile(r"^[A-Z]{2,5}\d{2,4}$")
DEPT_CODE_RE = re.compile(r"^[A-Z]{2,8}$")


def clean(data: dict) -> dict:
    """Strip spaces from every text value."""
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in data.items()}


# ------------------------------------------------------- single-field checks
def check_name(value, label="Name"):
    if not value or not NAME_RE.match(value):
        return f"{label} must be 2-100 characters (letters, spaces, . ' - only)."


def check_email(value):
    if not value or not EMAIL_RE.match(value) or len(value) > 120:
        return "Enter a valid email address (example: name@college.edu)."


def check_phone(value):
    if not value or not PHONE_RE.match(value):
        return "Phone must be a 10-digit mobile number starting with 6, 7, 8 or 9."


# --------------------------------------------------------------- entities
def validate_student(d: dict) -> list:
    d = clean(d)
    errors = []
    if not d.get("roll_no") or not ROLL_RE.match(d["roll_no"]):
        errors.append("Roll number must be 4-20 characters (letters, digits, - or /).")
    errors.append(check_name(d.get("name")))
    if d.get("gender") not in ("Male", "Female", "Other"):
        errors.append("Select a gender.")
    dob = d.get("date_of_birth")
    if not isinstance(dob, date):
        errors.append("Enter a valid date of birth.")
    else:
        age = (date.today() - dob).days / 365.25
        if not 15 <= age <= 45:
            errors.append("Date of birth gives an age outside 15-45 years.")
    if not d.get("department_id"):
        errors.append("Select a department.")
    if d.get("semester") not in config.SEMESTERS:
        errors.append("Semester must be between 1 and 8.")
    errors.append(check_email(d.get("email")))
    errors.append(check_phone(d.get("phone")))
    if len(d.get("address") or "") > 255:
        errors.append("Address must be at most 255 characters.")
    year = d.get("admission_year")
    if not isinstance(year, int) or not 2000 <= year <= date.today().year + 1:
        errors.append(f"Admission year must be between 2000 and {date.today().year + 1}.")
    return [e for e in errors if e]


def validate_faculty(d: dict) -> list:
    d = clean(d)
    errors = [check_name(d.get("name")), check_email(d.get("email")), check_phone(d.get("phone"))]
    if not d.get("department_id"):
        errors.append("Select a department.")
    if not d.get("designation") or len(d["designation"]) > 50:
        errors.append("Designation is required (maximum 50 characters).")
    joining = d.get("joining_date")
    if not isinstance(joining, date) or joining > date.today():
        errors.append("Joining date must be a valid date that is not in the future.")
    return [e for e in errors if e]


def validate_department(d: dict) -> list:
    d = clean(d)
    errors = []
    if not d.get("dept_code") or not DEPT_CODE_RE.match(d["dept_code"]):
        errors.append("Department code must be 2-8 capital letters (example: CSE).")
    if not d.get("dept_name") or not 3 <= len(d["dept_name"]) <= 100:
        errors.append("Department name must be 3-100 characters.")
    return errors


def validate_subject(d: dict) -> list:
    d = clean(d)
    errors = []
    if not d.get("subject_code") or not SUBJECT_CODE_RE.match(d["subject_code"]):
        errors.append("Subject code must look like CS301 (2-5 capital letters + 2-4 digits).")
    if not d.get("subject_name") or not 3 <= len(d["subject_name"]) <= 120:
        errors.append("Subject name must be 3-120 characters.")
    if not d.get("department_id"):
        errors.append("Select a department.")
    if d.get("semester") not in config.SEMESTERS:
        errors.append("Semester must be between 1 and 8.")
    if d.get("credits") not in range(1, 7):
        errors.append("Credits must be between 1 and 6.")
    return errors


def validate_notice(d: dict) -> list:
    d = clean(d)
    errors = []
    if not d.get("title") or not 3 <= len(d["title"]) <= 150:
        errors.append("Title must be 3-150 characters.")
    if not d.get("description") or len(d["description"]) < 5:
        errors.append("Description must be at least 5 characters.")
    if d.get("priority") not in config.PRIORITIES:
        errors.append("Select a priority.")
    return errors


def validate_marks_entry(marks, max_marks) -> str | None:
    """Check one mark against its maximum. Returns an error text or None."""
    if max_marks is None or not 0 < max_marks <= 1000:
        return "Maximum marks must be between 1 and 1000."
    if marks is None or marks < 0 or marks > max_marks:
        return f"Marks must be between 0 and {max_marks:g}."
    return None


def validate_password(password: str) -> list:
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        errors.append("Password must contain at least one letter and one digit.")
    return errors
