
import streamlit as st

st.set_page_config(page_title="Startup Diagnostic")

st.title("Smart College - Startup Diagnostic")
st.success("Streamlit server is running!")

modules = [
    "config",
    "pages.admin_dashboard",
    "pages.attendance",
    "pages.departments",
    "pages.faculty",
    "pages.faculty_dashboard",
    "pages.marks",
    "pages.notices",
    "pages.reports",
    "pages.settings",
    "pages.student_dashboard",
    "pages.students",
    "pages.subjects",
    "pages.timetable",
    "utils.authentication",
    "utils.ui",
]

import importlib

for module in modules:
    try:
        importlib.import_module(module)
        st.success(f"OK: {module}")
    except Exception as e:
        st.error(f"FAILED: {module}")
        st.exception(e)
