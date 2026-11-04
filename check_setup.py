"""
check_setup.py - run this BEFORE starting the app to confirm everything is installed
and that Python can really talk to MySQL.

    python check_setup.py

Every line starts with [PASS] or [FAIL]. If something fails, the hint tells you what to fix.
"""
import importlib
import os
import sys

failures = 0


def report(ok, message, hint=""):
    global failures
    print(("[PASS] " if ok else "[FAIL] ") + message)
    if not ok:
        failures += 1
        if hint:
            print("       -> " + hint)


print("=== Smart College Management System - setup check ===\n")

# 1. Python version -----------------------------------------------------------
report(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]}", "Install Python 3.9 or newer from python.org")

# 2. Packages -----------------------------------------------------------------
for module, pip_name in [("streamlit", "streamlit"), ("mysql.connector", "mysql-connector-python"),
                         ("pandas", "pandas"), ("dotenv", "python-dotenv"), ("reportlab", "reportlab")]:
    try:
        importlib.import_module(module)
        report(True, f"package {pip_name} is installed")
    except ImportError:
        optional = " (optional - only needed for PDF reports)" if module == "reportlab" else ""
        report(module == "reportlab", f"package {pip_name} is missing{optional}",
               "Activate your virtual environment, then run:  pip install -r requirements.txt")

# 3. .env file ----------------------------------------------------------------
here = os.path.dirname(os.path.abspath(__file__))
report(os.path.exists(os.path.join(here, ".env")), ".env file found",
       "Copy .env.example to .env and type your MySQL password in it:  copy .env.example .env")

# 4. MySQL connection -----------------------------------------------------------
try:
    from config import DB_CONFIG
    from database import connection

    ok, message = connection.test_connection()
    report(ok, message if ok else f"Cannot connect to MySQL: {message}",
           "Check that the MySQL80 service is running (Windows: Win+R -> services.msc) and that DB_USER / "
           "DB_PASSWORD / DB_NAME in .env are correct. If the database does not exist yet, import sql\\college_database.sql first.")
except Exception as err:  # noqa: BLE001
    ok = False
    report(False, f"Could not load project settings: {err}")

# 5. Tables, views and demo login -------------------------------------------------
if ok:
    from database import queries
    from utils.security import verify_password

    try:
        counts = queries.table_counts()
        report(all(v > 0 for k, v in counts.items()), "tables exist and contain sample data: " + ", ".join(
            f"{k}={v}" for k, v in counts.items()), "Re-import sql\\college_database.sql")
        summary = queries.attendance_summary()
        report(len(summary) > 0, f"Power BI / app views work (vw_attendance_summary returned {len(summary)} rows)")
        admin = queries.get_user_by_username("admin")
        report(bool(admin) and verify_password("admin123", admin["password_hash"]),
               "demo login admin / admin123 verifies against the database hash",
               "If you changed the admin password this is expected; otherwise re-import the SQL file.")
    except Exception as err:  # noqa: BLE001
        report(False, f"Database objects are missing or broken: {err}", "Re-import sql\\college_database.sql")

print()
if failures:
    print(f"{failures} check(s) failed - fix the items above and run this script again.")
    sys.exit(1)
print("All checks passed. Start the app with:   streamlit run app.py")
