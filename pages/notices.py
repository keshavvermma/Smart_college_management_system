"""
pages/notices.py - notice board.

  everyone : read published notices
  admin    : create / edit / delete / publish ANY notice
  faculty  : create notices, edit / delete / publish ONLY their own
"""
import mysql.connector
import streamlit as st

from config import NOTICE_PRIORITIES
from database import queries
from utils import authentication as auth
from utils import ui
from utils.validators import validate_notice


def render():
    user = auth.require_role("admin", "faculty", "student")
    ui.page_header("📢 Notices")
    ui.show_flash()

    if user["role"] == "student":
        _show_board(user)
        return

    tab_board, tab_create, tab_manage = st.tabs(["📋 Notice Board", "➕ Create Notice", "✏️ Edit / Delete / Publish"])
    with tab_board:
        _show_board(user)
    with tab_create:
        _create(user)
    with tab_manage:
        _manage(user)


def _show_board(user):
    notices = queries.get_notices(published_only=False)
    visible = [
        n for n in notices
        if n["is_published"] or user["role"] == "admin" or n["created_by"] == user["user_id"]
    ]
    if user["role"] == "student":
        visible = [n for n in visible if n["is_published"]]
    if not visible:
        st.info("No notices to show.")
    for notice in visible:
        ui.render_notice(notice, show_status=user["role"] != "student")


def _create(user):
    with st.form("create_notice_form", clear_on_submit=True):
        title = st.text_input("Title *")
        description = st.text_area("Description *", height=150)
        priority = st.selectbox("Priority", NOTICE_PRIORITIES)
        publish = st.checkbox("Publish now (students can see it)", value=True)
        submitted = st.form_submit_button("📣 Save Notice", type="primary")
    if submitted:
        data = {"title": title, "description": description, "priority": priority}
        errors = validate_notice(data)
        for e in errors:
            st.error(e)
        if not errors:
            saved = False
            try:
                queries.add_notice(title, description, priority, user["user_id"], publish)
                saved = True
            except mysql.connector.Error as err:
                st.error(ui.db_error_message(err))
            if saved:
                ui.flash("✅ Notice published." if publish else "✅ Notice saved as draft.")
                st.rerun()


def _manage(user):
    is_admin = user["role"] == "admin"
    notices = queries.get_notices(published_only=False, created_by=None if is_admin else user["user_id"])
    if not notices:
        st.info("You have no notices to manage.")
        return

    owner = None if is_admin else user["user_id"]  # enforced again inside queries.py
    options = {f"#{n['notice_id']} - {n['title']}": n for n in notices}
    notice = options[st.selectbox("Select notice", list(options), key="notice_pick")]
    nid = notice["notice_id"]

    with st.form(f"edit_notice_form_{nid}"):
        title = st.text_input("Title *", value=notice["title"], key=f"n_title_{nid}")
        description = st.text_area("Description *", value=notice["description"], height=150, key=f"n_desc_{nid}")
        priority = st.selectbox("Priority", NOTICE_PRIORITIES, index=NOTICE_PRIORITIES.index(notice["priority"]),
                                key=f"n_prio_{nid}")
        publish = st.checkbox("Published (visible to students)", value=bool(notice["is_published"]), key=f"n_pub_{nid}")
        update_clicked = st.form_submit_button("💾 Save Changes", type="primary")
    if update_clicked:
        errors = validate_notice({"title": title, "description": description, "priority": priority})
        for e in errors:
            st.error(e)
        if not errors:
            saved = False
            try:
                queries.update_notice(nid, title, description, priority, publish, owner)
                saved = True
            except PermissionError as err:
                st.error(str(err))
            except mysql.connector.Error as err:
                st.error(ui.db_error_message(err))
            if saved:
                ui.flash("✅ Notice updated.")
                st.rerun()

    st.divider()
    st.subheader("Delete notice")

    def _delete():
        try:
            queries.delete_notice(nid, owner)
        except PermissionError as err:
            st.error(str(err))
            return
        except mysql.connector.Error as err:
            st.error(ui.db_error_message(err))
            return
        ui.flash("🗑️ Notice deleted.")
        st.rerun()

    ui.confirm_delete(f"notice '{notice['title']}'", f"del_notice_{nid}", _delete)
