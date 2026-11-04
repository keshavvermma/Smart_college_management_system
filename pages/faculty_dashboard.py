"""pages/faculty_dashboard.py - dashboard for a logged-in faculty member."""
import streamlit as st

from database import queries
from utils import authentication as auth
from utils import ui


def render():
    user = auth.require_role("faculty")
    faculty_id = auth.current_faculty_id()
    ui.page_header(f"👨‍🏫 Welcome, {user['name']}", "Faculty dashboard")

    stats = queries.faculty_stats(faculty_id)
    scheduled = len(stats["scheduled_today"])
    pending_count = len(stats["pending_attendance"]) + len(stats["missing_marks"])

    cols = st.columns(4)
    with cols[0]:
        ui.metric_card("Assigned Subjects", len(stats["subjects"]))
    with cols[1]:
        ui.metric_card("Total Students", stats["total_students"])
    with cols[2]:
        ui.metric_card("Today's Attendance", f"{stats['marked_today']} marked", f"{scheduled} class(es) scheduled today")
    with cols[3]:
        ui.metric_card("Pending Tasks", pending_count)

    st.divider()
    st.subheader("📚 My subjects")
    ui.show_table(
        stats["subjects"],
        {"subject_code": "Code", "subject_name": "Subject", "department": "Department", "semester": "Sem",
         "credits": "Credits"},
        empty_message="No subjects are assigned to you yet. Ask the admin to assign subjects.",
    )

    st.subheader("📝 Pending tasks")
    if not pending_count:
        st.success("You are all caught up!")
    for subject in stats["pending_attendance"]:
        st.warning(f"Attendance not yet marked today for {subject['subject_code']} - {subject['subject_name']}")
    for row in stats["missing_marks"]:
        st.info(
            f"{row['subject_code']} - {row['subject_name']}: Internal marks pending for "
            f"{row['students_without_internal_marks']} student(s)"
        )

    st.subheader("📢 Recent notices")
    notices = queries.get_notices(published_only=True, limit=3)
    if not notices:
        st.info("No notices yet.")
    for notice in notices:
        ui.render_notice(notice)
