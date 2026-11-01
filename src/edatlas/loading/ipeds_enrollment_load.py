
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ipeds_enrollment_2024.csv"
)

EXPECTED_COLUMNS = [
    "school_id",
    "total_enrollment",
    "male_enrollment",
    "female_enrollment",
    "reporting_flag",
]


def load_enrollment_csv():
    """Read processed IPEDS enrollment data."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    return pd.read_csv(INPUT_PATH)


def load_enrollment_to_postgres(df):
    """Validate and transactionally refresh enrollment records."""
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        raise ValueError("EDATLAS_DATABASE_URL is not configured")

    if df.empty:
        raise ValueError("Cannot load an empty enrollment dataset")

    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError("Unexpected enrollment columns")

    if df["school_id"].isna().any():
        raise ValueError("Missing institution IDs")

    if df["school_id"].duplicated().any():
        raise ValueError("Duplicate institution IDs")

    numeric_columns = EXPECTED_COLUMNS[:4]

    for column in numeric_columns:
        values = pd.to_numeric(df[column], errors="raise")

        if values.isna().any():
            raise ValueError(f"Missing values in {column}")

        if (values < 0).any():
            raise ValueError(f"Negative values in {column}")

    if (
        df["male_enrollment"] + df["female_enrollment"]
        != df["total_enrollment"]
    ).any():
        raise ValueError("Enrollment counts do not reconcile")

    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.begin() as connection:
            # Keep the existing table schema and constraints.
            connection.execute(
                text("DELETE FROM public.ipeds_enrollment_2024")
            )

            df.to_sql(
                "ipeds_enrollment_2024",
                con=connection,
                schema="public",
                if_exists="append",
                index=False,
                chunksize=1000,
            )

            total = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM public.ipeds_enrollment_2024"
                )
            ).scalar_one()

            if total != len(df):
                raise ValueError(
                    f"Expected {len(df)} rows, found {total}"
                )

        print(f"Successfully loaded {total} enrollment records")

    finally:
        engine.dispose()


def main():
    df = load_enrollment_csv()
    load_enrollment_to_postgres(df)


if __name__ == "__main__":
    main()
