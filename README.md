# Clean Water & Health Tracker (SDG 6 + SDG 3)

A SQLite database and set of SQL queries for checking whether communities have **working, safe water** and whether low water access goes with more **water-borne illness**.

**SDG targets covered:** 6.1 (safe drinking water for all) and 3.3 (fight water-borne diseases).

## What it does
| Query | Question it answers | SQL skills shown |
|---|---|---|
| 1 | What % of each region is served by a working, safe water source? | `LEFT JOIN`, `CASE WHEN`, `SUM`, `GROUP BY` |
| 2 | Where are broken water points cutting off the most people? (repair priority list) | `WHERE` vs `HAVING` |
| 3 | Do regions with lower coverage report more diarrhoea per 1,000 people? | CTEs (`WITH`), rates, risk bands |
| 4 | Are cases rising or falling month to month? | Window function `LAG() OVER (PARTITION BY …)` |
| 5 | Which region in each state should be fixed first? | Window function `RANK()` |

## Run it (VS Code)
```bash
python generate_sample_data.py   # creates data/*.csv (made-up practice data)
python main.py                   # builds water_health.db and prints all 5 query results
python -m unittest discover tests  # unit tests on an in-memory database
```
You don't need to `pip install` anything, because everything uses the Python standard library.
To browse the database in VS Code, install the **SQLite Viewer** or **SQLTools + SQLite driver** extension and open `water_health.db`.

## Files
```
schema.sql               table design: keys, foreign keys, CHECK constraints, indexes
queries.sql              the 5 analysis queries (each line commented)
generate_sample_data.py  makes the synthetic CSVs
main.py                  builds the DB, loads CSVs, runs queries, prints tables
```

## ⚠️ About the data
The bundled data is **synthetic** (randomly generated, with fictional region names). It is only for practice, so don't present its numbers as real findings.

## Using real data (do this next, it makes the project much stronger)
- **Water Point Data Exchange (WPdx)**: real water-point records for Nigeria and many other countries, with fields for water source type and whether the point works. Map its columns onto `water_points`.
- **NBS / DHIS2 / NCDC reports**: regional disease case counts for `disease_cases`.
- **Population** per LGA from the National Population Commission or WorldPop.

Once you switch to real data, add a short "Findings" section to this README with 2–3 sentences and a chart. That section is the part recruiters actually read.
