"""
config.py - Central configuration for Smart College Management System.

Supports:
1. Local MySQL using .env
2. Cloud MySQL using Streamlit Secrets
3. Aiven MySQL with SSL
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


# ------------------------------------------------------------
# Load local environment variables
# ------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


# ------------------------------------------------------------
# Read settings from Streamlit Secrets or environment variables
# ------------------------------------------------------------

def get_setting(key, default=None):

    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]

    except Exception:
        pass

    return os.getenv(key, default)


# ------------------------------------------------------------
# Database configuration
# ------------------------------------------------------------

DB_HOST = get_setting("DB_HOST", "localhost")
DB_PORT = int(get_setting("DB_PORT", "3306"))
DB_USER = get_setting("DB_USER", "root")
DB_PASSWORD = get_setting("DB_PASSWORD", "")
DB_NAME = get_setting("DB_NAME", "smart_college")

DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "connect_timeout": 15,
}


# ------------------------------------------------------------
# SSL configuration for Aiven MySQL
# ------------------------------------------------------------

# ------------------------------------------------------------
# SSL configuration for Aiven MySQL
# ------------------------------------------------------------

SSL_CA = get_setting("DB_SSL_CA", "")

if SSL_CA:
    ca_path = Path(SSL_CA)

    # Resolve relative paths from project folder
    if not ca_path.is_absolute():
        ca_path = BASE_DIR / ca_path

    if not ca_path.exists():
        raise FileNotFoundError(
            f"SSL CA certificate not found: {ca_path}"
        )

    DB_CONFIG["ssl_ca"] = str(ca_path)
    DB_CONFIG["ssl_verify_cert"] = True
    DB_CONFIG["ssl_verify_identity"] = True


# ------------------------------------------------------------
# Application settings
# ------------------------------------------------------------

APP_NAME = "Smart College Management System"
APP_TITLE = APP_NAME

COLLEGE_NAME = get_setting(
    "COLLEGE_NAME",
    "Smart Institute of Engineering & Technology"
)

LOGO_PATH = BASE_DIR / "assets" / "logo.png"


# ------------------------------------------------------------
# Academic rules
# ------------------------------------------------------------

ATTENDANCE_THRESHOLD = 75
PASS_PERCENTAGE = 40

EXAM_TYPES = [
    "Internal",
    "Mid Term",
    "Practical",
    "End Semester"
]

SEMESTERS = list(range(1, 9))

DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]

PRIORITIES = [
    "Normal",
    "Important",
    "Urgent"
]

NOTICE_PRIORITIES = PRIORITIES

GENDERS = [
    "Male",
    "Female",
    "Other"
]

DESIGNATIONS = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Lecturer",
    "Lab Instructor"
]

DEFAULT_MAX_MARKS = {
    "Internal": 30,
    "Mid Term": 50,
    "Practical": 25,
    "End Semester": 100
}


# ------------------------------------------------------------
# Security settings
# ------------------------------------------------------------

DEFAULT_STUDENT_PASSWORD = get_setting(
    "DEFAULT_STUDENT_PASSWORD",
    "Student@123"
)

DEFAULT_FACULTY_PASSWORD = get_setting(
    "DEFAULT_FACULTY_PASSWORD",
    "Faculty@123"
)

SESSION_TIMEOUT_MINUTES = int(
    get_setting("SESSION_TIMEOUT_MINUTES", "30")
)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 60