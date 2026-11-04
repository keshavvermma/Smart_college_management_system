"""pages/student_dashboard.py - dashboard and profile for a logged-in student.

The student_id ALWAYS comes from the login session (auth.current_student_id()),
never from a text box, so a student can only ever see their own information.
"""
import streamlit as st

from config import ATTENDANCE_THRESHOLD
from database import queries
from utils import authentication as auth
from utils import ui
from utils.calculations import is_attendance_low


def render():
    user = auth.require_role("student")
    student_id = auth.current_student_id()
    ui.page_header(f"🎓 Welcome, {user['name']}", "Student dashboard")

    stats = queries.student_stats(student_id)
    cols = st.columns(4)
    with cols[0]:
        ui.metric_card("Attendance", ui.pct(stats["attendance"], 0))
    with cols[1]:
        ui.metric_card("Average Marks", ui.pct(stats["avg_marks"], 0))
    with cols[2]:
        ui.metric_card("Subjects", stats["subjects"])
    with cols[3]:
        ui.metric_card("New Notices", stats["new_notices"], "Notices posted in the last 7 days")

    if stats["attendance"] is not None and is_attendance_low(stats["attendance"]):
        st.warning(f"⚠️ Your attendance is {stats['attendance']:.0f}% - below the required {ATTENDANCE_THRESHOLD:.0f}%.")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("📚 My subjects")
        ui.show_table(
            queries.get_student_subjects(student_id),
            {"subject_code": "Code", "subject_name": "Subject", "credits": "Credits", "faculty": "Faculty"},
        )
    with right:
        st.subheader("📢 Latest notices")
        notices = queries.get_notices(published_only=True, limit=3)
        if not notices:
            st.info("No notices yet.")
        for notice in notices:
            ui.render_notice(notice)

    st.caption("Use the sidebar to open My Profile, My Attendance, My Marks, My Timetable and Notices.")


def render_profile():
    auth.require_role("student")
    student = queries.get_student(auth.current_student_id())
    ui.page_header("👤 My Profile")
    if not student:
        st.error("Profile not found.")
        return
    with st.container(border=True):
        left, right = st.columns(2)
        with left:
            st.markdown(f"**Name:** {student['name']}")
            st.markdown(f"**Roll No:** {student['roll_no']}")
            st.markdown(f"**Gender:** {student['gender']}")
            st.markdown(f"**Date of Birth:** {student['date_of_birth']:%d %b %Y}")
            st.markdown(f"**Address:** {student['address'] or '-'}")
        with right:
            st.markdown(f"**Department:** {student['department']}")
            st.markdown(f"**Semester:** {student['semester']}")
            st.markdown(f"**Admission Year:** {student['admission_year']}")
            st.markdown(f"**Email:** {student['email']}")
            st.markdown(f"**Phone:** {student['phone']}")
    st.caption("To correct any detail, please contact the college office.")
