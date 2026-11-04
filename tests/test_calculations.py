"""Run all tests with:   python -m unittest discover -s tests -v   (from the project folder)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.calculations import (attendance_percentage, evaluate_marks, grade_from_percentage,
                                is_attendance_low, marks_percentage, result_from_percentage)


class TestAttendance(unittest.TestCase):
    def test_percentage(self):
        self.assertEqual(attendance_percentage(17, 25), 68.0)
        self.assertEqual(attendance_percentage(0, 0), 0.0)
        self.assertEqual(attendance_percentage(10, 10), 100.0)

    def test_threshold(self):
        self.assertTrue(is_attendance_low(68, 25))
        self.assertTrue(is_attendance_low(74.99, 25))
        self.assertFalse(is_attendance_low(75, 25))
        self.assertFalse(is_attendance_low(0, 0))   # no classes held yet


class TestMarks(unittest.TestCase):
    def test_grades_match_scale(self):
        cases = {100: "A+", 90: "A+", 89.99: "A", 80: "A", 79: "B+", 70: "B+", 69: "B", 60: "B",
                 59: "C", 50: "C", 49: "D", 40: "D", 39.99: "F", 0: "F"}
        for pct, grade in cases.items():
            self.assertEqual(grade_from_percentage(pct), grade, pct)

    def test_pass_fail(self):
        self.assertEqual(result_from_percentage(40), "Pass")
        self.assertEqual(result_from_percentage(39.9), "Fail")

    def test_summary(self):
        s = evaluate_marks(76, 100)
        self.assertEqual((s["percentage"], s["grade"], s["result"]), (76.0, "B+", "Pass"))
        s = evaluate_marks(14, 50)
        self.assertEqual((s["percentage"], s["grade"], s["result"]), (28.0, "F", "Fail"))
        self.assertEqual(marks_percentage(5, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
