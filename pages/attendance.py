"""
pages/attendance.py - attendance for all three roles.

  faculty : mark attendance for THEIR subjects, view summaries of their subjects
  admin   : mark attendance for any subject, view college-wide summaries
  student : view ONLY their own attendance (student_id comes from the login session)
"""
from datetime import date

import mysql.connector
import pandas as pd
import streamlit as st

from config import ATTENDANCE_THRESHOLD, SEMESTERS
from database import queries
from utils import authentication as auth
from utils import ui
from utils.calculations import is_attendance_low


def render():
    user = auth.require_role("admin", "faculty", "student")
    if user["role"] == "student":
        _render_student()
    else:
        _render_staff()


# =====================================================================
# Faculty / Admin
# =====================================================================
def _render_staff():
    faculty_id = auth.current_faculty_id()  # None when the admin is logged in
    ui.page_header("📅 Attendance", "Mark attendance and track the 75% rule")
    ui.show_flash()
    tab_mark, tab_summary = st.tabs(["✅ Mark Attendance", "📈 Attendance Summary"])
    with tab_mark:
        _mark_attendance(faculty_id)
    with tab_summary:
        _summary(faculty_id)


def _mark_attendance(faculty_id):
    subjects = queries.get_subjects(faculty_id=faculty_id)
    if not subjects:
        st.info("No subjects are assigned to you yet. Ask the admin to assign subjects.")
        return

    subject = ui.pick_subject(subjects, "att")
    att_date = st.date_input("Date", value=date.today(), max_value=date.today(), key="att_date")

    students = queries.get_students_for_class(subject["department_id"], subject["semester"])
    if not students:
        st.warning("There are no students in this department and semester.")
        return

    existing = queries.get_attendance_for_date(subject["subject_id"], att_date)
    if existing:
        st.info("Attendance for this subject and date is already saved - you are editing it.")

    df = pd.DataFrame({
        "student_id": [s["student_id"] for s in students],
        "Roll No": [s["roll_no"] for s in students],
        "Name": [s["name"] for s in students],
        "Present": [existing.get(s["student_id"], "Present") == "Present" for s in students],
    })
    edited = st.data_editor(
        df,
        hide_index=True,
        disabled=["student_id", "Roll No", "Name"],
        column_config={
            "student_id": None,  # hide this column
            "Present": st.column_config.CheckboxColumn("Present", help="Untick = Absent", default=True),
        },
        key=f"att_editor_{subject['subject_id']}_{att_date}",
    )
    present = int(edited["Present"].sum())
    st.caption(f"Present: {present}   |   Absent: {len(edited) - present}   |   Total: {len(edited)}")

    if st.button("💾 Save Attendance", type="primary", key="att_save"):
        records = {
            int(sid): ("Present" if is_present else "Absent")
            for sid, is_present in zip(edited["student_id"], edited["Present"])
        }
        saved = False
        try:
            count = queries.save_attendance(subject["subject_id"], att_date, records, faculty_id)
            saved = True
        except PermissionError as err:
            st.error(str(err))
        except ValueError as err:
            st.error(str(err))
        except mysql.connector.Error as err:
            st.error(ui.db_error_message(err))
        if saved:
            ui.flash(f"✅ Attendance saved for {count} students ({subject['subject_code']}, {att_date:%d %b %Y}).")
            st.rerun()

    low = [r for r in queries.attendance_summary(subject_id=subject["subject_id"])
           if is_attendance_low(r["attendance_percentage"])]
    if low:
        st.warning(
            f"⚠️ {len(low)} student(s) are below {ATTENDANCE_THRESHOLD:.0f}% in {subject['subject_code']}:\n\n"
            + "\n".join(f"- **{r['student_name']}** ({r['roll_no']}) - {r['attendance_percentage']:.0f}%" for r in low)
        )


def _summary(faculty_id):
    dmap = ui.dept_map(queries.get_departments())
    c1, c2 = st.columns(2)
    dept_choice = c1.selectbox("Department", ["All"] + list(dmap), key="atts_dept")
    sem_choice = c2.selectbox("Semester", ["All"] + SEMESTERS, key="atts_sem")
    dept_id = dmap.get(dept_choice)
    semester = None if sem_choice == "All" else sem_choice

    st.subheader("Overall attendance per student")
    overall = queries.overall_attendance(dept_id, semester, faculty_id)
    if overall:
        df = pd.DataFrame(overall)
        df["Status"] = df["attendance_percentage"].apply(
            lambda p: "⚠️ Below 75%" if is_attendance_low(p) else "✅ OK")
        df = df[["roll_no", "student_name", "dept_name", "semester", "present_classes", "total_classes",
                 "attendance_percentage", "Status"]]
        df.columns = ["Roll No", "Student", "Department", "Sem", "Present", "Total Classes", "Attendance %", "Status"]
        st.dataframe(df, hide_index=True)
        low = [r for r in overall if is_attendance_low(r["attendance_percentage"])]
        if low:
            st.warning(
                f"⚠️ {len(low)} student(s) have attendance below {ATTENDANCE_THRESHOLD:.0f}%:\n\n"
                + "\n".join(f"- **{r['student_name']}** ({r['roll_no']}) - {r['attendance_percentage']:.0f}%" for r in low)
            )
    else:
        st.info("No attendance has been recorded yet.")

    st.subheader("Subject-wise attendance")
    rows = queries.attendance_summary(dept_id=dept_id, semester=semester, faculty_id=faculty_id)
    ui.show_table(
        rows,
        {"roll_no": "Roll No", "student_name": "Student", "subject_code": "Subject", "total_classes": "Classes",
         "present_classes": "Present", "attendance_percentage": "Attendance %", "attendance_status": "Status"},
    )


# =====================================================================
# Student (own data only)
# =====================================================================
def _render_student():
    student_id = auth.current_student_id()
    ui.page_header("📅 My Attendance")

    overall = queries.overall_attendance(student_id=student_id)
    if not overall:
        st.info("No attendance has been recorded for you yet.")
        return
    row = overall[0]
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card("Overall Attendance", ui.pct(row["attendance_percentage"]))
    with cols[1]:
        ui.metric_card("Classes Attended", int(row["present_classes"]))
    with cols[2]:
        ui.metric_card("Total Classes", int(row["total_classes"]))

    if is_attendance_low(row["attendance_percentage"]):
        st.warning(
            f"**Student:** {row['student_name']}  \n**Attendance:** {row['attendance_percentage']:.0f}%  \n"
            f"⚠️ Attendance below {ATTENDANCE_THRESHOLD:.0f}%"
        )
    else:
        st.success("✅ Your attendance is above the required 75%.")

    st.subheader("Subject-wise attendance")
    subjects = queries.attendance_summary(student_id=student_id)
    for s in subjects:
        pct_value = s["attendance_percentage"]
        flag = " ⚠️ below 75%" if is_attendance_low(pct_value) else ""
        st.progress(min(pct_value / 100.0, 1.0),
                    text=f"{s['subject_code']} - {s['subject_name']}: {pct_value:.0f}% "
                         f"({int(s['present_classes'])}/{int(s['total_classes'])}){flag}")

    st.subheader("Recent classes")
    ui.show_table(
        queries.attendance_history(student_id),
        {"date": "Date", "subject_code": "Code", "subject_name": "Subject", "status": "Status"},
    )
