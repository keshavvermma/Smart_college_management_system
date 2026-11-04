"""pages/admin_dashboard.py - overview cards and charts for the administrator."""
import pandas as pd
import streamlit as st

from database import queries
from utils import authentication as auth
from utils import ui


def render():
    user = auth.require_role("admin")
    ui.page_header("📊 Admin Dashboard", f"Welcome, {user['name']} - college overview")

    stats = queries.admin_stats()

    cols = st.columns(4)
    with cols[0]:
        ui.metric_card("Total Students", stats["students"])
    with cols[1]:
        ui.metric_card("Total Faculty", stats["faculty"])
    with cols[2]:
        ui.metric_card("Total Departments", stats["departments"])
    with cols[3]:
        ui.metric_card("Total Subjects", stats["subjects"])

    cols = st.columns(3)
    with cols[0]:
        ui.metric_card("Average Attendance", ui.pct(stats["avg_attendance"]))
    with cols[1]:
        ui.metric_card("Average Marks", ui.pct(stats["avg_marks"]))
    with cols[2]:
        ui.metric_card("Attendance below 75%", stats["low_attendance"], "Students whose overall attendance is under 75%")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Students per department")
        data = queries.dept_student_counts()
        if data:
            st.bar_chart(pd.DataFrame(data).set_index("department"))
    with right:
        st.subheader("Average attendance by department (%)")
        data = queries.dept_attendance()
        if data:
            st.bar_chart(pd.DataFrame(data).set_index("department"))
        else:
            st.info("No attendance recorded yet.")

    left, right = st.columns(2)
    with left:
        st.subheader("Average marks by department (%)")
        data = queries.dept_avg_marks()
        if data:
            st.bar_chart(pd.DataFrame(data).set_index("department"))
        else:
            st.info("No marks entered yet.")
    with right:
        st.subheader("Monthly attendance trend (%)")
        data = queries.attendance_monthly_trend()
        if data:
            st.line_chart(pd.DataFrame(data).set_index("month"))
        else:
            st.info("No attendance recorded yet.")

    st.divider()
    st.subheader("⚠️ Students with attendance below 75%")
    low = queries.low_attendance_students()
    ui.show_table(
        low,
        {"roll_no": "Roll No", "student_name": "Student", "dept_name": "Department", "semester": "Sem",
         "present_classes": "Present", "total_classes": "Total Classes", "attendance_percentage": "Attendance %"},
        empty_message="🎉 Every student has at least 75% attendance.",
    )

    st.subheader("📢 Latest notices")
    notices = queries.get_notices(published_only=True, limit=3)
    if not notices:
        st.info("No notices yet.")
    for notice in notices:
        ui.render_notice(notice)
