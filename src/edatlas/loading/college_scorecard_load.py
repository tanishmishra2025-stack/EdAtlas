import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from edatlas.quality.college_scorecard_quality import (
    validate_required_fields,
    validate_unique_school_ids,
    validate_numeric_ranges,
)

load_dotenv()

DATABASE_URL = os.getenv("EDATLAS_DATABASE_URL")


def load_curated_data():
    project_root = Path(__file__).resolve().parents[3]

    input_path = (
            project_root
            / "data"
            / "curated"
            / "college_scorecard_curated.csv"
    )

    return pd.read_csv(
        input_path,
        dtype={"zip_code": "string"},
    )


def load_to_postgres(df):
    if not DATABASE_URL:
        raise ValueError(
            "EDATLAS_DATABASE_URL is missing. Check your .env file."
        )

    engine = create_engine(DATABASE_URL)

    try:
        with engine.begin() as connection:

            # Create a temporary staging table.
            df.to_sql(
                "college_scorecard_staging",
                connection,
                if_exists="replace",
                index=False,
            )

            # Verify that staging contains all records.
            staging_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM college_scorecard_staging"
                )
            ).scalar_one()

            if staging_count != len(df):
                raise ValueError(
                    "Staging row count does not match DataFrame"
                )

            # Refresh the existing table without dropping it.
            connection.execute(
                text("DELETE FROM college_scorecard")
            )
            # Get column names from the DataFrame.
            columns = list(df.columns)

            # Build an explicit column list for PostgreSQL.
            column_names = ", ".join(
                f'"{column}"' for column in columns
            )

            connection.execute(
                text(f"""
                    INSERT INTO college_scorecard ({column_names})
                    SELECT {column_names}
                    FROM college_scorecard_staging
                """)
            )
            # Remove the staging table.
            connection.execute(
                text("DROP TABLE college_scorecard_staging")
            )

            final_count = connection.execute(
                text("SELECT COUNT(*) FROM college_scorecard")
            ).scalar_one()

        print(
            f"Successfully loaded {final_count} records "
            "into college_scorecard"
        )

    finally:
        engine.dispose()


def main():
    df = load_curated_data()

    print("Validating curated data before PostgreSQL loading...")

    required_errors = validate_required_fields(df)
    duplicate_errors = validate_unique_school_ids(df)
    numeric_errors, warnings = validate_numeric_ranges(df)

    total_errors = (
            required_errors
            + duplicate_errors
            + numeric_errors
    )

    print(f"\nValidation errors: {total_errors}")
    print(f"Validation warnings: {warnings}")

    if total_errors > 0:
        raise ValueError(
            "Data quality checks failed. PostgreSQL load cancelled."
        )

    print("\nValidation passed. Loading data...")
    load_to_postgres(df)


if __name__ == "__main__":
    main()
