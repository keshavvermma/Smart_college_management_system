"""
utils/authentication.py - login, logout, sessions and role-based access control.

The logged-in user is kept in st.session_state["user"] as a small dictionary:
    {"user_id": 3, "username": "...", "role": "admin|faculty|student", "ref_id": 5, "name": "..."}

Security rules used across the project:
  * Passwords are stored only as salted PBKDF2 hashes (see utils/security.py).
  * Students NEVER choose which student_id to look at - it always comes from the session
    (current_student_id()), so one student can never open another student's data.
  * Faculty ownership of subjects is re-checked inside database/queries.py when saving.
"""
import time

import streamlit as st

import config
from database import queries
from utils.security import hash_password, verify_password  # re-exported for convenience

MAX_FAILED_ATTEMPTS = config.MAX_LOGIN_ATTEMPTS


def login(username, password):
    """Check credentials. Returns (success, message)."""
    wait = int(st.session_state.get("locked_until", 0) - time.time())
    if wait > 0:
        return False, f"Too many failed attempts. Try again in {wait} seconds."

    username = (username or "").strip().lower()
    if not username or not password:
        return False, "Enter both username and password."

    user = queries.get_user_by_username(username)
    if user is None or not verify_password(password, user["password_hash"]):
        failed = st.session_state.get("failed_logins", 0) + 1
        st.session_state["failed_logins"] = failed
        if failed >= MAX_FAILED_ATTEMPTS:  # short lock-out (per browser session)
            st.session_state["locked_until"] = time.time() + config.LOCKOUT_SECONDS
            st.session_state["failed_logins"] = 0
        return False, "Invalid username or password."

    st.session_state["failed_logins"] = 0
    st.session_state["last_active"] = time.time()
    st.session_state["user"] = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "ref_id": user["ref_id"],
        "name": queries.get_display_name(user["role"], user["ref_id"]),
    }
    return True, "Login successful."


def logout():
    """Clear everything stored for this browser session."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def check_session_timeout():
    """Log the user out after SESSION_TIMEOUT_MINUTES without activity.
    Call once at the top of every script run. Returns True if the session expired."""
    if st.session_state.get("user") is None:
        return False
    now = time.time()
    if now - st.session_state.get("last_active", now) > config.SESSION_TIMEOUT_MINUTES * 60:
        logout()
        st.session_state["flash_login"] = "Your session expired. Please log in again."
        return True
    st.session_state["last_active"] = now
    return False


def current_user():
    return st.session_state.get("user")


def require_role(*roles):
    """Call at the top of every page. Stops the page if the user may not see it."""
    user = current_user()
    if user is None:
        st.error("Please log in first.")
        st.stop()
    if user["role"] not in roles:
        st.error("🚫 You do not have permission to open this page.")
        st.stop()
    return user


def current_student_id():
    """The student_id of the logged-in student (None for other roles)."""
    user = current_user()
    return user["ref_id"] if user and user["role"] == "student" else None


def current_faculty_id():
    """The faculty_id of the logged-in faculty member (None for other roles)."""
    user = current_user()
    return user["ref_id"] if user and user["role"] == "faculty" else None


def change_password(user_id, old_password, new_password):
    """Returns (success, message). Verifies the old password first."""
    user = queries.get_user_by_id(user_id)
    if user is None or not verify_password(old_password, user["password_hash"]):
        return False, "Current password is incorrect."
    queries.update_password(user_id, hash_password(new_password))
    return True, "Password changed successfully."
