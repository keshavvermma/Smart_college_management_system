"""
utils/calculations.py - attendance %, marks %, grade and pass/fail rules.

All academic formulas live in this one file so they are easy to explain in the
viva and easy to change. The SQL views used by Power BI (sql/college_database.sql)
follow exactly the same rules.
"""
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

import config


def _round2(value) -> float:
    """Round to 2 decimals, half-up (same as MySQL ROUND on DECIMAL values)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# ------------------------------------------------------------- attendance
def attendance_percentage(present, total) -> float:
    """Attendance % = (Present Classes / Total Classes) x 100."""
    present, total = float(present or 0), float(total or 0)
    if total <= 0:
        return 0.0
    return _round2(present / total * 100)


def is_attendance_low(percentage, total_classes=None) -> bool:
    """True when the % is below the threshold (75).
    If total_classes is given and is 0 (no class held yet) the answer is False."""
    if total_classes is not None and float(total_classes or 0) <= 0:
        return False
    return percentage is not None and percentage < config.ATTENDANCE_THRESHOLD


def attendance_warning(name, percentage) -> str:
    """Message such as:  Student: Rahul | Attendance: 68% | Warning."""
    return f"Student: {name} - Attendance: {percentage:g}% - ⚠️ Attendance below {config.ATTENDANCE_THRESHOLD}%"


def add_attendance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'attendance_pct' and 'status' columns to a frame that has
    'present_classes' and 'total_classes'."""
    df = df.copy()
    if df.empty:
        df["attendance_pct"] = []
        df["status"] = []
        return df
    df["attendance_pct"] = [
        attendance_percentage(p, t) for p, t in zip(df["present_classes"], df["total_classes"])
    ]
    df["status"] = [
        "No classes yet" if float(t or 0) == 0
        else ("⚠️ Below %d%%" % config.ATTENDANCE_THRESHOLD if is_attendance_low(p, t) else "✅ OK")
        for p, t in zip(df["attendance_pct"], df["total_classes"])
    ]
    return df


# ------------------------------------------------------------------ marks
def marks_percentage(marks, max_marks) -> float:
    """Percentage = marks / max marks x 100."""
    max_marks = Decimal(str(max_marks or 0))
    if max_marks <= 0:
        return 0.0
    return _round2(Decimal(str(marks or 0)) / max_marks * 100)


def grade_from_percentage(percentage) -> str:
    """90-100 A+, 80-89 A, 70-79 B+, 60-69 B, 50-59 C, 40-49 D, below 40 F."""
    p = float(percentage)
    if p >= 90:
        return "A+"
    if p >= 80:
        return "A"
    if p >= 70:
        return "B+"
    if p >= 60:
        return "B"
    if p >= 50:
        return "C"
    if p >= 40:
        return "D"
    return "F"


def result_from_percentage(percentage) -> str:
    return "Pass" if float(percentage) >= config.PASS_PERCENTAGE else "Fail"


def evaluate_marks(marks, max_marks) -> dict:
    """Return percentage, grade and result for one mark entry."""
    pct = marks_percentage(marks, max_marks)
    return {
        "percentage": pct,
        "grade": grade_from_percentage(pct),
        "result": result_from_percentage(pct),
    }


marks_summary = evaluate_marks   # short alias used by the marks page


def add_result_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add percentage / grade / result columns to a frame with 'marks' and 'max_marks'."""
    df = df.copy()
    if df.empty:
        for col in ("percentage", "grade", "result"):
            df[col] = []
        return df
    evaluated = [evaluate_marks(m, mx) for m, mx in zip(df["marks"], df["max_marks"])]
    df["percentage"] = [e["percentage"] for e in evaluated]
    df["grade"] = [e["grade"] for e in evaluated]
    df["result"] = [e["result"] for e in evaluated]
    return df


def subject_summary(df: pd.DataFrame, group_cols) -> pd.DataFrame:
    """Combine all exams of a subject: total obtained, total maximum, %, grade, result.

    `group_cols` is the list of columns that identify one row of the summary,
    e.g. ["subject_code", "subject_name"] for one student, or
    ["roll_no", "student_name", "subject_code", "subject_name"] for a class.
    """
    if df.empty:
        return pd.DataFrame(columns=list(group_cols) + [
            "total_obtained", "total_max", "percentage", "grade", "result"])
    summary = (
        df.groupby(list(group_cols), as_index=False, sort=False)
        .agg(total_obtained=("marks", "sum"), total_max=("max_marks", "sum"))
    )
    evaluated = [evaluate_marks(o, m) for o, m in zip(summary["total_obtained"], summary["total_max"])]
    summary["percentage"] = [e["percentage"] for e in evaluated]
    summary["grade"] = [e["grade"] for e in evaluated]
    summary["result"] = [e["result"] for e in evaluated]
    return summary
