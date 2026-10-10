"""
generate_sample_data.py
Creates SYNTHETIC (made-up) CSV files so the project runs without any downloads.
The numbers are NOT real statistics - they only exist to practise SQL on.
Swap them for real data later (see README: "Using real data").
"""

import csv                      # built-in module for reading/writing CSV files
import random                   # built-in module for generating random numbers
from pathlib import Path        # Path makes file paths work the same on Windows, Mac and Linux

DATA_DIR = Path(__file__).parent / "data"   # the "data" folder that sits next to this script
random.seed(42)                             # fixed seed = the "random" data is identical every run (reproducible)

# Fictional regions: (name, state, population). Names are invented on purpose.
REGIONS = [
    ("Riverbend", "North State", 120_000),   # underscores in numbers are just for readability (= 120000)
    ("Dry Plains", "North State", 85_000),
    ("Hilltop", "North State", 60_000),
    ("Lakeside", "South State", 150_000),
    ("Old Market", "South State", 95_000),
    ("Palm Grove", "South State", 70_000),
]

# Source types and how likely each one is to appear (weights).
SOURCE_TYPES = ["borehole", "protected_well", "piped_tap", "unprotected_well"]  # must match the CHECK in schema.sql
SOURCE_WEIGHTS = [4, 3, 2, 3]                                                   # boreholes most common, taps rarest

MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]   # list comprehension: builds '2025-01' ... '2025-12'


def write_csv(filename, header, rows):
    """Write a list of rows to data/<filename> with the given header row."""
    DATA_DIR.mkdir(exist_ok=True)                           # create the data folder if it is missing
    with open(DATA_DIR / filename, "w", newline="", encoding="utf-8") as f:  # newline="" stops blank lines on Windows
        writer = csv.writer(f)                              # csv.writer handles commas/quotes for us
        writer.writerow(header)                             # first line = column names
        writer.writerows(rows)                              # then every data row
    print(f"wrote {len(rows):>4} rows -> data/{filename}")  # :>4 right-aligns the number in 4 spaces


def main():
    """Build all three CSV files."""
    # ---- regions.csv -------------------------------------------------
    region_rows = [(i, name, state, pop)                    # (region_id, name, state, population)
                   for i, (name, state, pop) in enumerate(REGIONS, start=1)]  # enumerate gives 1,2,3... as ids
    write_csv("regions.csv", ["region_id", "name", "state", "population"], region_rows)

    # ---- water_points.csv --------------------------------------------
    point_rows = []                                         # empty list we will fill in the loop
    quality_by_region = {}                                  # remember each region's score for the disease step
    point_id = 1                                            # counter for unique water point ids
    for region_id, _name, _state, pop in region_rows:       # _name/_state: underscore = "not used here"
        quality = random.uniform(0.3, 1.0)                  # each region gets a hidden "how well-served" score
        quality_by_region[region_id] = quality              # store it in the dictionary under the region's id
        n_points = random.randint(15, 40)                   # how many water points this region has
        for _ in range(n_points):                           # repeat n_points times
            source = random.choices(SOURCE_TYPES, SOURCE_WEIGHTS)[0]   # pick a type using the weights
            functional = 1 if random.random() < 0.6 + 0.35 * quality else 0  # better regions -> fewer broken points
            served = int(pop * quality / n_points * random.uniform(0.6, 1.4))  # share of population per point
            point_rows.append((point_id, region_id, source, functional, served))  # add the row
            point_id += 1                                   # next id
    write_csv("water_points.csv",
              ["point_id", "region_id", "source_type", "is_functional", "people_served"], point_rows)

    # ---- disease_cases.csv -------------------------------------------
    case_rows = []                                          # will hold one row per region per month
    for region_id, _name, _state, pop in region_rows:
        quality = quality_by_region[region_id]              # look up the region's water score from above
        base_rate = 5.0 * (1.1 - quality) * random.uniform(0.8, 1.2)  # worse water -> more cases (assumption)
        for month_index, month in enumerate(MONTHS):        # month_index = 0..11
            rainy = 1.5 if 5 <= month_index <= 8 else 1.0  # June-September rainy season raises cases (assumption)
            cases = int(pop / 1000 * base_rate * rainy * random.uniform(0.8, 1.2))  # add some noise
            case_rows.append((region_id, month, cases))
    write_csv("disease_cases.csv", ["region_id", "month", "diarrhoea_cases"], case_rows)


if __name__ == "__main__":   # True only when you run this file directly (not when it is imported)
    main()                   # so the data is generated only on "python generate_sample_data.py"
