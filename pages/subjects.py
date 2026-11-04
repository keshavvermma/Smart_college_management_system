"""pages/subjects.py - subject management and faculty assignment (admin only)."""
import mysql.connector
import streamlit as st

from config import SEMESTERS
from database import queries
from utils import authentication as auth
from utils import ui
from utils.validators import validate_subject

LIST_COLUMNS = {
    "subject_code": "Code", "subject_name": "Subject", "department": "Department", "semester": "Sem",
    "credits": "Credits", "faculty": "Faculty",
}
UNASSIGNED = "— Unassigned —"


def _subject_form(prefix, dept_names, faculty_options, defaults=None):
    d = defaults or {}
    left, right = st.columns(2)
    with left:
        code = st.text_input("Subject code * (e.g. CS501)", value=d.get("subject_code", ""), key=f"{prefix}_code")
        name = st.text_input("Subject name *", value=d.get("subject_name", ""), key=f"{prefix}_name")
        credits = st.selectbox("Credits *", list(range(1, 7)), index=(d.get("credits", 3) - 1), key=f"{prefix}_credits")
    with right:
        dept_index = dept_names.index(d["department"]) if d.get("department") in dept_names else 0
        department = st.selectbox("Department *", dept_names, index=dept_index, key=f"{prefix}_dept")
        semester = st.selectbox("Semester *", SEMESTERS, index=SEMESTERS.index(d.get("semester", 1)), key=f"{prefix}_sem")
        fac_labels = list(faculty_options)
        fac_index = 0
        if d.get("faculty_id"):
            for i, label in enumerate(fac_labels):
                if faculty_options[label] == d["faculty_id"]:
                    fac_index = i
        faculty_label = st.selectbox("Assigned faculty", fac_labels, index=fac_index, key=f"{prefix}_fac")
    return {"subject_code": code, "subject_name": name, "credits": credits, "department": department,
            "semester": semester, "faculty_id": faculty_options[faculty_label]}


def render():
    auth.require_role("admin")
    ui.page_header("📚 Subject Management", "Create subjects and assign faculty")
    ui.show_flash()

    dmap = ui.dept_map(queries.get_departments())
    dept_names = list(dmap)
    if not dept_names:
        st.warning("Please add a department first (Departments page).")
        return

    faculty_options = {UNASSIGNED: None}
    for f in queries.get_faculty_list():
        faculty_options[f"{f['name']} ({f['department']})"] = f["faculty_id"]

    tab_list, tab_add, tab_edit = st.tabs(["📋 Subject List", "➕ Add Subject", "✏️ Edit / Delete / Assign"])

    with tab_list:
        c1, c2, c3 = st.columns([2, 1, 1])
        search = c1.text_input("🔍 Search by code or name", key="sub_search")
        dept_choice = c2.selectbox("Department", ["All"] + dept_names, key="sub_filter_dept")
        sem_choice = c3.selectbox("Semester", ["All"] + SEMESTERS, key="sub_filter_sem")
        subjects = queries.get_subjects(dmap.get(dept_choice), None if sem_choice == "All" else sem_choice, None, search)
        st.caption(f"{len(subjects)} subject(s) found")
        ui.show_table(subjects, LIST_COLUMNS)

    with tab_add:
        with st.form("add_subject_form"):
            data = _subject_form("add_sub", dept_names, faculty_options)
            submitted = st.form_submit_button("➕ Add Subject", type="primary")
        if submitted:
            data["department_id"] = dmap[data["department"]]
            errors = validate_subject(data)
            for e in errors:
                st.error(e)
            if not errors:
                saved = False
                try:
                    queries.add_subject(data)
                    saved = True
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                if saved:
                    ui.flash(f"✅ Subject {data['subject_code'].strip().upper()} added.")
                    st.rerun()

    with tab_edit:
        all_subjects = queries.get_subjects()
        if not all_subjects:
            st.info("No subjects to edit.")
        else:
            options = {f"{s['subject_code']} - {s['subject_name']}": s for s in all_subjects}
            subject = options[st.selectbox("Select subject", list(options), key="sub_edit_pick")]
            sid = subject["subject_id"]
            with st.form(f"edit_subject_form_{sid}"):
                data = _subject_form(f"edit_sub_{sid}", dept_names, faculty_options, subject)
                update_clicked = st.form_submit_button("💾 Save Changes", type="primary")
            if update_clicked:
                data["department_id"] = dmap[data["department"]]
                errors = validate_subject(data)
                for e in errors:
                    st.error(e)
                if not errors:
                    saved = False
                    try:
                        queries.update_subject(sid, data)
                        saved = True
                    except mysql.connector.Error as err:
                        st.error(ui.db_error_message(err))
                    if saved:
                        ui.flash(f"✅ Subject {data['subject_code'].strip().upper()} updated.")
                        st.rerun()

            st.divider()
            st.subheader("Delete subject")
            st.caption("Also deletes this subject's attendance, marks and timetable entries.")

            def _delete():
                try:
                    queries.delete_subject(sid)
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                    return
                ui.flash(f"🗑️ Subject {subject['subject_code']} deleted.")
                st.rerun()

            ui.confirm_delete(subject["subject_code"], f"del_sub_{sid}", _delete)
