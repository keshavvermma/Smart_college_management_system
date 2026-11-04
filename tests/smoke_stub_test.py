"""
Smoke test that runs WITHOUT Streamlit or MySQL installed.
It replaces `streamlit` and the database layer with simple fakes and calls the
render() function of every page for every role. It catches typos, wrong names,
bad imports and crashes on empty or odd data - it does NOT prove the SQL is correct
(that needs a real MySQL: use check_setup.py for that).

Run:  python -m pytest tests/smoke_stub_test.py   (or python tests/smoke_stub_test.py)
"""
import os, sys, types, datetime as dt
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class State(dict):
    __getattr__ = dict.get
    def __setattr__(self, k, v): self[k] = v


def make_streamlit(user):
    st = MagicMock(name="streamlit")
    st.session_state = State(user=user)
    st.columns.side_effect = lambda spec, **kw: [st for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.tabs.side_effect = lambda labels: [st for _ in labels]
    st.button.return_value = False
    st.form_submit_button.return_value = False
    st.checkbox.return_value = False
    st.text_input.return_value = ""
    st.text_area.return_value = ""
    st.number_input.side_effect = lambda *a, **kw: kw.get("value", 0)
    st.date_input.side_effect = lambda *a, **kw: kw.get("value") or dt.date.today()
    def selectbox(label, options=(), *a, **kw):
        options = list(options)
        return options[kw.get("index", 0) or 0] if options else None
    st.selectbox.side_effect = selectbox
    st.multiselect.return_value = []
    st.radio.side_effect = lambda label, options=(), *a, **kw: list(options)[0] if list(options) else None
    st.data_editor.side_effect = lambda df, **kw: df
    st.stop.side_effect = SystemExit
    return st


def fake_value(key):
    k = key.lower()
    if "date" in k and "time" not in k: return dt.date(2026, 10, 1)
    if k.endswith("_at"): return dt.datetime(2026, 10, 1, 10, 0)
    if "time" in k: return "09:00"
    if "year" in k: return 2025
    if k in ("role",): return "student"
    if k in ("semester", "credits"): return 3
    if any(w in k for w in ("pct", "percent", "avg", "marks", "classes", "count", "total", "present", "num", "credits", "semester", "_id", "id", "scheduled", "marked", "pending", "low")):
        return 10
    if "email" in k: return "a@b.com"
    if "gender" in k: return "Male"
    if "priority" in k: return "Normal"
    if "grade" in k: return "A"
    if "result" in k: return "Pass"
    if "status" in k: return "Present"
    if "day" in k: return "Monday"
    return "Sample"


class Row(dict):
    def __missing__(self, key): return fake_value(key)
    def get(self, key, default=None): return self[key]


import re


def columns_of(sql):
    """Guess the result column names of a SELECT (aliases or plain column names)."""
    m0 = re.search(r"SELECT\s+(?:DISTINCT\s+)?", sql, re.I)
    if not m0:
        return []
    depth, i, end = 0, m0.end(), None
    while i < len(sql):
        if sql[i] == "(": depth += 1
        elif sql[i] == ")": depth -= 1
        elif depth == 0 and re.match(r"\s+FROM\s", sql[i:], re.I):
            end = i; break
        i += 1
    class M:  # tiny stand-in for a regex match
        def group(self, n): return sql[m0.end():end if end else len(sql)]
    m = M()
    parts, depth, cur = [], 0, ""
    for ch in m.group(1):
        depth += ch == "("; depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    names = []
    for p in parts:
        p = p.strip()
        if p == "*": continue
        mm = re.search(r"\bAS\s+`?(\w+)`?\s*$", p, re.I)
        names.append(mm.group(1) if mm else re.split(r"[\s.]", p)[-1].strip("`"))
    return names


def fake_rows(sql, params=None):
    cols = columns_of(sql)
    return [Row({c: fake_value(c) for c in cols}) for _ in range(2)]


def install_fakes(user):
    st = make_streamlit(user)
    sys.modules["streamlit"] = st
    conn = types.ModuleType("mysql.connector")
    conn.Error = type("Error", (Exception,), {})
    conn.connect = MagicMock()
    pkg = types.ModuleType("mysql"); pkg.connector = conn
    sys.modules["mysql"], sys.modules["mysql.connector"] = pkg, conn
    for m in [m for m in sys.modules if m.split(".")[0] in ("pages", "utils", "database", "config")]:
        del sys.modules[m]
    import database.connection as c
    for fn in ("fetch_all",):
        setattr(c, fn, fake_rows)
    c.fetch_one = lambda sql, params=None: fake_rows(sql)[0]
    c.execute = lambda *a, **k: (1, 1)
    c.execute_many = lambda *a, **k: 1
    class Cur(MagicMock):
        def fetchall(self): return []
    from contextlib import contextmanager
    @contextmanager
    def tx():
        yield Cur()
    c.transaction = tx
    return st


def run_all():
    import importlib
    cases = {
        "admin": ["admin_dashboard", "students", "faculty", "departments", "subjects", "timetable",
                  "attendance", "marks", "notices", "reports", "settings"],
        "faculty": ["faculty_dashboard", "attendance", "marks", "timetable", "notices", "settings"],
        "student": ["student_dashboard", "attendance", "marks", "timetable", "notices", "settings"],
    }
    failures = []
    for role, mods in cases.items():
        user = {"user_id": 1, "username": "u", "role": role, "ref_id": 1, "name": "Test User"}
        install_fakes(user)
        for mod in mods:
            m = importlib.import_module(f"pages.{mod}")
            fns = [getattr(m, n) for n in dir(m) if n.startswith("render") and callable(getattr(m, n))]
            for fn in fns:
                try:
                    fn()
                except SystemExit:
                    pass   # require_role() stops pages not meant for this role - expected
                except Exception as e:
                    import traceback
                    failures.append(f"{role}/{mod}.{fn.__name__}: {type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}")
    return failures


def test_all_pages_render_with_fakes():
    failures = run_all()
    assert not failures, "\n".join(failures)


if __name__ == "__main__":
    f = run_all()
    print("\n".join(f) if f else "ALL PAGES OK")
    sys.exit(1 if f else 0)
