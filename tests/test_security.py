import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import hash_password, verify_password


class TestPasswords(unittest.TestCase):
    def test_round_trip(self):
        h = hash_password("admin123")
        self.assertNotIn("admin123", h)
        self.assertTrue(verify_password("admin123", h))
        self.assertFalse(verify_password("wrong", h))

    def test_salt_is_random(self):
        self.assertNotEqual(hash_password("same"), hash_password("same"))

    def test_garbage_hash(self):
        self.assertFalse(verify_password("x", "not-a-hash"))
        self.assertFalse(verify_password("x", None))


class TestSampleDataHashes(unittest.TestCase):
    """The hashes inside sql/college_database.sql must match the documented demo passwords."""

    def test_demo_hashes(self):
        import re
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "college_database.sql")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        expected = {"'admin'": "admin123", "'rajesh.sharma'": "faculty123", "'cse24001'": "student123"}
        for username, password in expected.items():
            m = re.search(r"\(\d+, " + re.escape(username) + r", '(pbkdf2_sha256\$[^']+)'", text)
            self.assertIsNotNone(m, username)
            self.assertTrue(verify_password(password, m.group(1)), username)


if __name__ == "__main__":
    unittest.main()
