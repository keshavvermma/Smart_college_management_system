# Power BI Guide – Smart College Dashboard

Power BI reads the **same MySQL database** (`smart_college`) that the Streamlit app writes to.
> A `.pbix` file is not included: Power BI files are built in Power BI Desktop (Windows). This guide gives the exact connection steps, model, DAX and page designs so you can build it in about 45 minutes.

## 1. Connect MySQL to Power BI
1. Install **MySQL Connector/NET 8.x** from https://dev.mysql.com/downloads/connector/net/ and restart Power BI Desktop (Power BI needs it for MySQL).
2. Power BI Desktop → **Home → Get data → MySQL database → Connect**.
3. Server `localhost` (or `localhost:3306`) · Database `smart_college` · Data Connectivity mode **Import** → OK.
4. In the **Database** tab enter user + password → Connect.
5. In *Navigator* tick: `vw_attendance_detail`, `vw_attendance_summary`, `vw_marks_detail`, `vw_student_results`, `vw_student_overview`, `departments`, `faculty`, `subjects` → **Load**.
6. After new data is entered in the app: **Home → Refresh**.

**Optional – read-only account for Power BI** (safer than root). Run in Workbench:
```sql
CREATE USER 'powerbi_reader'@'localhost' IDENTIFIED BY 'ChangeThis#123';
GRANT SELECT ON smart_college.* TO 'powerbi_reader'@'localhost';
FLUSH PRIVILEGES;
```

## 2. Data model (Model view)
| View / table | Grain (one row = …) | Used for |
|---|---|---|
| `vw_student_overview` | one student | **dimension**: gender, department, semester, academic year, overall attendance / marks |
| `departments`, `subjects`, `faculty` | one each | dimensions |
| `vw_attendance_detail` | one attendance record | monthly trend, present/absent counts |
| `vw_attendance_summary` | student × subject | subject-wise %, students below 75 % |
| `vw_marks_detail` | one mark entry | grade distribution, exam-wise |
| `vw_student_results` | student × subject (all exams added) | pass/fail, top students |

Relationships (many → one, single direction):
* `vw_attendance_detail[student_id]` → `vw_student_overview[student_id]`
* `vw_attendance_summary[student_id]` → `vw_student_overview[student_id]`
* `vw_marks_detail[student_id]` → `vw_student_overview[student_id]`
* `vw_student_results[student_id]` → `vw_student_overview[student_id]`
* `subjects[subject_id]` → `vw_attendance_summary[subject_id]`, `vw_marks_detail[subject_id]`, `vw_student_results[subject_id]` (many side = view)
* `departments[dept_name]` ← `vw_student_overview[dept_name]` (optional; `dept_name` is already inside each view)

Use `vw_student_overview` for the Department / Semester / Gender / Academic Year **slicers** so every page filters together.

## 3. DAX measures (create a table `_Measures`)
```DAX
Total Students     = DISTINCTCOUNT ( vw_student_overview[student_id] )
Total Faculty      = COUNTROWS ( faculty )
Total Departments  = COUNTROWS ( departments )

Present Classes    = SUM ( vw_attendance_detail[is_present] )
Total Classes      = COUNTROWS ( vw_attendance_detail )
Average Attendance = DIVIDE ( [Present Classes], [Total Classes] ) * 100

Average Marks %    = AVERAGE ( vw_marks_detail[percentage] )

Pass %             = DIVIDE (
                        CALCULATE ( COUNTROWS ( vw_student_results ), vw_student_results[result] = "Pass" ),
                        COUNTROWS ( vw_student_results ) ) * 100

Students Below 75  = CALCULATE ( DISTINCTCOUNT ( vw_student_overview[student_id] ),
                                 vw_student_overview[overall_attendance] < 75 )
```
Set formatting: percentages with 1 decimal. Conditional formatting for attendance: red < 75, green ≥ 75.

## 4. Report pages
**Page 1 – Overview**: six KPI cards (Total Students, Total Faculty, Total Departments, Average Attendance, Average Marks %, Pass %) · clustered bar *Students by department* · donut *Students by gender* · slicers Department/Semester.

**Page 2 – Attendance Analytics**
* Bar: *Average Attendance* by `dept_name` (Department-wise)
* Column: *Average Attendance* by `semester`
* Bar: *Average Attendance* by `subject_name` (from `vw_attendance_detail`)
* Table: `student_name, roll_no, overall_attendance` filtered `< 75` (Students below 75 %)
* Line: *Average Attendance* by `month_name` (sort by `month_key`)

**Page 3 – Academic Performance**
* Bar: *Average Marks %* by `dept_name`
* Bar: *Average Marks %* by `subject_name`
* 100 % stacked column / donut: Pass vs Fail (`vw_student_results[result]`)
* Column: count of `grade` (grade distribution, order A+ → F)
* Table: *Top 10* students by `vw_student_overview[overall_marks_percentage]` (Filters pane → Top N)

**Page 4 – Student Analytics**: slicers **Department, Semester, Gender, Academic Year** (all from `vw_student_overview`) · table of students with `overall_attendance`, `overall_marks_percentage` · scatter *attendance (x) vs marks (y)* per student · KPI cards that react to the slicers.

Theme: navy `#1E3A8A`, light grey background `#F1F5F9`, red `#DC2626` for warnings (same as the web app).

## 5. Notes
* `academic_year` in `vw_student_overview` is the **admission** year range; semester + department already identify the class.
* Grade and pass/fail rules in the views are identical to `utils/calculations.py` (A+ ≥ 90 … D ≥ 40, F < 40; pass ≥ 40 %).
* "Average Attendance" is record-weighted (present records ÷ all records), which is also what the Admin dashboard shows.
