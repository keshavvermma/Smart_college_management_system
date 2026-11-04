# Viva Questions and Answers

## A. Project basics
**1. What is your project?** A web-based Smart College Management System with Admin, Faculty and Student roles, built with Python, Streamlit, MySQL and Pandas, with Power BI dashboards on the same database.

**2. Why Streamlit?** It builds data-driven web UIs in pure Python (forms, tables, charts) without HTML/JS, ideal for a mini project and for Pandas-based apps.

**3. Why MySQL?** Free, reliable, relational; supports foreign keys, constraints, transactions and views, and Power BI has a MySQL connector.

**4. Why is this not a static project?** Every operation reads/writes MySQL: login, add/update/delete/search, attendance, marks, notices and dashboards are all database queries.

**5. Who uses which module?** Admin – everything; Faculty – attendance, marks, notices for own subjects; Student – read-only own data.

## B. Database
**6. What is normalisation? Which form is your DB in?** Organising data to remove redundancy. It is in 3NF: department data stored once; derived values (percentage, grade) are not stored.

**7. Primary key vs foreign key vs unique key?** PK uniquely identifies a row (not null); FK refers to a PK in another table to keep integrity; UNIQUE prevents duplicates (roll_no, email) but allows one NULL.

**8. Explain ON DELETE RESTRICT / CASCADE / SET NULL as used.** RESTRICT: can't delete a department that has students. CASCADE: deleting a student deletes their attendance and marks. SET NULL: deleting a faculty keeps subjects/attendance but clears the teacher.

**9. Why a UNIQUE key on (student_id, subject_id, date)?** One attendance record per student per subject per day; saving again updates it (`INSERT … ON DUPLICATE KEY UPDATE`).

**10. What is a view? Why use views?** A saved SELECT. `vw_*` views contain joins and calculations once and are reused by Power BI.

**11. What is an index?** A structure that speeds up lookups (e.g. (department_id, semester)); costs some write speed and space.

**12. What is a transaction?** A group of statements that all succeed or all fail (ACID). Creating a student and their login account is one transaction.

**13. Write a query for attendance %.**
`SELECT student_id, ROUND(100*SUM(status='Present')/COUNT(*),2) AS pct FROM attendance GROUP BY student_id;`

**14. Difference between WHERE and HAVING?** WHERE filters rows before grouping; HAVING filters groups after aggregation (e.g. `HAVING pct < 75`).

**15. INNER JOIN vs LEFT JOIN?** Inner returns only matching rows; left returns all left rows (students with no attendance still appear).

## C. Security
**16. How are passwords stored?** Salted PBKDF2-HMAC-SHA256 (260,000 iterations): `pbkdf2_sha256$iterations$salt$hash`. Plain text is never stored.

**17. Why a salt?** Same password gives different hashes and rainbow tables don't work.

**18. What is SQL injection and how did you prevent it?** Malicious input altering a query. All queries use parameter placeholders (`%s`) with values passed separately.

**19. How is role-based access implemented?** `app.py` builds a menu per role, and each page calls `require_role(...)`. Student queries use the `ref_id` from the server-side session, so they can't request another student's ID. Faculty saves re-check subject ownership.

**20. Where is the DB password?** In `.env` (not in code, not in Git); `.env.example` shows the format.

**21. Session management?** `st.session_state` holds the logged-in user; inactivity timeout 30 min; logout clears it; 5 failed logins lock for 60 s.

## D. Python / Streamlit / Pandas
**22. How does Streamlit run?** The script re-runs top-to-bottom on every interaction; `st.session_state` keeps values between runs.

**23. What does `st.navigation` do?** Registers the pages the current role is allowed to see; pages not in the list can't be opened.

**24. Why `mysql-connector-python`?** Official Oracle driver, pure Python/C, supports MySQL 8 authentication.

**25. Role of Pandas?** Converting query results to DataFrames, computing percentage/grade columns, grouping subject totals, CSV export.

**26. What is `st.data_editor`?** An editable table widget; used for ticking Present/Absent and typing marks for the whole class at once.

## E. Business rules
**27. Attendance formula and warning?** (Present ÷ Total) × 100; below 75 % shows ⚠️.

**28. Grade scale?** 90+ A+, 80-89 A, 70-79 B+, 60-69 B, 50-59 C, 40-49 D, below 40 F; Pass ≥ 40 %.

**29. How is the subject total computed?** Sum of marks obtained over all exams ÷ sum of maximum marks × 100.

## F. Power BI
**30. How does Power BI connect?** Get Data → MySQL → localhost / smart_college (needs MySQL Connector/NET); import the `vw_*` views and refresh when data changes.

**31. What is a measure in DAX?** A calculation evaluated in the current filter context, e.g. `Average Attendance = DIVIDE([Present Classes],[Total Classes])*100`.

**32. Import vs DirectQuery?** Import copies data into Power BI (fast, manual refresh); DirectQuery queries the database live (always fresh, slower).

## G. Design / improvement
**33. Which diagrams did you draw?** ER, DFD level 0 and 1, use case, architecture (in `docs/diagrams`).

**34. Limitations?** Local deployment, no notifications, session-based lock-out, manual Power BI refresh, no SGPA.

**35. Future work?** E-mail/SMS alerts, QR attendance, fee/library modules, REST API, Docker/cloud, SGPA/CGPA.

**36. How did you test?** Unit tests for formulas/validators/hashing, a smoke test of all pages for all roles, `check_setup.py` for the live DB connection, and manual test cases (see report §16).
