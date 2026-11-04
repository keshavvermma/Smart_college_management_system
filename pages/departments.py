"""pages/departments.py - add, edit and delete departments (admin only)."""
import mysql.connector
import streamlit as st

from database import queries
from utils import authentication as auth
from utils import ui
from utils.validators import validate_department


def render():
    auth.require_role("admin")
    ui.page_header("🏛️ Department Management")
    ui.show_flash()

    departments = queries.get_departments()
    tab_list, tab_add, tab_edit = st.tabs(["📋 Departments", "➕ Add Department", "✏️ Edit / Delete"])

    with tab_list:
        ui.show_table(
            departments,
            {"dept_code": "Code", "dept_name": "Department", "students": "Students", "faculty": "Faculty",
             "subjects": "Subjects"},
        )

    with tab_add:
        with st.form("add_dept_form", clear_on_submit=True):
            name = st.text_input("Department name *")
            code = st.text_input("Short code * (e.g. CSE)")
            submitted = st.form_submit_button("➕ Add Department", type="primary")
        if submitted:
            data = {"dept_name": name, "dept_code": code}
            errors = validate_department(data)
            for e in errors:
                st.error(e)
            if not errors:
                saved = False
                try:
                    queries.add_department(name, code)
                    saved = True
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                if saved:
                    ui.flash(f"✅ Department '{name.strip()}' added.")
                    st.rerun()

    with tab_edit:
        if not departments:
            st.info("No departments yet.")
        else:
            options = {d["dept_name"]: d for d in departments}
            dept = options[st.selectbox("Select department", list(options), key="dept_edit_pick")]
            dept_id = dept["department_id"]
            with st.form(f"edit_dept_form_{dept_id}"):
                name = st.text_input("Department name *", value=dept["dept_name"], key=f"dept_name_{dept_id}")
                code = st.text_input("Short code *", value=dept["dept_code"], key=f"dept_code_{dept_id}")
                update_clicked = st.form_submit_button("💾 Save Changes", type="primary")
            if update_clicked:
                errors = validate_department({"dept_name": name, "dept_code": code})
                for e in errors:
                    st.error(e)
                if not errors:
                    saved = False
                    try:
                        queries.update_department(dept_id, name, code)
                        saved = True
                    except mysql.connector.Error as err:
                        st.error(ui.db_error_message(err))
                    if saved:
                        ui.flash("✅ Department updated.")
                        st.rerun()

            st.divider()
            st.subheader("Delete department")
            if dept["students"] or dept["faculty"] or dept["subjects"]:
                st.warning(
                    f"{dept['dept_name']} still has {dept['students']} student(s), {dept['faculty']} faculty and "
                    f"{dept['subjects']} subject(s). Move or delete them first - otherwise the database will refuse."
                )

            def _delete():
                try:
                    queries.delete_department(dept_id)
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                    return
                ui.flash(f"🗑️ Department '{dept['dept_name']}' deleted.")
                st.rerun()

            ui.confirm_delete(dept["dept_name"], f"del_dept_{dept_id}", _delete)
