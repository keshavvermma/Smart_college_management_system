"""pages/faculty.py - faculty management (admin only): list/search, add, edit, delete, assign subjects."""
from datetime import date

import mysql.connector
import streamlit as st

from config import DEFAULT_FACULTY_PASSWORD, DESIGNATIONS
from database import queries
from utils import authentication as auth
from utils import ui
from utils.validators import validate_faculty

LIST_COLUMNS = {
    "name": "Name", "designation": "Designation", "department": "Department", "email": "Email",
    "phone": "Phone", "joining_date": "Joining Date", "subjects": "Subjects",
}


def _faculty_form(prefix, dept_names, defaults=None):
    d = defaults or {}
    left, right = st.columns(2)
    with left:
        name = st.text_input("Full name *", value=d.get("name", ""), key=f"{prefix}_name")
        email = st.text_input("Email *", value=d.get("email", ""), key=f"{prefix}_email")
        phone = st.text_input("Phone (10 digits) *", value=d.get("phone", ""), key=f"{prefix}_phone")
    with right:
        dept_index = dept_names.index(d["department"]) if d.get("department") in dept_names else 0
        department = st.selectbox("Department *", dept_names, index=dept_index, key=f"{prefix}_dept")
        options = list(DESIGNATIONS)
        if d.get("designation") and d["designation"] not in options:
            options.append(d["designation"])
        designation = st.selectbox("Designation *", options,
                                   index=options.index(d["designation"]) if d.get("designation") else 0,
                                   key=f"{prefix}_desig")
        joining = st.date_input("Joining date *", value=d.get("joining_date", date.today()),
                                min_value=date(1980, 1, 1), max_value=date.today(), key=f"{prefix}_join")
    return {"name": name, "email": email, "phone": phone, "department": department,
            "designation": designation, "joining_date": joining}


def render():
    auth.require_role("admin")
    ui.page_header("👨‍🏫 Faculty Management", "Add faculty, assign departments and subjects")
    ui.show_flash()

    dmap = ui.dept_map(queries.get_departments())
    dept_names = list(dmap)
    if not dept_names:
        st.warning("Please add a department first (Departments page).")
        return

    tab_list, tab_add, tab_edit, tab_assign = st.tabs(
        ["📋 Faculty List", "➕ Add Faculty", "✏️ Edit / Delete", "📚 Assign Subjects"]
    )

    with tab_list:
        c1, c2 = st.columns([2, 1])
        search = c1.text_input("🔍 Search by name, email or designation", key="fac_search")
        dept_choice = c2.selectbox("Department", ["All"] + dept_names, key="fac_filter_dept")
        faculty = queries.get_faculty_list(search, dmap.get(dept_choice))
        st.caption(f"{len(faculty)} faculty member(s) found")
        ui.show_table(faculty, LIST_COLUMNS)

    with tab_add:
        with st.form("add_faculty_form"):
            data = _faculty_form("add_fac", dept_names)
            submitted = st.form_submit_button("➕ Add Faculty", type="primary")
        if submitted:
            data["department_id"] = dmap[data["department"]]
            errors = validate_faculty(data)
            for e in errors:
                st.error(e)
            if not errors:
                saved = False
                try:
                    queries.add_faculty(data)
                    saved = True
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                if saved:
                    username = data["email"].strip().lower().split("@")[0]
                    ui.flash(f"✅ {data['name']} added. Login username: {username} / password: {DEFAULT_FACULTY_PASSWORD}")
                    st.rerun()

    with tab_edit:
        all_faculty = queries.get_faculty_list()
        if not all_faculty:
            st.info("No faculty to edit.")
        else:
            options = {f"{f['name']} ({f['department']})": f["faculty_id"] for f in all_faculty}
            faculty_id = options[st.selectbox("Select faculty member", list(options), key="fac_edit_pick")]
            member = queries.get_faculty(faculty_id)
            with st.form(f"edit_faculty_form_{faculty_id}"):
                data = _faculty_form(f"edit_fac_{faculty_id}", dept_names, member)
                saved_clicked = st.form_submit_button("💾 Save Changes", type="primary")
            if saved_clicked:
                data["department_id"] = dmap[data["department"]]
                errors = validate_faculty(data)
                for e in errors:
                    st.error(e)
                if not errors:
                    saved = False
                    try:
                        queries.update_faculty(faculty_id, data)
                        saved = True
                    except mysql.connector.Error as err:
                        st.error(ui.db_error_message(err))
                    if saved:
                        ui.flash(f"✅ {data['name']} updated.")
                        st.rerun()

            st.divider()
            st.subheader("Delete faculty")
            st.caption("The login account is removed and the faculty member's subjects become 'Unassigned'.")

            def _delete():
                try:
                    queries.delete_faculty(faculty_id)
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                    return
                ui.flash(f"🗑️ {member['name']} deleted.")
                st.rerun()

            ui.confirm_delete(member["name"], f"del_fac_{faculty_id}", _delete)

    with tab_assign:
        all_faculty = queries.get_faculty_list()
        subjects = queries.get_subjects()
        if not all_faculty or not subjects:
            st.info("You need at least one faculty member and one subject.")
        else:
            options = {f"{f['name']} ({f['department']})": f["faculty_id"] for f in all_faculty}
            faculty_id = options[st.selectbox("Faculty member", list(options), key="fac_assign_pick")]
            labels = {s["subject_id"]: f"{s['subject_code']} - {s['subject_name']} ({s['department']}, Sem {s['semester']})"
                      for s in subjects}
            current = [labels[s["subject_id"]] for s in subjects if s["faculty_id"] == faculty_id]
            chosen = st.multiselect("Subjects taught by this faculty member", list(labels.values()),
                                    default=current, key=f"fac_assign_subjects_{faculty_id}")
            st.caption("A subject has one teacher. Selecting a subject that belongs to someone else moves it to this faculty member.")
            if st.button("💾 Save Assignment", type="primary", key="fac_assign_save"):
                chosen_ids = [sid for sid, label in labels.items() if label in chosen]
                saved = False
                try:
                    queries.set_faculty_subjects(faculty_id, chosen_ids)
                    saved = True
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                if saved:
                    ui.flash("✅ Subject assignment saved.")
                    st.rerun()
