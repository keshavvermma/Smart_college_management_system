"""pages/settings.py - change password (everyone) + system information (admin)."""
import streamlit as st

from config import APP_TITLE, DB_CONFIG
from database import connection, queries
from utils import authentication as auth
from utils import ui
from utils.validators import validate_password


def render():
    user = auth.require_role("admin", "faculty", "student")
    ui.page_header("⚙️ Settings")

    st.subheader("🔑 Change password")
    with st.form("change_password_form", clear_on_submit=True):
        old = st.text_input("Current password", type="password")
        new = st.text_input("New password (min 8 characters, letters + digits)", type="password")
        again = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Change Password", type="primary")
    if submitted:
        errors = validate_password(new)
        if new != again:
            errors.append("The two new passwords do not match.")
        for e in errors:
            st.error(e)
        if not errors:
            ok, message = auth.change_password(user["user_id"], old, new)
            (st.success if ok else st.error)(message)

    st.divider()
    st.subheader("👤 Account")
    st.markdown(f"**Name:** {user['name']}  \n**Username:** {user['username']}  \n**Role:** {user['role'].title()}")

    if user["role"] == "admin":
        st.divider()
        st.subheader("🛠️ System status")
        ok, message = connection.test_connection()
        (st.success if ok else st.error)(f"Database: {message}")
        st.markdown(f"**Host:** {DB_CONFIG['host']}:{DB_CONFIG['port']}  \n**Database:** {DB_CONFIG['database']}  \n"
                    f"**User:** {DB_CONFIG['user']}")
        if ok:
            ui.show_table([{"Table": k, "Rows": v} for k, v in queries.table_counts().items()])
        st.caption(f"{APP_TITLE} - Power BI connects to the same MySQL database (see README).")
