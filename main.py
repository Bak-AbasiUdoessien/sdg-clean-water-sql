"""
main.py  -  Clean Water & Health Tracker (SDG 6 + SDG 3)
1. Builds a SQLite database from sql/schema.sql
2. Loads the CSV files in data/ into it
3. Runs every query in sql/queries.sql and prints the results as tables

Run it:  python main.py
Needs only the Python standard library (no pip install).
"""

import csv                      # read the CSV files
import sqlite3                  # SQLite database engine that ships with Python
import sys                      # used to exit with an error message
from pathlib import Path        # cross-platform file paths

ROOT = Path(__file__).parent            # folder this script lives in
DATA_DIR = ROOT / "data"                # where the CSV files are
SQL_DIR = ROOT / "sql"                  # where the .sql files are
DB_PATH = ROOT / "water_health.db"      # the database file that will be created

# Which CSV goes into which table. Order matters: parent table (regions) first.
TABLES = ["regions", "water_points", "disease_cases"]


def build_database(conn):
    """Create the tables by running schema.sql."""
    schema = (SQL_DIR / "schema.sql").read_text(encoding="utf-8")  # read the whole file as one string
    conn.executescript(schema)                                     # executescript runs many statements at once


def load_csv(conn, table):
    """Insert every row of data/<table>.csv into the table with the same name."""
    path = DATA_DIR / f"{table}.csv"                    # e.g. data/regions.csv
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)                          # reads each line into a list of strings
        header = next(reader)                           # first line = column names
        rows = list(reader)                             # every remaining line = data
    columns = ", ".join(header)                         # "region_id, name, state, population"
    placeholders = ", ".join("?" for _ in header)       # "?, ?, ?, ?" - one ? per column
    # The ? placeholders let sqlite3 insert values safely (prevents SQL injection).
    conn.executemany(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", rows)
    print(f"loaded {len(rows):>4} rows into {table}")


def split_queries(text):
    """Split queries.sql into (title, sql) pairs using the '-- name:' marker lines."""
    queries = []                                        # list of (title, sql) tuples to return
    title, lines = None, []                             # current query title and its lines
    for line in text.splitlines():                      # go through the file line by line
        if line.startswith("-- name:"):                 # a new query starts here
            if title:                                   # save the previous query first (if any)
                queries.append((title, "\n".join(lines)))
            title = line.removeprefix("-- name:").strip()  # keep just the title text
            lines = []                                  # start collecting fresh lines
        elif title:                                     # ignore the file header before the first query
            lines.append(line)
    if title:                                           # don't forget the last query in the file
        queries.append((title, "\n".join(lines)))
    return queries


def print_table(headers, rows):
    """Print rows as a neat text table with aligned columns."""
    cells = [[str(v) for v in row] for row in rows]     # convert every value to text
    widths = [max(len(h), *(len(r[i]) for r in cells)) if cells else len(h)  # widest value per column
              for i, h in enumerate(headers)]
    line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))  # ljust pads text to the column width
    print(line)                                         # header row
    print("-+-".join("-" * w for w in widths))          # separator row
    for r in cells:
        print(" | ".join(v.ljust(w) for v, w in zip(r, widths)))  # each data row


def main():
    missing = [t for t in TABLES if not (DATA_DIR / f"{t}.csv").exists()]  # CSVs that don't exist yet
    if missing:                                                          # stop with a helpful hint
        sys.exit(f"Missing data files: {missing}. Run: python generate_sample_data.py")

    with sqlite3.connect(DB_PATH) as conn:              # opens (or creates) the database file; commits on success
        conn.execute("PRAGMA foreign_keys = ON")        # SQLite only enforces foreign keys when asked
        build_database(conn)                            # fresh tables every run
        for table in TABLES:
            load_csv(conn, table)                       # fill each table

        sql_text = (SQL_DIR / "queries.sql").read_text(encoding="utf-8")
        for title, sql in split_queries(sql_text):      # run each analysis query
            cursor = conn.execute(sql)                  # execute returns a cursor holding the results
            headers = [d[0] for d in cursor.description]  # description holds column info; [0] is the name
            print(f"\n=== {title} ===")
            print_table(headers, cursor.fetchall())     # fetchall pulls every result row

    print(f"\nDatabase saved to {DB_PATH.name} - open it in VS Code with a SQLite extension to explore.")


if __name__ == "__main__":
    main()
