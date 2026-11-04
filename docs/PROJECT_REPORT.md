# SMART COLLEGE MANAGEMENT SYSTEM
### A B.Tech (CSE) Mini Project Report
Submitted by: Keshav Kumar · Rajshree Institute of Management and Technology, Bareilly · Session 2026-27
Guide: ____________  ·  Department of Computer Science & Engineering

*(Replace the blanks, add a certificate page, acknowledgement and index with page numbers in Word.)*

---

## 1. Abstract
Colleges still keep attendance in registers and marks in spreadsheets, which causes duplicate work, errors and delayed information. This project presents a web-based **Smart College Management System** built with Python, Streamlit and MySQL. It gives three roles – Admin, Faculty and Student – their own secured dashboards. Admins manage students, faculty, departments, subjects, timetable and notices; faculty mark attendance and enter marks for their own subjects; students see only their own profile, attendance, results, timetable and notices. Attendance percentage, grade and pass/fail are calculated automatically and students below 75 % attendance are flagged. All data is stored in a normalised MySQL database, processed with Pandas, and exposed through SQL views to **Power BI** for management analytics. Passwords are stored as salted PBKDF2 hashes and every query is parameterised.

## 2. Introduction
Educational institutions generate large volumes of academic data every day. A digital management system centralises this data, speeds up routine work and supports decisions with analytics. This project delivers such a system as a lightweight, locally deployable web application suitable for a small or medium engineering college.

## 3. Problem Statement
Manual / spreadsheet-based record keeping leads to: (a) time-consuming attendance and result preparation, (b) no early warning for students with shortage of attendance, (c) data scattered over files, inconsistent and insecure, (d) students depending on staff to know their own attendance and marks, (e) no consolidated analytics for management. A secure, role-based, database-driven system is needed.

## 4. Objectives
1. Build a role-based web application (Admin, Faculty, Student) with secure login.
2. Provide complete CRUD for students, faculty, departments and subjects.
3. Record attendance per subject per date and compute attendance % automatically with a 75 % warning.
4. Record marks per exam type and compute total, percentage, grade and pass/fail automatically.
5. Publish notices with priority, and maintain class timetables.
6. Generate Student, Attendance, Result and Faculty reports (CSV/PDF).
7. Prepare the database for Power BI dashboards (attendance, performance, student analytics).
8. Enforce security: hashing, RBAC, validation, parameterised SQL, no hard-coded credentials.

## 5. Existing System
Paper attendance registers, Excel mark sheets, notice boards and WhatsApp groups. **Drawbacks:** manual calculation errors, no real-time view for students, no access control or audit, redundancy, difficult analysis, lost records.

## 6. Proposed System
A centralised Streamlit + MySQL application. **Advantages:** single source of truth, automatic calculations, instant student access to own data, shortage-of-attendance alerts, access restricted by role, analytics through Power BI, easy installation (one SQL file + `pip install`). Both the app and Power BI use the *same* database, so dashboards are always consistent with the application.

## 7. System Requirements
### 7.1 Hardware
| Item | Minimum | Recommended |
|---|---|---|
| Processor | Dual-core 2 GHz | Quad-core i5 / Ryzen 5 |
| RAM | 4 GB | 8 GB |
| Disk | 2 GB free | 10 GB SSD |
| Display / Network | 1366×768 / LAN or localhost | 1920×1080 |
### 7.2 Software
Windows 10/11 · Python 3.11/3.12 · MySQL Server 8.0 + MySQL Workbench · Streamlit, mysql-connector-python, Pandas, python-dotenv, ReportLab · Power BI Desktop + MySQL Connector/NET · any modern browser · VS Code (optional).

## 8. System Architecture
*(Figure: `docs/diagrams/architecture.png`)*
Three layers:
1. **Presentation layer** – Streamlit pages (`pages/`), sidebar navigation chosen by role in `app.py`.
2. **Application layer** – `utils/` (authentication, validators, calculations, UI helpers) and `database/queries.py` (all SQL, parameterised).
3. **Data layer** – MySQL database `smart_college` (9 tables, 5 views) accessed through `database/connection.py`; Power BI reads the views.

Request flow: browser → Streamlit script re-run → role check (`require_role`) → query function → MySQL → Pandas DataFrame / dict → widgets.

## 9. ER Diagram Description
*(Figure: `docs/diagrams/er_diagram.png`)*
**Entities:** Departments, Students, Faculty, Subjects, Attendance, Marks, Notices, Timetable, Users.
**Relationships**
* Department 1 — N Students, Faculty, Subjects, Timetable entries.
* Faculty 1 — N Subjects (a subject has at most one assigned teacher); Faculty 1 — N Attendance records (who marked them).
* Student 1 — N Attendance; Student 1 — N Marks.
* Subject 1 — N Attendance, Marks, Timetable slots.
* Users 1 — N Notices (author). A user row represents a login and points (via `role` + `ref_id`) to one student or one faculty member; Admin has no reference.
**Keys / constraints:** surrogate primary keys; UNIQUE on roll_no, email, subject_code, dept_name/code, username, and on (student, subject, date) and (student, subject, exam_type); CHECK constraints on semester (1-8), credits (1-6), marks range, class end time; foreign keys with RESTRICT (master data), CASCADE (student/subject child records) and SET NULL (faculty/author references).

## 10. DFD Level 0 (Context diagram)
*(Figure: `docs/diagrams/dfd_level0.png`)*
Single process "Smart College Management System". External entities: **Admin** (master data, notices, report requests → dashboards, reports), **Faculty** (attendance, marks, notices → class lists, subjects), **Student** (login, view requests → own profile, attendance, marks, timetable, notices). Data store: MySQL `smart_college`, which also feeds Power BI.

## 11. DFD Level 1
*(Figure: `docs/diagrams/dfd_level1.png`)*
| Process | Input | Output | Data store |
|---|---|---|---|
| 1.0 Authentication | username, password | session (role, ref id) | D1 users |
| 2.0 Master-data management | student / faculty / dept / subject details | confirmation, lists | D2 |
| 3.0 Attendance | subject, date, present/absent list | saved records, % and warnings | D3 attendance |
| 4.0 Marks & results | marks per student & exam | percentage, grade, pass/fail | D4 marks |
| 5.0 Notices & timetable | notice text, slots | published notices, timetable | D5 |
| 6.0 Reports & analytics | filters | tables, charts, CSV/PDF | D2, D3, D4 |
| 7.0 Power BI views | — | `vw_*` datasets | D2, D3, D4 |

## 12. Use Case Diagram Description
*(Figure: `docs/diagrams/use_case.png`)*
**Admin:** login, manage students / faculty / departments / subjects / timetable, assign faculty, mark attendance & marks (overview), manage notices, generate reports, view analytics, change password.
**Faculty:** login, mark attendance (own subjects), enter marks (own subjects), publish own notices, view dashboard and timetable, change password.
**Student:** login, view profile, attendance (with warning), marks/results, timetable, notices, change password.

## 13. Database Design
| Table | Important columns |
|---|---|
| departments | department_id PK, dept_name UK, dept_code UK |
| faculty | faculty_id PK, name, email UK, phone, department_id FK, designation, joining_date |
| students | student_id PK, roll_no UK, name, gender, date_of_birth, department_id FK, semester, email UK, phone, address, admission_year |
| subjects | subject_id PK, subject_code UK, subject_name, department_id FK, semester, credits, faculty_id FK |
| users | user_id PK, username UK, password_hash, role (admin/faculty/student), ref_id |
| attendance | attendance_id PK, student_id FK, subject_id FK, faculty_id FK, date, status (Present/Absent); UK(student,subject,date) |
| marks | mark_id PK, student_id FK, subject_id FK, exam_type, marks, max_marks; UK(student,subject,exam_type) |
| notices | notice_id PK, title, description, created_by FK, created_at, priority, is_published |
| timetable | timetable_id PK, department_id FK, semester, subject_id FK, day_of_week, start_time, end_time, room |

*Normalisation:* all tables are in 3NF – department names are stored once and referenced by id; percentages, grades and attendance % are **derived** (calculated in code/views) instead of stored, avoiding update anomalies. Indexes: composite (department, semester) on students/subjects/timetable, (subject, date) on attendance, unique keys above.
*Views:* `vw_attendance_summary`, `vw_attendance_detail`, `vw_marks_detail`, `vw_student_results`, `vw_student_overview`.

## 14. Module Description
1. **Authentication & session** (`utils/authentication.py`, `security.py`) – PBKDF2-SHA256 salted hashes, constant-time comparison, lock-out after 5 failures, 30-minute inactivity timeout, `require_role()` on every page.
2. **Admin dashboard** – counts, average attendance, average marks, defaulter list, department charts, latest notices.
3. **Student / Faculty / Department / Subject management** – add, edit, delete (with confirmation), search and filters; creating a student or faculty also creates the login account in one transaction.
4. **Attendance** – class selection → editable present/absent table → upsert into MySQL; summaries with % and warnings.
5. **Marks & results** – bulk entry per subject and exam type, validation 0…max, automatic percentage/grade/result, student result view with subject totals.
6. **Notices** – create, edit, delete, publish/unpublish, priority; faculty can alter only their own.
7. **Timetable** – admin builds weekly slots with faculty clash detection; students/faculty view a grid.
8. **Reports** – student list, attendance, results, faculty; CSV and optional PDF.
9. **Settings** – change own password (strength rules), admin password reset.
10. **Power BI integration** – SQL views and the guide in `POWERBI_GUIDE.md`.

## 15. Implementation
* **Language/UI:** Python 3, Streamlit (`st.navigation` for role-based menus, forms, tabs, `st.data_editor` for attendance/marks tables, metrics for cards).
* **Database access:** `mysql-connector-python`; every statement uses `%s` placeholders; multi-statement operations use transactions (commit/rollback).
* **Data processing:** Pandas for tables, percentage columns, grouping subject totals and CSV export.
* **Configuration:** `.env` via python-dotenv; `.env.example` provided.
* **Key formulas:** Attendance % = Present ÷ Total × 100; Percentage = Marks ÷ Max × 100; Grade: ≥90 A+, ≥80 A, ≥70 B+, ≥60 B, ≥50 C, ≥40 D, else F; Pass if ≥ 40 %.
* **Authorisation rules:** students' queries always use the `ref_id` stored in the server-side session (never a value typed in the browser); faculty attendance/marks saves re-check that the subject is assigned to the logged-in faculty.

## 16. Testing
| Type | What was done | Result |
|---|---|---|
| Unit tests (`tests/`) | percentage, grade boundaries (39.99/40/89.99/90 …), pass/fail, validators (email, phone, student, faculty, subject, notice, marks, password), password hashing and the sample-data hashes | 14 tests pass |
| Smoke test (`tests/smoke_stub_test.py`) | every page's render function executed for Admin, Faculty and Student with a fake Streamlit and fake database | no exceptions |
| Setup check (`check_setup.py`) | packages, `.env`, real MySQL connection, tables, views, demo login | run on your machine |
| Manual test cases | below | to be executed and ticked by you |

**Manual test cases to run (record result and screenshot):**
| # | Test | Expected |
|---|---|---|
| 1 | Login admin/admin123 | Admin dashboard, 11 menu items |
| 2 | Wrong password 5 times | Login blocked for 60 s |
| 3 | Add student with phone "123" | Validation error, nothing saved |
| 4 | Add student valid → check MySQL `SELECT * FROM students` | Row exists; login account created |
| 5 | Delete department that has students | Friendly error (RESTRICT) |
| 6 | Faculty marks attendance for own subject | Rows appear in `attendance` |
| 7 | Student `cse24001` opens Attendance | 66.7 % overall, warning shown |
| 8 | Enter marks 55/50 | Rejected (above maximum) |
| 9 | Enter 14/30 Internal | 46.67 %, grade D, Pass |
| 10 | Student tries other pages/IDs | Only own data shown |
| 11 | Admin → Reports → download CSV | File downloads |
| 12 | Add attendance, refresh Power BI | New value appears |

## 17. Results
With the supplied sample data (26 students, 8 faculty, 5 departments, 15 subjects): overall attendance ≈ 84.6 %; average marks ≈ 66 %; 3 students are below 75 % overall (Rahul Kumar 66.7 %, Simran Kaur 50 %, Sachin Kashyap 66.7 %) and are flagged on the dashboard and reports. Insert your screenshots of the Admin dashboard, attendance screen, student result view and the Power BI pages here.

## 18. Limitations
* Single-college, English only, runs on one server/PC (no cloud deployment by default).
* Login lock-out is per browser session, not stored in the database.
* No e-mail/SMS alerts, no fee, library or hostel modules, no file uploads.
* Power BI refresh is manual (Import mode) unless a gateway is configured.
* Result calculation is percentage-based; no credit-weighted SGPA/CGPA yet.
* The full application has been tested here with unit tests and a simulated UI; final system testing on your Windows + MySQL machine is part of the submission.

## 19. Future Scope
E-mail/SMS/WhatsApp alerts for shortage of attendance, QR/face-recognition attendance, SGPA/CGPA and mark-sheet PDF, fee and library modules, parent login, REST API with FastAPI and a mobile app, Docker/cloud deployment, Power BI DirectQuery with gateway, audit log, two-factor login.

## 20. Conclusion
The Smart College Management System replaces manual registers with a secure, automated and analysable platform. It demonstrates a complete full-stack workflow – relational design, Python business logic, a web UI and BI reporting – using one shared database, and can be extended into a full ERP for colleges.

## 21. References
1. Streamlit documentation – https://docs.streamlit.io
2. MySQL 8.0 Reference Manual – https://dev.mysql.com/doc/refman/8.0/en/
3. MySQL Connector/Python Developer Guide – https://dev.mysql.com/doc/connector-python/en/
4. pandas documentation – https://pandas.pydata.org/docs/
5. Microsoft Power BI documentation – https://learn.microsoft.com/power-bi/
6. Python `hashlib.pbkdf2_hmac` – https://docs.python.org/3/library/hashlib.html
7. Elmasri & Navathe, *Fundamentals of Database Systems*, Pearson.
