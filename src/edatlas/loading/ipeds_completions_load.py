
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

PROGRAM_PATH = (
    PROJECT_ROOT / "data" / "processed"
    / "ipeds_completions_programs_2024.csv"
)

TOTAL_PATH = (
    PROJECT_ROOT / "data" / "processed"
    / "ipeds_completions_totals_2024.csv"
)

PROGRAM_TABLE = "ipeds_completions_programs_2024"
TOTAL_TABLE = "ipeds_completions_totals_2024"

COMMON_COLUMNS = [
    "school_id",
    "award_level",
    "total_awards",
    "male_awards",
    "female_awards",
    "reporting_flag",
]

PROGRAM_COLUMNS = [
    "school_id",
    "cip_code",
    "award_level",
    "total_awards",
    "male_awards",
    "female_awards",
    "reporting_flag",
]


def read_data():
    """Read the two processed completions datasets."""
    programs = pd.read_csv(
        PROGRAM_PATH,
        dtype={"cip_code": "string"},
    )
    totals = pd.read_csv(TOTAL_PATH)

    return programs, totals


def validate_data(df, expected_columns, key_columns):
    """Validate structure, identifiers, and award counts."""
    if df.empty:
        raise ValueError("Completions dataset is empty")

    if list(df.columns) != expected_columns:
        raise ValueError("Unexpected completions columns")

    if df[key_columns].isna().any().any():
        raise ValueError("Missing completion identifiers")

    if df.duplicated(key_columns).any():
        raise ValueError("Duplicate completion identifiers")

    numeric_columns = [
        "school_id",
        "award_level",
        "total_awards",
        "male_awards",
        "female_awards",
    ]

    for column in numeric_columns:
        values = pd.to_numeric(df[column], errors="raise")

        if values.isna().any():
            raise ValueError(f"Missing {column}")

        if (values % 1 != 0).any():
            raise ValueError(f"Non-integer values in {column}")

        if column.endswith("awards") and (values < 0).any():
            raise ValueError(f"Negative values in {column}")

    if (
        df["male_awards"] + df["female_awards"]
        != df["total_awards"]
    ).any():
        raise ValueError("Award counts do not reconcile")


def validate_program_totals(programs, totals):
    """Check program-level sums against reported award totals."""
    sums = (
        programs.groupby(["school_id", "award_level"])["total_awards"]
        .sum()
        .rename("program_sum")
    )

    reported = totals.set_index(
        ["school_id", "award_level"]
    )["total_awards"]

    if not sums.index.equals(reported.index):
        sums = sums.sort_index()
        reported = reported.sort_index()

    if not sums.index.equals(reported.index):
        raise ValueError("Program and total award keys differ")

    if not sums.eq(reported).all():
        raise ValueError("Program award totals do not reconcile")


def load_to_postgres(programs, totals):
    """Refresh both tables in one PostgreSQL transaction."""
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        raise ValueError("EDATLAS_DATABASE_URL is missing")

    validate_data(
        programs,
        PROGRAM_COLUMNS,
        ["school_id", "cip_code", "award_level"],
    )

    validate_data(
        totals,
        COMMON_COLUMNS,
        ["school_id", "award_level"],
    )

    validate_program_totals(programs, totals)

    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM public.ipeds_completions_programs_2024"
                )
            )
            connection.execute(
                text(
                    "DELETE FROM public.ipeds_completions_totals_2024"
                )
            )

            programs.to_sql(
                PROGRAM_TABLE,
                con=connection,
                schema="public",
                if_exists="append",
                index=False,
                chunksize=2000,
            )

            totals.to_sql(
                TOTAL_TABLE,
                con=connection,
                schema="public",
                if_exists="append",
                index=False,
                chunksize=2000,
            )

            program_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM "
                    "public.ipeds_completions_programs_2024"
                )
            ).scalar_one()

            total_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM "
                    "public.ipeds_completions_totals_2024"
                )
            ).scalar_one()

            if program_count != len(programs):
                raise ValueError("Program record count mismatch")

            if total_count != len(totals):
                raise ValueError("Total record count mismatch")

        print(f"Loaded {program_count} program records")
        print(f"Loaded {total_count} institution-award totals")

    finally:
        engine.dispose()


def main():
    programs, totals = read_data()
    load_to_postgres(programs, totals)


if __name__ == "__main__":
    main()
