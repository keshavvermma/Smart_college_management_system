"""
database/queries.py - every SQL query used by the application.

The pages never write SQL themselves; they call the functions below.
All values are passed as parameters (%s) - never pasted into the SQL text.
"""
from config import ATTENDANCE_THRESHOLD, DAYS, DEFAULT_FACULTY_PASSWORD, DEFAULT_STUDENT_PASSWORD
from database.connection import execute, execute_many, fetch_all, fetch_one, transaction
from utils.security import hash_password

DAY_ORDER_SQL = "FIELD(t.day_of_week, " + ", ".join(f"'{d}'" for d in DAYS) + ")"


# =====================================================================
# USERS / LOGIN
# =====================================================================
def get_user_by_username(username):
    return fetch_one(
        "SELECT user_id, username, password_hash, role, ref_id FROM users WHERE username = %s",
        (username,),
    )


def get_user_by_id(user_id):
    return fetch_one("SELECT user_id, username, password_hash, role, ref_id FROM users WHERE user_id = %s", (user_id,))


def update_password(user_id, new_hash):
    execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, user_id))


def get_display_name(role, ref_id):
    if role == "admin":
        return "Administrator"
    table, column = ("students", "student_id") if role == "student" else ("faculty", "faculty_id")
    row = fetch_one(f"SELECT name FROM {table} WHERE {column} = %s", (ref_id,))
    return row["name"] if row else "User"


# =====================================================================
# DEPARTMENTS
# =====================================================================
def get_departments():
    return fetch_all(
        """
        SELECT d.department_id, d.dept_name, d.dept_code,
               (SELECT COUNT(*) FROM students s  WHERE s.department_id  = d.department_id) AS students,
               (SELECT COUNT(*) FROM faculty f   WHERE f.department_id  = d.department_id) AS faculty,
               (SELECT COUNT(*) FROM subjects sb WHERE sb.department_id = d.department_id) AS subjects
        FROM departments d ORDER BY d.dept_name
        """
    )


def add_department(name, code):
    return execute("INSERT INTO departments (dept_name, dept_code) VALUES (%s, %s)", (name.strip(), code.strip().upper()))[0]


def update_department(department_id, name, code):
    execute(
        "UPDATE departments SET dept_name = %s, dept_code = %s WHERE department_id = %s",
        (name.strip(), code.strip().upper(), department_id),
    )


def delete_department(department_id):
    # Fails (foreign key) if students / faculty / subjects still belong to it.
    execute("DELETE FROM departments WHERE department_id = %s", (department_id,))


# =====================================================================
# STUDENTS
# =====================================================================
STUDENT_SELECT = """
    SELECT s.student_id, s.roll_no, s.name, s.gender, s.date_of_birth, s.department_id,
           d.dept_name AS department, s.semester, s.email, s.phone, s.address, s.admission_year
    FROM students s JOIN departments d ON d.department_id = s.department_id
"""


def search_students(search="", dept_id=None, semester=None):
    sql = STUDENT_SELECT + " WHERE 1 = 1"
    params = []
    if search and search.strip():
        like = f"%{search.strip()}%"
        sql += " AND (s.name LIKE %s OR s.roll_no LIKE %s OR s.email LIKE %s)"
        params += [like, like, like]
    if dept_id:
        sql += " AND s.department_id = %s"
        params.append(dept_id)
    if semester:
        sql += " AND s.semester = %s"
        params.append(semester)
    sql += " ORDER BY s.roll_no"
    return fetch_all(sql, params)


def get_student(student_id):
    return fetch_one(STUDENT_SELECT + " WHERE s.student_id = %s", (student_id,))


def add_student(d):
    """Insert the student AND create the login account in one transaction."""
    with transaction() as cur:
        cur.execute(
            """INSERT INTO students (roll_no, name, gender, date_of_birth, department_id, semester,
                                     email, phone, address, admission_year)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (d["roll_no"].strip().upper(), d["name"].strip(), d["gender"], d["date_of_birth"], d["department_id"],
             d["semester"], d["email"].strip().lower(), d["phone"].strip(), (d.get("address") or "").strip(),
             d["admission_year"]),
        )
        student_id = cur.lastrowid
        cur.execute(
            "INSERT INTO users (username, password_hash, role, ref_id) VALUES (%s, %s, 'student', %s)",
            (d["roll_no"].strip().lower(), hash_password(DEFAULT_STUDENT_PASSWORD), student_id),
        )
    return student_id


def update_student(student_id, d):
    with transaction() as cur:
        cur.execute(
            """UPDATE students SET roll_no=%s, name=%s, gender=%s, date_of_birth=%s, department_id=%s,
                      semester=%s, email=%s, phone=%s, address=%s, admission_year=%s
               WHERE student_id=%s""",
            (d["roll_no"].strip().upper(), d["name"].strip(), d["gender"], d["date_of_birth"], d["department_id"],
             d["semester"], d["email"].strip().lower(), d["phone"].strip(), (d.get("address") or "").strip(),
             d["admission_year"], student_id),
        )
        cur.execute(
            "UPDATE users SET username=%s WHERE role='student' AND ref_id=%s",
            (d["roll_no"].strip().lower(), student_id),
        )


def delete_student(student_id):
    """Removes the student, their login, and (by CASCADE) attendance and marks."""
    with transaction() as cur:
        cur.execute("DELETE FROM users WHERE role='student' AND ref_id=%s", (student_id,))
        cur.execute("DELETE FROM students WHERE student_id=%s", (student_id,))


def get_students_for_class(dept_id, semester):
    return fetch_all(
        "SELECT student_id, roll_no, name FROM students WHERE department_id=%s AND semester=%s ORDER BY roll_no",
        (dept_id, semester),
    )


# =====================================================================
# FACULTY
# =====================================================================
FACULTY_SELECT = """
    SELECT f.faculty_id, f.name, f.email, f.phone, f.department_id, d.dept_name AS department,
           f.designation, f.joining_date,
           (SELECT COUNT(*) FROM subjects sb WHERE sb.faculty_id = f.faculty_id) AS subject_count,
           (SELECT GROUP_CONCAT(sb.subject_code ORDER BY sb.subject_code SEPARATOR ', ')
              FROM subjects sb WHERE sb.faculty_id = f.faculty_id) AS subjects
    FROM faculty f JOIN departments d ON d.department_id = f.department_id
"""


def get_faculty_list(search="", dept_id=None):
    sql = FACULTY_SELECT + " WHERE 1 = 1"
    params = []
    if search and search.strip():
        like = f"%{search.strip()}%"
        sql += " AND (f.name LIKE %s OR f.email LIKE %s OR f.designation LIKE %s)"
        params += [like, like, like]
    if dept_id:
        sql += " AND f.department_id = %s"
        params.append(dept_id)
    sql += " ORDER BY f.name"
    return fetch_all(sql, params)


def get_faculty(faculty_id):
    return fetch_one(FACULTY_SELECT + " WHERE f.faculty_id = %s", (faculty_id,))


def add_faculty(d):
    """Insert faculty AND create the login account (username = part of email before @)."""
    with transaction() as cur:
        cur.execute(
            """INSERT INTO faculty (name, email, phone, department_id, designation, joining_date)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (d["name"].strip(), d["email"].strip().lower(), d["phone"].strip(), d["department_id"],
             d["designation"].strip(), d["joining_date"]),
        )
        faculty_id = cur.lastrowid
        cur.execute(
            "INSERT INTO users (username, password_hash, role, ref_id) VALUES (%s, %s, 'faculty', %s)",
            (d["email"].strip().lower().split("@")[0], hash_password(DEFAULT_FACULTY_PASSWORD), faculty_id),
        )
    return faculty_id


def update_faculty(faculty_id, d):
    execute(
        """UPDATE faculty SET name=%s, email=%s, phone=%s, department_id=%s, designation=%s, joining_date=%s
           WHERE faculty_id=%s""",
        (d["name"].strip(), d["email"].strip().lower(), d["phone"].strip(), d["department_id"],
         d["designation"].strip(), d["joining_date"], faculty_id),
    )


def delete_faculty(faculty_id):
    """Subjects become 'Unassigned' (ON DELETE SET NULL); the login account is removed."""
    with transaction() as cur:
        cur.execute("DELETE FROM users WHERE role='faculty' AND ref_id=%s", (faculty_id,))
        cur.execute("DELETE FROM faculty WHERE faculty_id=%s", (faculty_id,))


def set_faculty_subjects(faculty_id, subject_ids):
    """Make `subject_ids` the complete list of subjects taught by this faculty member."""
    with transaction() as cur:
        cur.execute("UPDATE subjects SET faculty_id = NULL WHERE faculty_id = %s", (faculty_id,))
        for subject_id in subject_ids:
            cur.execute("UPDATE subjects SET faculty_id = %s WHERE subject_id = %s", (faculty_id, subject_id))


# =====================================================================
# SUBJECTS
# =====================================================================
def get_subjects(dept_id=None, semester=None, faculty_id=None, search=""):
    sql = """
        SELECT sb.subject_id, sb.subject_code, sb.subject_name, sb.department_id,
               d.dept_name AS department, sb.semester, sb.credits, sb.faculty_id,
               COALESCE(f.name, 'Unassigned') AS faculty
        FROM subjects sb
        JOIN departments d ON d.department_id = sb.department_id
        LEFT JOIN faculty f ON f.faculty_id = sb.faculty_id
        WHERE 1 = 1
    """
    params = []
    if dept_id:
        sql += " AND sb.department_id = %s"
        params.append(dept_id)
    if semester:
        sql += " AND sb.semester = %s"
        params.append(semester)
    if faculty_id:
        sql += " AND sb.faculty_id = %s"
        params.append(faculty_id)
    if search and search.strip():
        like = f"%{search.strip()}%"
        sql += " AND (sb.subject_code LIKE %s OR sb.subject_name LIKE %s)"
        params += [like, like]
    sql += " ORDER BY d.dept_name, sb.semester, sb.subject_code"
    return fetch_all(sql, params)


def get_subject(subject_id):
    rows = fetch_all(
        """SELECT subject_id, subject_code, subject_name, department_id, semester, credits, faculty_id
           FROM subjects WHERE subject_id = %s""",
        (subject_id,),
    )
    return rows[0] if rows else None


def add_subject(d):
    return execute(
        """INSERT INTO subjects (subject_code, subject_name, department_id, semester, credits, faculty_id)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (d["subject_code"].strip().upper(), d["subject_name"].strip(), d["department_id"], d["semester"],
         d["credits"], d.get("faculty_id")),
    )[0]


def update_subject(subject_id, d):
    execute(
        """UPDATE subjects SET subject_code=%s, subject_name=%s, department_id=%s, semester=%s,
                  credits=%s, faculty_id=%s WHERE subject_id=%s""",
        (d["subject_code"].strip().upper(), d["subject_name"].strip(), d["department_id"], d["semester"],
         d["credits"], d.get("faculty_id"), subject_id),
    )


def delete_subject(subject_id):
    """Also deletes attendance, marks and timetable rows of the subject (ON DELETE CASCADE)."""
    execute("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))


def get_student_subjects(student_id):
    """Subjects of the student's own department and semester."""
    return fetch_all(
        """SELECT sb.subject_id, sb.subject_code, sb.subject_name, sb.credits,
                  COALESCE(f.name, 'Unassigned') AS faculty
           FROM students st
           JOIN subjects sb ON sb.department_id = st.department_id AND sb.semester = st.semester
           LEFT JOIN faculty f ON f.faculty_id = sb.faculty_id
           WHERE st.student_id = %s ORDER BY sb.subject_code""",
        (student_id,),
    )


# =====================================================================
# ATTENDANCE
# =====================================================================
def get_attendance_for_date(subject_id, att_date):
    rows = fetch_all(
        "SELECT student_id, status FROM attendance WHERE subject_id = %s AND `date` = %s",
        (subject_id, att_date),
    )
    return {r["student_id"]: r["status"] for r in rows}


def save_attendance(subject_id, att_date, records, faculty_id=None):
    """
    records = {student_id: 'Present' | 'Absent'}
    faculty_id: the logged-in faculty member (None for admin). A faculty member can only
    save attendance for subjects assigned to them - enforced here, not just in the UI.
    """
    subject = get_subject(subject_id)
    if subject is None:
        raise ValueError("Subject not found.")
    if faculty_id is not None and subject["faculty_id"] != faculty_id:
        raise PermissionError("You are not assigned to this subject.")
    valid_ids = {s["student_id"] for s in get_students_for_class(subject["department_id"], subject["semester"])}
    rows = []
    for student_id, status in records.items():
        if student_id in valid_ids and status in ("Present", "Absent"):
            rows.append((student_id, subject_id, subject["faculty_id"], att_date, status))
    if not rows:
        raise ValueError("No valid attendance rows to save.")
    execute_many(
        """INSERT INTO attendance (student_id, subject_id, faculty_id, `date`, status)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE status = VALUES(status), faculty_id = VALUES(faculty_id)""",
        rows,
    )
    return len(rows)


def attendance_summary(dept_id=None, semester=None, subject_id=None, student_id=None, faculty_id=None):
    """Attendance % for every student-subject pair (from the vw_attendance_summary view)."""
    sql = """SELECT student_id, subject_id, roll_no, student_name, dept_name, semester, subject_code,
                    subject_name, total_classes, present_classes, attendance_percentage, attendance_status
             FROM vw_attendance_summary WHERE 1 = 1"""
    params = []
    for column, value in (("department_id", dept_id), ("semester", semester), ("subject_id", subject_id),
                          ("student_id", student_id), ("faculty_id", faculty_id)):
        if value:
            sql += f" AND {column} = %s"
            params.append(value)
    sql += " ORDER BY roll_no, subject_code"
    return fetch_all(sql, params)


def overall_attendance(dept_id=None, semester=None, faculty_id=None, student_id=None):
    """Overall attendance % per student, lowest first."""
    sql = """SELECT student_id, roll_no, student_name, dept_name, semester,
                    SUM(present_classes) AS present_classes, SUM(total_classes) AS total_classes,
                    ROUND(100 * SUM(present_classes) / SUM(total_classes), 2) AS attendance_percentage
             FROM vw_attendance_summary WHERE 1 = 1"""
    params = []
    for column, value in (("department_id", dept_id), ("semester", semester), ("faculty_id", faculty_id),
                          ("student_id", student_id)):
        if value:
            sql += f" AND {column} = %s"
            params.append(value)
    sql += " GROUP BY student_id, roll_no, student_name, dept_name, semester ORDER BY attendance_percentage, roll_no"
    return fetch_all(sql, params)


def low_attendance_students(threshold=ATTENDANCE_THRESHOLD, faculty_id=None):
    return [r for r in overall_attendance(faculty_id=faculty_id) if r["attendance_percentage"] < threshold]


def attendance_history(student_id, limit=40):
    return fetch_all(
        """SELECT a.`date` AS date, sb.subject_code, sb.subject_name, a.status
           FROM attendance a JOIN subjects sb ON sb.subject_id = a.subject_id
           WHERE a.student_id = %s ORDER BY a.`date` DESC, sb.subject_code LIMIT %s""",
        (student_id, limit),
    )


def attendance_monthly_trend():
    return fetch_all(
        """SELECT CONCAT(YEAR(`date`), '-', LPAD(MONTH(`date`), 2, '0')) AS month,
                  ROUND(100 * SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / COUNT(*), 2) AS attendance
           FROM attendance GROUP BY YEAR(`date`), MONTH(`date`) ORDER BY YEAR(`date`), MONTH(`date`)"""
    )


# =====================================================================
# MARKS / RESULTS
# =====================================================================
def get_marks_for_entry(subject_id, exam_type):
    rows = fetch_all(
        "SELECT student_id, marks, max_marks FROM marks WHERE subject_id = %s AND exam_type = %s",
        (subject_id, exam_type),
    )
    return {r["student_id"]: r for r in rows}


def save_marks(subject_id, exam_type, max_marks, records, faculty_id=None):
    """
    records = {student_id: marks}. Enforces ownership for faculty and validates every value.
    Returns number of rows saved.
    """
    subject = get_subject(subject_id)
    if subject is None:
        raise ValueError("Subject not found.")
    if faculty_id is not None and subject["faculty_id"] != faculty_id:
        raise PermissionError("You are not assigned to this subject.")
    if max_marks is None or max_marks <= 0:
        raise ValueError("Maximum marks must be greater than 0.")
    valid_ids = {s["student_id"] for s in get_students_for_class(subject["department_id"], subject["semester"])}
    rows = []
    for student_id, value in records.items():
        if student_id not in valid_ids:
            continue
        if value < 0 or value > max_marks:
            raise ValueError(f"Marks must be between 0 and {max_marks:g}.")
        rows.append((student_id, subject_id, exam_type, value, max_marks))
    if not rows:
        raise ValueError("No marks to save.")
    execute_many(
        """INSERT INTO marks (student_id, subject_id, exam_type, marks, max_marks)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE marks = VALUES(marks), max_marks = VALUES(max_marks)""",
        rows,
    )
    return len(rows)


def delete_mark(mark_id):
    execute("DELETE FROM marks WHERE mark_id = %s", (mark_id,))


def get_marks(student_id=None, subject_id=None, dept_id=None, semester=None, exam_type=None, faculty_id=None):
    sql = """SELECT mark_id, student_id, roll_no, student_name, dept_name, semester, subject_code,
                    subject_name, exam_type, marks, max_marks, percentage, grade, result
             FROM vw_marks_detail WHERE 1 = 1"""
    params = []
    for column, value in (("student_id", student_id), ("subject_id", subject_id), ("department_id", dept_id),
                          ("semester", semester), ("exam_type", exam_type), ("faculty_id", faculty_id)):
        if value:
            sql += f" AND {column} = %s"
            params.append(value)
    sql += " ORDER BY roll_no, subject_code, exam_type"
    return fetch_all(sql, params)


def get_results(student_id=None, dept_id=None, semester=None, subject_id=None, faculty_id=None):
    """Total marks, percentage, grade and Pass/Fail per student per subject."""
    sql = """SELECT student_id, roll_no, student_name, dept_name, semester, subject_code, subject_name,
                    total_marks, total_max_marks, percentage, grade, result
             FROM vw_student_results WHERE 1 = 1"""
    params = []
    for column, value in (("student_id", student_id), ("department_id", dept_id), ("semester", semester),
                          ("subject_id", subject_id), ("faculty_id", faculty_id)):
        if value:
            sql += f" AND {column} = %s"
            params.append(value)
    sql += " ORDER BY roll_no, subject_code"
    return fetch_all(sql, params)


# =====================================================================
# NOTICES
# =====================================================================
NOTICE_SELECT = """
    SELECT n.notice_id, n.title, n.description, n.created_by, n.created_at, n.priority, n.is_published,
           COALESCE(CASE WHEN u.role = 'admin' THEN 'Administrator' ELSE f.name END, u.username, 'Unknown') AS author
    FROM notices n
    LEFT JOIN users u   ON u.user_id = n.created_by
    LEFT JOIN faculty f ON u.role = 'faculty' AND f.faculty_id = u.ref_id
"""


def get_notices(published_only=True, limit=None, created_by=None):
    sql = NOTICE_SELECT + " WHERE 1 = 1"
    params = []
    if published_only:
        sql += " AND n.is_published = 1"
    if created_by:
        sql += " AND n.created_by = %s"
        params.append(created_by)
    sql += " ORDER BY n.created_at DESC, n.notice_id DESC"
    if limit:
        sql += " LIMIT %s"
        params.append(int(limit))
    return fetch_all(sql, params)


def get_notice(notice_id):
    return fetch_one(NOTICE_SELECT + " WHERE n.notice_id = %s", (notice_id,))


def add_notice(title, description, priority, created_by, is_published=True):
    return execute(
        "INSERT INTO notices (title, description, priority, created_by, is_published) VALUES (%s, %s, %s, %s, %s)",
        (title.strip(), description.strip(), priority, created_by, 1 if is_published else 0),
    )[0]


def _check_notice_owner(notice_id, owner_user_id):
    """Faculty may only change notices they created (admin passes owner_user_id=None)."""
    if owner_user_id is None:
        return
    row = fetch_one("SELECT created_by FROM notices WHERE notice_id = %s", (notice_id,))
    if row is None or row["created_by"] != owner_user_id:
        raise PermissionError("You can only change notices that you created.")


def update_notice(notice_id, title, description, priority, is_published, owner_user_id=None):
    _check_notice_owner(notice_id, owner_user_id)
    execute(
        "UPDATE notices SET title=%s, description=%s, priority=%s, is_published=%s WHERE notice_id=%s",
        (title.strip(), description.strip(), priority, 1 if is_published else 0, notice_id),
    )


def delete_notice(notice_id, owner_user_id=None):
    _check_notice_owner(notice_id, owner_user_id)
    execute("DELETE FROM notices WHERE notice_id = %s", (notice_id,))


def count_recent_notices(days=7):
    row = fetch_one(
        "SELECT COUNT(*) AS c FROM notices WHERE is_published = 1 AND created_at >= NOW() - INTERVAL %s DAY",
        (int(days),),
    )
    return row["c"] if row else 0


# =====================================================================
# TIMETABLE
# =====================================================================
def get_timetable(dept_id, semester):
    return fetch_all(
        f"""SELECT t.timetable_id, t.day_of_week, t.start_time, t.end_time, t.room,
                   sb.subject_code, sb.subject_name, COALESCE(f.name, '') AS faculty
            FROM timetable t
            JOIN subjects sb ON sb.subject_id = t.subject_id
            LEFT JOIN faculty f ON f.faculty_id = sb.faculty_id
            WHERE t.department_id = %s AND t.semester = %s
            ORDER BY {DAY_ORDER_SQL}, t.start_time""",
        (dept_id, semester),
    )


def get_faculty_timetable(faculty_id):
    return fetch_all(
        f"""SELECT t.timetable_id, t.day_of_week, t.start_time, t.end_time, t.room,
                   sb.subject_code, sb.subject_name, d.dept_code, t.semester
            FROM timetable t
            JOIN subjects sb ON sb.subject_id = t.subject_id
            JOIN departments d ON d.department_id = t.department_id
            WHERE sb.faculty_id = %s
            ORDER BY {DAY_ORDER_SQL}, t.start_time""",
        (faculty_id,),
    )


def timetable_conflict(dept_id, semester, day, start, end):
    """True if the same class already has a period overlapping start-end on that day."""
    row = fetch_one(
        """SELECT COUNT(*) AS c FROM timetable
           WHERE department_id = %s AND semester = %s AND day_of_week = %s
             AND start_time < %s AND end_time > %s""",
        (dept_id, semester, day, end, start),
    )
    return bool(row and row["c"])


def add_timetable_entry(dept_id, semester, subject_id, day, start, end, room):
    return execute(
        """INSERT INTO timetable (department_id, semester, subject_id, day_of_week, start_time, end_time, room)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (dept_id, semester, subject_id, day, start, end, room),
    )[0]


def delete_timetable_entry(timetable_id):
    execute("DELETE FROM timetable WHERE timetable_id = %s", (timetable_id,))


# =====================================================================
# DASHBOARD STATISTICS
# =====================================================================
def admin_stats():
    counts = fetch_one(
        """SELECT (SELECT COUNT(*) FROM students)    AS students,
                  (SELECT COUNT(*) FROM faculty)     AS faculty,
                  (SELECT COUNT(*) FROM departments) AS departments,
                  (SELECT COUNT(*) FROM subjects)    AS subjects"""
    )
    att = fetch_one(
        "SELECT ROUND(100 * SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct FROM attendance"
    )
    mk = fetch_one("SELECT ROUND(AVG(100 * marks / max_marks), 2) AS pct FROM marks")
    counts["avg_attendance"] = (att or {}).get("pct") or 0.0
    counts["avg_marks"] = (mk or {}).get("pct") or 0.0
    counts["low_attendance"] = len(low_attendance_students())
    return counts


def faculty_stats(faculty_id):
    subjects = get_subjects(faculty_id=faculty_id)
    students = fetch_one(
        """SELECT COUNT(DISTINCT st.student_id) AS c FROM subjects sb
           JOIN students st ON st.department_id = sb.department_id AND st.semester = sb.semester
           WHERE sb.faculty_id = %s""",
        (faculty_id,),
    )
    scheduled = fetch_all(
        """SELECT DISTINCT sb.subject_id, sb.subject_code, sb.subject_name
           FROM timetable t JOIN subjects sb ON sb.subject_id = t.subject_id
           WHERE sb.faculty_id = %s AND t.day_of_week = DAYNAME(CURDATE())""",
        (faculty_id,),
    )
    marked = fetch_all(
        """SELECT DISTINCT subject_id FROM attendance
           WHERE `date` = CURDATE() AND subject_id IN (SELECT subject_id FROM subjects WHERE faculty_id = %s)""",
        (faculty_id,),
    )
    marked_ids = {m["subject_id"] for m in marked}
    pending_attendance = [s for s in scheduled if s["subject_id"] not in marked_ids]
    missing_marks = fetch_all(
        """SELECT sb.subject_code, sb.subject_name, COUNT(*) AS students_without_internal_marks
           FROM subjects sb
           JOIN students st ON st.department_id = sb.department_id AND st.semester = sb.semester
           LEFT JOIN marks m ON m.student_id = st.student_id AND m.subject_id = sb.subject_id
                             AND m.exam_type = 'Internal'
           WHERE sb.faculty_id = %s AND m.mark_id IS NULL
           GROUP BY sb.subject_id, sb.subject_code, sb.subject_name""",
        (faculty_id,),
    )
    return {
        "subjects": subjects,
        "total_students": students["c"] if students else 0,
        "scheduled_today": scheduled,
        "marked_today": len(marked_ids),
        "pending_attendance": pending_attendance,
        "missing_marks": missing_marks,
    }


def student_stats(student_id):
    overall = overall_attendance(student_id=student_id)
    avg = fetch_one("SELECT ROUND(AVG(percentage), 2) AS pct FROM vw_marks_detail WHERE student_id = %s", (student_id,))
    return {
        "attendance": overall[0]["attendance_percentage"] if overall else None,
        "avg_marks": (avg or {}).get("pct"),
        "subjects": len(get_student_subjects(student_id)),
        "new_notices": count_recent_notices(7),
    }


def dept_student_counts():
    return fetch_all(
        """SELECT d.dept_code AS department, COUNT(s.student_id) AS students
           FROM departments d LEFT JOIN students s ON s.department_id = d.department_id
           GROUP BY d.department_id, d.dept_code ORDER BY d.dept_code"""
    )


def dept_attendance():
    return fetch_all(
        """SELECT dept_name AS department,
                  ROUND(100 * SUM(present_classes) / SUM(total_classes), 2) AS attendance
           FROM vw_attendance_summary GROUP BY dept_name ORDER BY dept_name"""
    )


def dept_avg_marks():
    return fetch_all(
        "SELECT dept_name AS department, ROUND(AVG(percentage), 2) AS average_marks FROM vw_marks_detail "
        "GROUP BY dept_name ORDER BY dept_name"
    )


def grade_distribution():
    return fetch_all(
        "SELECT grade, COUNT(*) AS students FROM vw_student_results GROUP BY grade ORDER BY grade"
    )


def table_counts():
    tables = ["users", "students", "faculty", "departments", "subjects", "attendance", "marks", "notices", "timetable"]
    # table names come from the fixed list above, never from user input
    return {t: fetch_one(f"SELECT COUNT(*) AS c FROM {t}")["c"] for t in tables}
