"""pages/reports.py - report viewer with CSV and (optional) PDF download. Admin only."""
import streamlit as st

from config import APP_TITLE, COLLEGE_NAME, SEMESTERS
from database import queries
from utils import authentication as auth
from utils import ui
from utils.pdf_report import PDF_AVAILABLE, dataframe_to_pdf

REPORTS = ["Student List", "Attendance Report", "Result Report", "Faculty Report"]


def render():
    auth.require_role("admin")
    ui.page_header("📑 Reports", "View a report, then download it as CSV or PDF")

    dmap = ui.dept_map(queries.get_departments())
    c1, c2, c3 = st.columns(3)
    report = c1.selectbox("Report", REPORTS, key="rep_type")
    dept_choice = c2.selectbox("Department", ["All"] + list(dmap), key="rep_dept")
    use_semester = report != "Faculty Report"
    sem_choice = c3.selectbox("Semester", ["All"] + SEMESTERS, key="rep_sem", disabled=not use_semester)
    dept_id = dmap.get(dept_choice)
    semester = None if (sem_choice == "All" or not use_semester) else sem_choice

    if report == "Student List":
        rows = queries.search_students("", dept_id, semester)
        columns = {"roll_no": "Roll No", "name": "Name", "gender": "Gender", "department": "Department",
                   "semester": "Sem", "email": "Email", "phone": "Phone", "admission_year": "Admission Year"}
    elif report == "Attendance Report":
        rows = queries.attendance_summary(dept_id=dept_id, semester=semester)
        columns = {"roll_no": "Roll No", "student_name": "Student", "dept_name": "Department", "semester": "Sem",
                   "subject_code": "Subject", "total_classes": "Classes", "present_classes": "Present",
                   "attendance_percentage": "Attendance %", "attendance_status": "Status"}
    elif report == "Result Report":
        rows = queries.get_results(dept_id=dept_id, semester=semester)
        columns = {"roll_no": "Roll No", "student_name": "Student", "dept_name": "Department", "semester": "Sem",
                   "subject_code": "Subject", "total_marks": "Total", "total_max_marks": "Out of",
                   "percentage": "%", "grade": "Grade", "result": "Result"}
    else:
        rows = queries.get_faculty_list("", dept_id)
        columns = {"name": "Name", "designation": "Designation", "department": "Department", "email": "Email",
                   "phone": "Phone", "joining_date": "Joining Date", "subject_count": "Subjects", "subjects": "Subject Codes"}

    st.caption(f"{len(rows)} row(s)")
    df = ui.show_table(rows, columns)
    if df.empty:
        return

    file_stem = report.lower().replace(" ", "_")
    c1, c2, _ = st.columns([1, 1, 3])
    c1.download_button("⬇️ Download CSV", df.to_csv(index=False).encode("utf-8"), file_name=f"{file_stem}.csv",
                       mime="text/csv")
    if PDF_AVAILABLE:
        try:
            pdf_bytes = dataframe_to_pdf(report, df, COLLEGE_NAME)
            c2.download_button("⬇️ Download PDF", pdf_bytes, file_name=f"{file_stem}.pdf", mime="application/pdf")
        except Exception as err:  # PDF is optional - never break the page because of it
            c2.caption(f"PDF unavailable: {err}")
    else:
        c2.caption("PDF export needs: pip install reportlab")
