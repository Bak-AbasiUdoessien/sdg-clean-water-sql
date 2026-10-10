"""Tests for the schema and queries. Run from the project folder:  python -m unittest discover tests"""

import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # make "import main" work
import main  # noqa: E402


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")                # fresh, temporary database
        self.conn.execute("PRAGMA foreign_keys = ON")
        main.build_database(self.conn)
        self.conn.executescript("""
            INSERT INTO regions VALUES (1, 'R1', 'S', 1000), (2, 'R2', 'S', 1000);
            INSERT INTO water_points VALUES
                (1, 1, 'borehole', 1, 600),            -- working and safe -> counts
                (2, 1, 'borehole', 0, 300),            -- broken -> doesn't count
                (3, 1, 'unprotected_well', 1, 100),    -- unsafe -> doesn't count
                (4, 2, 'piped_tap', 1, 900);
            INSERT INTO disease_cases VALUES (1, '2025-01', 10), (1, '2025-02', 25),
                                             (2, '2025-01', 4),  (2, '2025-02', 2);
        """)
        self.queries = main.split_queries((main.SQL_DIR / "queries.sql").read_text())

    def run_query(self, prefix):
        sql = next(q for t, q in self.queries if t.startswith(prefix))   # first query whose title matches
        return self.conn.execute(sql).fetchall()

    def test_five_queries_found(self):
        self.assertEqual(len(self.queries), 5)

    def test_coverage_counts_only_working_safe_points(self):
        rows = self.run_query("1.")
        self.assertEqual(rows[0][0], "R1")                     # worst coverage first
        self.assertEqual(rows[0][3], 60.0)                     # 600 of 1,000 people

    def test_broken_points(self):
        self.assertEqual(self.run_query("2."), [("R1", 1, 300)])

    def test_month_over_month_change(self):
        rows = self.run_query("4.")
        self.assertEqual(rows[1][4], 15)                       # R1: 10 -> 25 cases = +15

    def test_check_constraint_rejects_bad_source(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO water_points VALUES (9, 1, 'river', 1, 10)")

    def tearDown(self):
        self.conn.close()


if __name__ == "__main__":
    unittest.main()
