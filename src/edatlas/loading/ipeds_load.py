import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ipeds_institutions.csv"
)


def load_ipeds_csv():
    """Read processed IPEDS institution data."""
    return pd.read_csv(INPUT_PATH)


def load_ipeds_to_postgres(df):
    """Refresh the IPEDS table inside a database transaction."""
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        raise ValueError("EDATLAS_DATABASE_URL is not configured")

    if df.empty:
        raise ValueError("Cannot load an empty IPEDS dataset")

    if df["school_id"].isna().any():
        raise ValueError("IPEDS contains missing school IDs")

    if df["school_id"].duplicated().any():
        raise ValueError("IPEDS contains duplicate school IDs")

    engine = create_engine(database_url)

    try:
        with engine.begin() as connection:
            # Preserve the destination table and its primary key.
            connection.execute(
                text("DELETE FROM public.ipeds_institutions")
            )

            df.to_sql(
                "ipeds_institutions",
                con=connection,
                schema="public",
                if_exists="append",
                index=False,
                chunksize=1000,
            )

            total = connection.execute(
                text("SELECT COUNT(*) FROM public.ipeds_institutions")
            ).scalar_one()

            if total != len(df):
                raise ValueError(
                    f"Expected {len(df)} rows, found {total}"
                )

        print(f"Successfully loaded {total} IPEDS records")

    finally:
        engine.dispose()


def main():
    df = load_ipeds_csv()
    load_ipeds_to_postgres(df)


if __name__ == "__main__":
    main()
