"""
app.py - the entry point.   Run with:   streamlit run app.py

What it does:
  1. shows the login page when nobody is logged in
  2. after login, builds a sidebar menu that depends on the user's role
  3. adds a Logout button

st.navigation() is used instead of Streamlit's automatic "pages/" menu, so a page
is only reachable if it is in the menu of the logged-in role.
"""
import streamlit as st

from config import APP_TITLE, COLLEGE_NAME, LOGO_PATH

st.set_page_config(page_title=APP_TITLE, page_icon="🎓", layout="wide")

from pages import (admin_dashboard, attendance, departments, faculty, faculty_dashboard, marks, notices,  # noqa: E402
                   reports, settings, student_dashboard, students, subjects, timetable)
from utils import authentication as auth  # noqa: E402
from utils import ui  # noqa: E402

ui.inject_css()


def login_page():
    left, middle, right = st.columns([1, 2, 1])
    with middle:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=90)
        st.title(f"🎓 {COLLEGE_NAME}")
        st.caption(APP_TITLE)
        if st.session_state.get("flash_login"):
            st.warning(st.session_state.pop("flash_login"))
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Login", type="primary")
        if submitted:
            try:
                ok, message = auth.login(username, password)
            except Exception as err:  # most often: MySQL is not running or .env is wrong
                st.error(f"Cannot reach the database. Check MySQL and your .env file.\n\nDetails: {err}")
                return
            if ok:
                st.rerun()
            else:
                st.error(message)


def pages_for(role):
    """Sidebar menu for each role."""
    if role == "admin":
        return [
            st.Page(admin_dashboard.render, title="Dashboard", icon="📊", url_path="dashboard", default=True),
            st.Page(students.render, title="Students", icon="🎓", url_path="students"),
            st.Page(faculty.render, title="Faculty", icon="👨‍🏫", url_path="faculty"),
            st.Page(departments.render, title="Departments", icon="🏛️", url_path="departments"),
            st.Page(subjects.render, title="Subjects", icon="📚", url_path="subjects"),
            st.Page(timetable.render, title="Timetable", icon="🗓️", url_path="timetable"),
            st.Page(attendance.render, title="Attendance", icon="📅", url_path="attendance"),
            st.Page(marks.render, title="Marks", icon="📝", url_path="marks"),
            st.Page(notices.render, title="Notices", icon="📢", url_path="notices"),
            st.Page(reports.render, title="Reports", icon="📑", url_path="reports"),
            st.Page(settings.render, title="Settings", icon="⚙️", url_path="settings"),
        ]
    if role == "faculty":
        return [
            st.Page(faculty_dashboard.render, title="Dashboard", icon="📊", url_path="dashboard", default=True),
            st.Page(attendance.render, title="Attendance", icon="📅", url_path="attendance"),
            st.Page(marks.render, title="Marks", icon="📝", url_path="marks"),
            st.Page(timetable.render, title="My Timetable", icon="🗓️", url_path="timetable"),
            st.Page(notices.render, title="Notices", icon="📢", url_path="notices"),
            st.Page(settings.render, title="Settings", icon="⚙️", url_path="settings"),
        ]
    return [  # student
        st.Page(student_dashboard.render, title="Dashboard", icon="📊", url_path="dashboard", default=True),
        st.Page(student_dashboard.render_profile, title="My Profile", icon="👤", url_path="profile"),
        st.Page(attendance.render, title="My Attendance", icon="📅", url_path="attendance"),
        st.Page(marks.render, title="My Marks", icon="📝", url_path="marks"),
        st.Page(timetable.render, title="My Timetable", icon="🗓️", url_path="timetable"),
        st.Page(notices.render, title="Notices", icon="📢", url_path="notices"),
        st.Page(settings.render, title="Settings", icon="⚙️", url_path="settings"),
    ]


def main():
    auth.check_session_timeout()
    user = auth.current_user()
    if user is None:
        page = st.navigation([st.Page(login_page, title="Login", icon="🔐", url_path="login")])
        page.run()
        return

    if LOGO_PATH.exists():
        try:
            st.logo(str(LOGO_PATH))
        except AttributeError:  # very old Streamlit without st.logo
            pass

    page = st.navigation(pages_for(user["role"]))
    with st.sidebar:
        st.divider()
        st.markdown(f"**{user['name']}**  \n:gray[{user['role'].title()}]")
        if st.button("🚪 Logout", key="logout_btn"):
            auth.logout()
            st.rerun()
    page.run()


main()
