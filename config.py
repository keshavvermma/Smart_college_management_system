"""
config.py - central configuration for the Smart College Management System.

Database credentials are NEVER written in the source code. They are read from
environment variables, which can be placed in a ".env" file (see .env.example).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load variables from the .env file (if python-dotenv is installed and the file exists)
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # the app still works if variables are set in Windows itself
    pass

# ---------------------------------------------------------------- database
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "smart_college"),
}

# ------------------------------------------------------------ application
APP_NAME = "Smart College Management System"
APP_TITLE = APP_NAME
COLLEGE_NAME = os.getenv("COLLEGE_NAME", "Smart Institute of Engineering & Technology")
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

# ---------------------------------------------------------- academic rules
ATTENDANCE_THRESHOLD = 75      # % - below this a warning is shown
PASS_PERCENTAGE = 40           # % - below this the result is "Fail"
EXAM_TYPES = ["Internal", "Mid Term", "Practical", "End Semester"]
SEMESTERS = list(range(1, 9))
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PRIORITIES = ["Normal", "Important", "Urgent"]
NOTICE_PRIORITIES = PRIORITIES
GENDERS = ["Male", "Female", "Other"]
DESIGNATIONS = ["Professor", "Associate Professor", "Assistant Professor", "Lecturer", "Lab Instructor"]
# default "maximum marks" suggested on the marks-entry screen for each exam type
DEFAULT_MAX_MARKS = {"Internal": 30, "Mid Term": 50, "Practical": 25, "End Semester": 100}

# ---------------------------------------------------------------- security
# Initial passwords given to accounts created from the Admin screens.
# Users can change them from the Settings page.
DEFAULT_STUDENT_PASSWORD = os.getenv("DEFAULT_STUDENT_PASSWORD", "Student@123")
DEFAULT_FACULTY_PASSWORD = os.getenv("DEFAULT_FACULTY_PASSWORD", "Faculty@123")

SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MAX_LOGIN_ATTEMPTS = 5         # failed logins before a short lock-out
LOCKOUT_SECONDS = 60
