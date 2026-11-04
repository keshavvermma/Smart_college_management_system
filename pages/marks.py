"""
pages/marks.py - marks and results for all three roles.

  faculty : enter marks for THEIR subjects only
  admin   : enter/view/delete marks for any subject
  student : view ONLY their own marks and results
"""
import mysql.connector
import pandas as pd
import streamlit as st

from config import DEFAULT_MAX_MARKS, EXAM_TYPES, SEMESTERS
from database import queries
from utils import authentication as auth
from utils import ui
from utils.calculations import marks_summary
from utils.validators import validate_marks_entry

MARK_COLUMNS = {
    "roll_no": "Roll No", "student_name": "Student", "subject_code": "Subject", "exam_type": "Exam",
    "marks": "Marks", "max_marks": "Max", "percentage": "%", "grade": "Grade", "result": "Result",
}
RESULT_COLUMNS = {
    "roll_no": "Roll No", "student_name": "Student", "dept_name": "Department", "semester": "Sem",
    "subject_code": "Subject", "total_marks": "Total", "total_max_marks": "Out of", "percentage": "%",
    "grade": "Grade", "result": "Result",
}


def render():
    user = auth.require_role("admin", "faculty", "student")
    if user["role"] == "student":
        _render_student()
    else:
        _render_staff(user)


# =====================================================================
# Faculty / Admin
# =====================================================================
def _render_staff(user):
    faculty_id = auth.current_faculty_id()  # None for admin
    ui.page_header("📝 Marks & Results", "Enter marks - grade, percentage and Pass/Fail are calculated automatically")
    ui.show_flash()
    tab_enter, tab_view, tab_results = st.tabs(["✏️ Enter Marks", "📄 Marks Entries", "🏆 Results Summary"])
    with tab_enter:
        _enter_marks(faculty_id)
    with tab_view:
        _view_marks(faculty_id, is_admin=user["role"] == "admin")
    with tab_results:
        _results_summary(faculty_id)


def _enter_marks(faculty_id):
    subjects = queries.get_subjects(faculty_id=faculty_id)
    if not subjects:
        st.info("No subjects are assigned to you yet. Ask the admin to assign subjects.")
        return

    subject = ui.pick_subject(subjects, "mk")
    c1, c2 = st.columns(2)
    exam_type = c1.selectbox("Exam type", EXAM_TYPES, key="mk_exam")
    max_marks = c2.number_input("Maximum marks", min_value=1.0, max_value=500.0, step=1.0,
                                value=float(DEFAULT_MAX_MARKS[exam_type]), key=f"mk_max_{exam_type}")

    students = queries.get_students_for_class(subject["department_id"], subject["semester"])
    if not students:
        st.warning("There are no students in this department and semester.")
        return
    existing = queries.get_marks_for_entry(subject["subject_id"], exam_type)

    df = pd.DataFrame({
        "student_id": [s["student_id"] for s in students],
        "Roll No": [s["roll_no"] for s in students],
        "Name": [s["name"] for s in students],
        "Marks": [existing.get(s["student_id"], {}).get("marks") for s in students],
    })
    df["Marks"] = pd.to_numeric(df["Marks"], errors="coerce")

    st.caption("Type the marks in the 'Marks' column. Leave a cell empty to skip that student.")
    edited = st.data_editor(
        df,
        hide_index=True,
        disabled=["student_id", "Roll No", "Name"],
        column_config={
            "student_id": None,
            "Marks": st.column_config.NumberColumn("Marks", min_value=0.0, max_value=float(max_marks), step=0.5),
        },
        key=f"mk_editor_{subject['subject_id']}_{exam_type}_{max_marks}",
    )

    entered = edited.dropna(subset=["Marks"])
    if not entered.empty:
        with st.expander("Preview percentage, grade and result", expanded=False):
            preview = []
            for _, r in entered.iterrows():
                s = marks_summary(float(r["Marks"]), float(max_marks))
                preview.append({"Roll No": r["Roll No"], "Name": r["Name"], "Marks": r["Marks"],
                                "Percentage": s["percentage"], "Grade": s["grade"], "Result": s["result"]})
            st.dataframe(pd.DataFrame(preview), hide_index=True)

    if st.button("💾 Save Marks", type="primary", key="mk_save"):
        records, errors = {}, []
        for sid, name, value in zip(entered["student_id"], entered["Name"], entered["Marks"]):
            problem = validate_marks_entry(float(value), float(max_marks))
            if problem:
                errors.append(f"{name}: {problem}")
            else:
                records[int(sid)] = float(value)
        for e in errors:
            st.error(e)
        if not records and not errors:
            st.warning("Nothing to save - enter at least one mark.")
        if records and not errors:
            saved = False
            try:
                count = queries.save_marks(subject["subject_id"], exam_type, float(max_marks), records, faculty_id)
                saved = True
            except (PermissionError, ValueError) as err:
                st.error(str(err))
            except mysql.connector.Error as err:
                st.error(ui.db_error_message(err))
            if saved:
                ui.flash(f"✅ Saved {count} {exam_type} mark(s) for {subject['subject_code']}.")
                st.rerun()


def _filters(prefix):
    dmap = ui.dept_map(queries.get_departments())
    c1, c2, c3 = st.columns(3)
    dept_choice = c1.selectbox("Department", ["All"] + list(dmap), key=f"{prefix}_dept")
    sem_choice = c2.selectbox("Semester", ["All"] + SEMESTERS, key=f"{prefix}_sem")
    exam_choice = c3.selectbox("Exam type", ["All"] + EXAM_TYPES, key=f"{prefix}_exam")
    return (dmap.get(dept_choice), None if sem_choice == "All" else sem_choice,
            None if exam_choice == "All" else exam_choice)


def _view_marks(faculty_id, is_admin):
    dept_id, semester, exam = _filters("mkv")
    rows = queries.get_marks(dept_id=dept_id, semester=semester, exam_type=exam, faculty_id=faculty_id)
    ui.show_table(rows, MARK_COLUMNS)

    if is_admin and rows:
        with st.expander("🗑️ Delete a marks entry (admin)"):
            options = {
                f"{r['roll_no']} | {r['subject_code']} | {r['exam_type']} | {r['marks']:g}/{r['max_marks']:g}": r["mark_id"]
                for r in rows
            }
            label = st.selectbox("Select entry", list(options), key="mk_del_pick")
            mark_id = options[label]

            def _delete():
                try:
                    queries.delete_mark(mark_id)
                except mysql.connector.Error as err:
                    st.error(ui.db_error_message(err))
                    return
                ui.flash("🗑️ Marks entry deleted.")
                st.rerun()

            ui.confirm_delete("this marks entry", f"del_mark_{mark_id}", _delete)


def _results_summary(faculty_id):
    dmap = ui.dept_map(queries.get_departments())
    c1, c2 = st.columns(2)
    dept_choice = c1.selectbox("Department", ["All"] + list(dmap), key="mkr_dept")
    sem_choice = c2.selectbox("Semester", ["All"] + SEMESTERS, key="mkr_sem")
    rows = queries.get_results(dept_id=dmap.get(dept_choice),
                               semester=None if sem_choice == "All" else sem_choice, faculty_id=faculty_id)
    df = ui.show_table(rows, RESULT_COLUMNS, empty_message="No marks have been entered yet.")
    if not df.empty:
        total = len(df)
        passed = int((df["Result"] == "Pass").sum())
        cols = st.columns(3)
        with cols[0]:
            ui.metric_card("Results", total)
        with cols[1]:
            ui.metric_card("Pass", f"{passed} ({passed * 100 / total:.0f}%)")
        with cols[2]:
            ui.metric_card("Fail", total - passed)
        st.subheader("Grade distribution")
        grade_order = ["A+", "A", "B+", "B", "C", "D", "F"]
        counts = df["Grade"].value_counts().reindex(grade_order, fill_value=0)
        st.bar_chart(counts)


# =====================================================================
# Student (own data only)
# =====================================================================
def _render_student():
    student_id = auth.current_student_id()
    ui.page_header("📝 My Marks & Results")

    results = queries.get_results(student_id=student_id)
    if not results:
        st.info("No marks have been published for you yet.")
        return

    avg = sum(r["percentage"] for r in results) / len(results)
    passed = sum(1 for r in results if r["result"] == "Pass")
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card("Average", ui.pct(avg))
    with cols[1]:
        ui.metric_card("Subjects Passed", f"{passed}/{len(results)}")
    with cols[2]:
        ui.metric_card("Subjects Failed", len(results) - passed)

    st.subheader("Subject results (all exams combined)")
    ui.show_table(results, {
        "subject_code": "Code", "subject_name": "Subject", "total_marks": "Total", "total_max_marks": "Out of",
        "percentage": "%", "grade": "Grade", "result": "Result"})

    st.subheader("Exam-wise marks")
    ui.show_table(queries.get_marks(student_id=student_id), {
        "subject_code": "Code", "subject_name": "Subject", "exam_type": "Exam", "marks": "Marks",
        "max_marks": "Max", "percentage": "%", "grade": "Grade", "result": "Result"})
