# 🎓 Smart College Management System

A web-based college management system built as a B.Tech CSE mini project.
**Python + Streamlit** (UI) · **MySQL** (database) · **Pandas** (data processing) · **Power BI** (analytics).

> Admin, Faculty and Student logins · attendance with 75 % warnings · marks, grades and results · notices · timetable · reports (CSV/PDF) · Power BI-ready database views.

---

## 1. Features

| Role | What they can do |
|---|---|
| **Admin** | Dashboard (totals, avg attendance, avg marks, students below 75 %) · manage Students, Faculty, Departments, Subjects, Timetable · assign faculty to subjects · attendance and marks overview · notices · Reports (student list, attendance, results, faculty) as CSV/PDF · Settings (change password, reset a user's password) |
| **Faculty** | Dashboard (assigned subjects, students, today's attendance, pending tasks, notices) · mark attendance **only for own subjects** · enter/update marks **only for own subjects** · publish notices (edit/delete only own) · own timetable |
| **Student** | Dashboard · My Profile · My Attendance (with warning below 75 %) · My Marks (grade, pass/fail) · My Timetable · Notices. A student can only ever see **their own** data. |

Security: salted PBKDF2-SHA256 password hashes · role-based access on every page · parameterised SQL everywhere · input validation · session timeout and login lock-out · DB password only in `.env`.

## 2. Technology stack
Python 3.11/3.12 · Streamlit ≥ 1.50 · MySQL 8.0 · mysql-connector-python · Pandas · python-dotenv · ReportLab (optional PDF) · Power BI Desktop.

## 3. Folder structure
```
smart_college/
├── app.py                 entry point: login + role-based sidebar menu
├── config.py              settings read from .env
├── check_setup.py         run this first: tests packages + MySQL connection
├── requirements.txt   .env.example
├── database/              connection.py (MySQL helpers) · queries.py (all SQL)
├── pages/                 one file per screen (dashboards, students, attendance, marks ...)
├── utils/                 authentication.py · security.py · calculations.py · validators.py · ui.py · pdf_report.py
├── sql/college_database.sql   database + tables + sample data + Power BI views
├── tests/                 unit tests + a smoke test
├── assets/logo.png
└── docs/                  report, diagrams, Power BI guide, viva Q&A
```
Architecture diagram: `docs/diagrams/architecture.png`. Database structure / ER diagram: `docs/diagrams/er_diagram.png`.

Tables: `departments`, `faculty`, `students`, `subjects`, `users`, `attendance`, `marks`, `notices`, `timetable`. Views for Power BI: `vw_attendance_summary`, `vw_attendance_detail`, `vw_marks_detail`, `vw_student_results`, `vw_student_overview`.

---

## 4. Installation on Windows (step by step)

### Step 1 – Install Python
1. Download **Python 3.12** from https://www.python.org/downloads/ .
2. Run the installer and **tick "Add python.exe to PATH"**, then *Install Now*.
3. Open **Command Prompt** (Win + R → `cmd`) and check: `python --version`

### Step 2 – Install MySQL
1. Download **MySQL Installer** from https://dev.mysql.com/downloads/installer/ and choose *Developer Default* (installs MySQL Server 8 + Workbench).
2. When asked, set a **root password** and remember it. Keep the service name `MySQL80`.
3. Finish the installer. Check the service is running: Win + R → `services.msc` → `MySQL80` → *Running*.

### Step 3 – Create the database
Pick **one** way:

**A. MySQL Workbench (easiest)**
1. Open Workbench → click the *Local instance MySQL80* connection → enter the root password.
2. *File → Open SQL Script…* → choose `sql\college_database.sql`.
3. Click the ⚡ **Execute** button. Wait until it finishes (a few seconds).
4. Right-click *SCHEMAS → Refresh All*: you should see `smart_college` with 9 tables and 5 views.

**B. Command Prompt** (use *Command Prompt*, not PowerShell, because of the `<` sign)
```
cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"
mysql -u root -p < "C:\path\to\smart_college\sql\college_database.sql"
```
> ⚠️ The script starts with `DROP DATABASE IF EXISTS smart_college` – running it again resets the demo data.

### Step 4 – Set up the Python environment
Open Command Prompt in the project folder (type `cmd` in the folder's address bar):
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
(If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or just use Command Prompt.)

### Step 5 – Add your MySQL password
```
copy .env.example .env
notepad .env
```
Change `DB_PASSWORD=` to your MySQL root password (if it contains `#`, put it in quotes). Save the file. **Never share `.env`.**

### Step 6 – Verify the connection
```
python check_setup.py
```
You want every line to say `[PASS]` (packages, `.env`, *Connected to MySQL 8.x*, tables with sample data, views, demo login). Each `[FAIL]` prints a hint.

### Step 7 – Run the app
```
streamlit run app.py
```
The browser opens at http://localhost:8501 . Stop the app with `Ctrl + C`.

### Run the tests (optional)
```
pip install pytest
python -m pytest tests
```

---

## 5. Demo credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Faculty | `rajesh.sharma`, `priya.verma`, `anil.mishra`, `sunita.singh`, `amit.gupta`, `neha.agarwal`, `vikram.rathore`, `pooja.saxena` | `faculty123` |
| Student | roll number in lowercase: `cse24001` … `cse24005`, `cse25001` …, `it24001`, `ece25001`, `me25001`, `ce25001` … (26 students) | `student123` |

Good demo story: log in as `cse24001` (Rahul Kumar, overall attendance 66.7 % → warning shown); log in as `rajesh.sharma` → mark attendance for CS501; log in as `admin` → dashboard, reports.
Accounts created from the Admin screens get the passwords `Faculty@123` / `Student@123` (change in `.env` with `DEFAULT_FACULTY_PASSWORD` / `DEFAULT_STUDENT_PASSWORD`). **Change all demo passwords before any real use.**

Sample data: 5 departments, 8 faculty, 15 subjects, 26 students, 648 attendance records, 124 mark entries, for Internal / Mid Term / Practical (End Semester left empty so you can enter it live), 6 notices, a weekly timetable.

---

## 6. Power BI connection (summary)
Full guide with DAX measures and page layouts: **`docs/POWERBI_GUIDE.md`**.
1. Install *MySQL Connector/NET 8.x* (Power BI needs it), restart Power BI Desktop.
2. *Get Data → MySQL database* → Server `localhost` · Database `smart_college` → *Database* tab → user/password.
3. Tick the five `vw_…` views (plus `departments`) → *Load*.
4. Build relationships on `student_id` / `dept_name` as described in the guide.
Attendance and marks entered in the Streamlit app appear in Power BI after *Refresh*.

## 7. Screenshots
Add your own after running the app (Windows: Win + Shift + S) and save them in `docs/screenshots/`:
`login.png`, `admin_dashboard.png`, `attendance.png`, `student_dashboard.png`, `powerbi_overview.png`.

## 8. Troubleshooting
| Problem | Fix |
|---|---|
| `Access denied for user 'root'` | Wrong `DB_PASSWORD` in `.env`. |
| `Unknown database 'smart_college'` | Run Step 3 again. |
| `Can't connect to MySQL server` | Start the `MySQL80` service (`services.msc`). |
| `streamlit` is not recognised | Activate the venv (`venv\Scripts\activate`) first. |
| Demo login says wrong password | Re-import the SQL file (it resets the admin password to `admin123`). |
| `pip install` fails on very new Python | Use Python 3.11 or 3.12. |

## 9. Future enhancements
Email/SMS alerts for low attendance · QR-code attendance · fee management · parent login · library module · assignment upload · REST API (FastAPI) · Docker deployment · automatic CGPA/SGPA.

## 10. Team members
| Name | Roll no | Role |
|---|---|---|
| Keshav Kumar | _your roll no._ | _Developer_ |
| _Member 2_ | | |

Guide: _name of your project guide_ · Institute: Rajshree Institute of Management and Technology, Bareilly.
