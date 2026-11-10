
"""Run a read-only EdAtlas SQL query and export its results."""

import argparse
import csv
from pathlib import Path

from sqlalchemy import text

from edatlas.warehouse.build import get_engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_file", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
    )
    args = parser.parse_args()

    sql_file = args.sql_file.resolve()
    sql = sql_file.read_text(encoding="utf-8").strip()

    if sql_file.suffix.lower() != ".sql":
        raise ValueError("Expected a .sql file")

   # Ignore leading blank lines and SQL comments.
    sql_lines = [
        line.strip()
        for line in sql.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]

    if not sql_lines:
        raise ValueError("SQL file is empty or contains only comments")

    first_line = sql_lines[0].upper()

    if not (
        first_line.startswith("SELECT ")
        or first_line.startswith("WITH ")
    ):
        raise ValueError("Only SELECT queries are supported")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / f"{sql_file.stem}.csv"

    engine = get_engine()
    try:
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(
                    text("SET TRANSACTION READ ONLY")
                )
                result = connection.execute(text(sql))
                columns = list(result.keys())
                rows = result.fetchall()

        with destination.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)

        print(" | ".join(columns))
        for row in rows:
            print(" | ".join(map(str, row)))

        print(f"\nRows returned: {len(rows)}")
        print(f"CSV exported to: {destination}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
