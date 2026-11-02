
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

INPUT_PATH = (
    PROJECT_ROOT / "data" / "processed"
    / "bls_oews_state_2025.csv"
)

TABLE_NAME = "bls_oews_state_2025"

MEASURE_COLUMNS = [
    "employment",
    "annual_mean_wage",
    "annual_median_wage",
    "hourly_mean_wage",
    "hourly_median_wage",
]

IDENTIFIER_COLUMNS = [
    "reference_year",
    "state",
    "state_name",
    "area_type",
    "occupation_code",
    "occupation_title",
]

EXPECTED_COLUMNS = IDENTIFIER_COLUMNS + [
    item
    for measure in MEASURE_COLUMNS
    for item in (measure, f"{measure}_flag")
]

ALLOWED_FLAGS = {
    "employment": {"**"},
    "annual_mean_wage": {"*", "#"},
    "annual_median_wage": {"*", "#"},
    "hourly_mean_wage": {"*", "#"},
    "hourly_median_wage": {"*", "#"},
}


def read_bls_csv():
    """Read the cleaned BLS OEWS dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    return pd.read_csv(
        INPUT_PATH,
        dtype={
            "state": "string",
            "occupation_code": "string",
        },
    )


def validate_bls_data(df):
    """Validate the cleaned data before loading."""
    if df.empty:
        raise ValueError("BLS dataset is empty")

    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError("Unexpected BLS dataset columns")

    if df[IDENTIFIER_COLUMNS].isna().any().any():
        raise ValueError("Missing BLS identifiers")

    keys = ["reference_year", "state", "occupation_code"]

    if df.duplicated(keys).any():
        raise ValueError("Duplicate BLS occupation keys")

    if not df["reference_year"].eq(2025).all():
        raise ValueError("Unexpected BLS reference year")

    if not df["area_type"].isin([2, 3]).all():
        raise ValueError("Unexpected geographic area type")

    for column in MEASURE_COLUMNS:
        numeric = pd.to_numeric(df[column], errors="raise")

        if numeric.lt(0).any():
            raise ValueError(f"Negative values in {column}")

        flag_column = f"{column}_flag"
        flags = df[flag_column].dropna()

        if not flags.isin(ALLOWED_FLAGS[column]).all():
            raise ValueError(f"Unexpected flags in {flag_column}")

        if (numeric.notna() & df[flag_column].notna()).any():
            raise ValueError(
                f"Numeric values and flags conflict in {column}"
            )

        if (numeric.isna() & df[flag_column].isna()).any():
            raise ValueError(
                f"Missing value without a flag in {column}"
            )

    employment = pd.to_numeric(
        df["employment"], errors="raise"
    ).dropna()

    if (employment % 1 != 0).any():
        raise ValueError("Fractional employment estimates")


def load_bls_to_postgres(df):
    """Refresh BLS records in a single database transaction."""
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        raise ValueError("EDATLAS_DATABASE_URL is not configured")

    validate_bls_data(df)

    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.begin() as connection:
            # Preserve the existing table and its constraints.
            connection.execute(
                text("DELETE FROM public.bls_oews_state_2025")
            )

            df.to_sql(
                TABLE_NAME,
                con=connection,
                schema="public",
                if_exists="append",
                index=False,
                chunksize=1000,
            )

            count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM public.bls_oews_state_2025"
                )
            ).scalar_one()

            if count != len(df):
                raise ValueError(
                    f"Expected {len(df)} records, found {count}"
                )

        print(f"Successfully loaded {count} BLS records")

    finally:
        engine.dispose()


def main():
    df = read_bls_csv()
    load_bls_to_postgres(df)


if __name__ == "__main__":
    main()
