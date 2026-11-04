"""
pages/timetable.py - class timetable.

  student : the timetable of their own department and semester
  faculty : all periods of the subjects they teach
  admin   : view and manage the timetable of any department / semester
"""
from datetime import time

import mysql.connector
import pandas as pd
import streamlit as st

from config import DAYS, SEMESTERS
from database import queries
from utils import authentication as auth
from utils import ui


def render():
    user = auth.require_role("admin", "faculty", "student")
    ui.page_header("🗓️ Timetable")
    ui.show_flash()
    if user["role"] == "student":
        _render_student()
    elif user["role"] == "faculty":
        _render_faculty()
    else:
        _render_admin()


def _grid(rows):
    """Show rows as a weekly grid: time slots down the side, days across the top."""
    if not rows:
        st.info("No timetable entries yet.")
        return
    df = pd.DataFrame(rows)
    df["Time"] = df["start_time"] + " - " + df["end_time"]
    grid = df.pivot_table(index="Time", columns="day_of_week", values="subject_code",
                          aggfunc=lambda items: ", ".join(items)).fillna("")
    grid = grid[[d for d in DAYS if d in grid.columns]]
    st.dataframe(grid)


def _render_student():
    student = queries.get_student(auth.current_student_id())
    if not student:
        st.error("Student record not found.")
        return
    st.caption(f"{student['department']} - Semester {student['semester']}")
    rows = queries.get_timetable(student["department_id"], student["semester"])
    _grid(rows)
    if rows:
        st.subheader("Period details")
        ui.show_table(rows, {"day_of_week": "Day", "start_time": "From", "end_time": "To", "subject_code": "Code",
                             "subject_name": "Subject", "faculty": "Faculty", "room": "Room"})


def _render_faculty():
    rows = queries.get_faculty_timetable(auth.current_faculty_id())
    if rows:
        for r in rows:
            r["subject_code"] = f"{r['subject_code']} ({r['dept_code']}-S{r['semester']})"
    _grid(rows)
    if rows:
        st.subheader("Period details")
        ui.show_table(rows, {"day_of_week": "Day", "start_time": "From", "end_time": "To",
                             "subject_code": "Subject", "room": "Room"})


def _render_admin():
    departments = queries.get_departments()
    dmap = ui.dept_map(departments)
    if not dmap:
        st.warning("Add a department first.")
        return
    c1, c2 = st.columns(2)
    dept_name = c1.selectbox("Department", list(dmap), key="tt_dept")
    semester = c2.selectbox("Semester", SEMESTERS, index=2, key="tt_sem")
    dept_id = dmap[dept_name]

    rows = queries.get_timetable(dept_id, semester)
    _grid(rows)

    tab_add, tab_delete = st.tabs(["➕ Add Period", "🗑️ Delete Period"])
    with tab_add:
        subjects = queries.get_subjects(dept_id=dept_id, semester=semester)
        if not subjects:
            st.info("This department and semester has no subjects yet. Add subjects first.")
        else:
            options = {f"{s['subject_code']} - {s['subject_name']}": s["subject_id"] for s in subjects}
            with st.form("add_period_form"):
                subject_label = st.selectbox("Subject", list(options))
                day = st.selectbox("Day", DAYS)
                c1, c2, c3 = st.columns(3)
                start = c1.time_input("Start time", value=time(9, 0))
                end = c2.time_input("End time", value=time(10, 0))
                room = c3.text_input("Room", value="Room 101")
                submitted = st.form_submit_button("➕ Add Period", type="primary")
            if submitted:
                if end <= start:
                    st.error("End time must be after start time.")
                elif queries.timetable_conflict(dept_id, semester, day, start.strftime("%H:%M:%S"),
                                                end.strftime("%H:%M:%S")):
                    st.error("Clash: this class already has a period overlapping that time on that day.")
                else:
                    saved = False
                    try:
                        queries.add_timetable_entry(dept_id, semester, options[subject_label], day,
                                                    start.strftime("%H:%M:%S"), end.strftime("%H:%M:%S"),
                                                    room.strip() or None)
                        saved = True
                    except mysql.connector.Error as err:
                        st.error(ui.db_error_message(err))
                    if saved:
                        ui.flash("✅ Period added.")
                        st.rerun()

    with tab_delete:
        if not rows:
            st.info("Nothing to delete.")
        else:
            options = {f"{r['day_of_week']} {r['start_time']}-{r['end_time']} | {r['subject_code']}": r["timetable_id"]
                       for r in rows}
            label = st.selectbox("Select period", list(options), key="tt_del_pick")
            tid = options[label]

            def _delete():
                try:
                    queries.delete_timetable_entry(tid)
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                    return
                ui.flash("🗑️ Period deleted.")
                st.rerun()

            ui.confirm_delete("this period", f"del_tt_{tid}", _delete)
