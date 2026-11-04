"""pages/students.py - student management (admin only): list/search/filter, add, edit, delete."""
from datetime import date

import mysql.connector
import streamlit as st

from config import DEFAULT_STUDENT_PASSWORD, GENDERS, SEMESTERS
from database import queries
from utils import authentication as auth
from utils import ui
from utils.validators import validate_student

LIST_COLUMNS = {
    "roll_no": "Roll No", "name": "Name", "gender": "Gender", "department": "Department",
    "semester": "Sem", "email": "Email", "phone": "Phone", "admission_year": "Admission Year",
}


def _student_form(prefix, dept_names, defaults=None):
    """Draw the student input widgets and return what the user typed as a dictionary."""
    d = defaults or {}
    left, right = st.columns(2)
    with left:
        roll_no = st.text_input("Roll number *", value=d.get("roll_no", ""), key=f"{prefix}_roll")
        name = st.text_input("Full name *", value=d.get("name", ""), key=f"{prefix}_name")
        gender = st.selectbox("Gender *", GENDERS, index=GENDERS.index(d["gender"]) if d.get("gender") in GENDERS else 0,
                              key=f"{prefix}_gender")
        dob = st.date_input("Date of birth *", value=d.get("date_of_birth", date(2005, 1, 1)),
                            min_value=date(1980, 1, 1), max_value=date.today(), key=f"{prefix}_dob")
        address = st.text_area("Address", value=d.get("address") or "", key=f"{prefix}_address")
    with right:
        dept_index = dept_names.index(d["department"]) if d.get("department") in dept_names else 0
        department = st.selectbox("Department *", dept_names, index=dept_index, key=f"{prefix}_dept")
        semester = st.selectbox("Semester *", SEMESTERS, index=SEMESTERS.index(d.get("semester", 1)),
                                key=f"{prefix}_sem")
        email = st.text_input("Email *", value=d.get("email", ""), key=f"{prefix}_email")
        phone = st.text_input("Phone (10 digits) *", value=d.get("phone", ""), key=f"{prefix}_phone")
        admission_year = st.number_input("Admission year *", min_value=2000, max_value=date.today().year, step=1,
                                         value=int(d.get("admission_year", date.today().year)), key=f"{prefix}_year")
    return {
        "roll_no": roll_no, "name": name, "gender": gender, "date_of_birth": dob, "address": address,
        "department": department, "semester": semester, "email": email, "phone": phone,
        "admission_year": int(admission_year),
    }


def render():
    auth.require_role("admin")
    ui.page_header("🎓 Student Management", "Add, search, update and remove students")
    ui.show_flash()

    departments = queries.get_departments()
    dmap = ui.dept_map(departments)
    dept_names = list(dmap)
    if not dept_names:
        st.warning("Please add a department first (Departments page).")
        return

    tab_list, tab_add, tab_edit = st.tabs(["📋 Student List", "➕ Add Student", "✏️ Edit / Delete"])

    # ------------------------------------------------------------ list + search
    with tab_list:
        c1, c2, c3 = st.columns([2, 1, 1])
        search = c1.text_input("🔍 Search by name, roll number or email", key="stu_search")
        dept_choice = c2.selectbox("Department", ["All"] + dept_names, key="stu_filter_dept")
        sem_choice = c3.selectbox("Semester", ["All"] + SEMESTERS, key="stu_filter_sem")
        students = queries.search_students(
            search, dmap.get(dept_choice), None if sem_choice == "All" else sem_choice
        )
        st.caption(f"{len(students)} student(s) found")
        ui.show_table(students, LIST_COLUMNS)

        if students:
            st.subheader("Student details")
            options = {f"{s['roll_no']} - {s['name']}": s for s in students}
            chosen = options[st.selectbox("Select a student to view full details", list(options), key="stu_detail")]
            with st.container(border=True):
                a, b = st.columns(2)
                a.markdown(f"**Roll No:** {chosen['roll_no']}  \n**Name:** {chosen['name']}  \n"
                           f"**Gender:** {chosen['gender']}  \n**Date of birth:** {chosen['date_of_birth']:%d %b %Y}  \n"
                           f"**Address:** {chosen['address'] or '-'}")
                b.markdown(f"**Department:** {chosen['department']}  \n**Semester:** {chosen['semester']}  \n"
                           f"**Admission year:** {chosen['admission_year']}  \n**Email:** {chosen['email']}  \n"
                           f"**Phone:** {chosen['phone']}")

    # ------------------------------------------------------------ add
    with tab_add:
        with st.form("add_student_form", clear_on_submit=False):
            data = _student_form("add_stu", dept_names)
            submitted = st.form_submit_button("➕ Add Student", type="primary")
        if submitted:
            data["department_id"] = dmap[data["department"]]
            errors = validate_student(data)
            for e in errors:
                st.error(e)
            if not errors:
                saved = False
                try:
                    queries.add_student(data)
                    saved = True
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                if saved:
                    ui.flash(f"✅ Student {data['name']} added. Login username: {data['roll_no'].lower()} / "
                             f"password: {DEFAULT_STUDENT_PASSWORD}")
                    st.rerun()

    # ------------------------------------------------------------ edit / delete
    with tab_edit:
        all_students = queries.search_students()
        if not all_students:
            st.info("No students to edit.")
        else:
            options = {f"{s['roll_no']} - {s['name']}": s["student_id"] for s in all_students}
            label = st.selectbox("Select student", list(options), key="stu_edit_pick")
            student_id = options[label]
            student = queries.get_student(student_id)

            with st.form(f"edit_student_form_{student_id}"):
                data = _student_form(f"edit_stu_{student_id}", dept_names, student)
                update_clicked = st.form_submit_button("💾 Save Changes", type="primary")
            if update_clicked:
                data["department_id"] = dmap[data["department"]]
                errors = validate_student(data)
                for e in errors:
                    st.error(e)
                if not errors:
                    saved = False
                    try:
                        queries.update_student(student_id, data)
                        saved = True
                    except mysql.connector.Error as err:
                        st.error(ui.db_error_message(err))
                    if saved:
                        ui.flash(f"✅ Student {data['name']} updated.")
                        st.rerun()

            st.divider()
            st.subheader("Delete student")
            st.caption("Deleting also removes the student's login, attendance and marks.")

            def _delete():
                try:
                    queries.delete_student(student_id)
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                    return
                ui.flash(f"🗑️ Student {student['name']} deleted.")
                st.rerun()

            ui.confirm_delete(f"{student['name']} ({student['roll_no']})", f"del_stu_{student_id}", _delete)
