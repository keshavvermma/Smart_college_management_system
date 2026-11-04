"""
utils/ui.py - small reusable Streamlit helpers so every page looks consistent.
"""
import pandas as pd
import streamlit as st

CSS = """
<style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {color: #1E3A8A; font-weight: 700;}
    h2, h3 {color: #1E3A8A;}
    [data-testid="stMetricValue"] {color: #1E3A8A; font-weight: 700;}
    [data-testid="stSidebar"] {border-right: 1px solid #E2E8F0;}
    .notice-card {border-left: 6px solid #94A3B8; background: #F8FAFC; padding: 0.7rem 1rem;
                  border-radius: 6px; margin-bottom: 0.7rem; color: #0F172A;}
    .notice-Urgent {border-left-color: #DC2626; background: #FEF2F2;}
    .notice-Important {border-left-color: #F59E0B; background: #FFFBEB;}
    .notice-Normal {border-left-color: #2563EB; background: #EFF6FF;}
    .notice-card small {color: #475569;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title, subtitle=""):
    st.title(title)
    if subtitle:
        st.caption(subtitle)


# ---- messages that survive st.rerun() ---------------------------------
def flash(message, kind="success"):
    """Remember a message and show it after the next rerun. kind: success|error|warning|info"""
    st.session_state["_flash"] = (kind, message)


def show_flash():
    item = st.session_state.pop("_flash", None)
    if item:
        kind, message = item
        getattr(st, kind)(message)


# ---- widgets ------------------------------------------------------------
def metric_card(label, value, help_text=None):
    with st.container(border=True):
        st.metric(label, value, help=help_text)


def to_dataframe(rows):
    return rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)


def show_table(rows, columns=None, empty_message="No records found."):
    """
    Show a list of dicts (or a DataFrame) as a table.
    columns = {"db_column": "Nice Label", ...} chooses, orders and renames the columns.
    Returns the DataFrame that was displayed (handy for CSV download).
    """
    df = to_dataframe(rows)
    if df.empty:
        st.info(empty_message)
        return df
    if columns:
        df = df[list(columns)].rename(columns=columns)
    st.dataframe(df, hide_index=True)
    return df


def db_error_message(err):
    """Turn a MySQL error into a message a student can understand."""
    errno = getattr(err, "errno", None)
    if errno == 1062:
        return "That value already exists (roll number, email, code, username or name must be unique)."
    if errno in (1451, 1217):
        return "Cannot delete: other records (students, faculty, subjects...) still depend on this item."
    if errno == 1452:
        return "Invalid reference: the selected department / subject / faculty does not exist."
    return f"Database error: {err}"


def pct(value, digits=1):
    """Format a percentage or show a dash when there is no data."""
    return "-" if value is None else f"{value:.{digits}f}%"


def render_notice(notice, show_status=False):
    """Draw one notice as a coloured card."""
    created = notice["created_at"]
    stamp = created.strftime("%d %b %Y, %I:%M %p") if hasattr(created, "strftime") else str(created)
    draft = " &nbsp;·&nbsp; <b>DRAFT (not visible to students)</b>" if show_status and not notice["is_published"] else ""
    title = _escape(notice["title"])
    body = _escape(notice["description"]).replace("\n", "<br>")
    st.markdown(
        f"""<div class="notice-card notice-{notice['priority']}">
        <b>{title}</b> &nbsp;<small>[{notice['priority']}]</small><br>
        {body}<br>
        <small>Posted by {_escape(notice['author'])} · {stamp}{draft}</small></div>""",
        unsafe_allow_html=True,
    )


def _escape(text):
    """Escape HTML so notice text typed by users cannot inject markup."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def pick_subject(subjects, key_prefix):
    """
    Three linked dropdowns: Department -> Semester -> Subject.
    `subjects` is a list from queries.get_subjects(). Returns the chosen subject dict.
    """
    dept_names = sorted({s["department"] for s in subjects})
    cols = st.columns(3)
    dept = cols[0].selectbox("Department", dept_names, key=f"{key_prefix}_dept")
    semesters = sorted({s["semester"] for s in subjects if s["department"] == dept})
    sem = cols[1].selectbox("Semester", semesters, key=f"{key_prefix}_sem")
    options = {
        f"{s['subject_code']} - {s['subject_name']}": s
        for s in subjects if s["department"] == dept and s["semester"] == sem
    }
    label = cols[2].selectbox("Subject", list(options), key=f"{key_prefix}_subject")
    return options[label]


def dept_map(departments):
    """{'Computer Science & Engineering': 1, ...} for dropdowns."""
    return {d["dept_name"]: d["department_id"] for d in departments}


def confirm_delete(label, key, on_confirm):
    """
    Two-step delete: the user must tick a box AND press the red button.
    `on_confirm` is a function that performs the deletion.
    """
    sure = st.checkbox(f"Yes, I am sure I want to delete {label}. This cannot be undone.", key=f"{key}_sure")
    if st.button("🗑️ Delete", key=f"{key}_btn", type="primary", disabled=not sure):
        on_confirm()
