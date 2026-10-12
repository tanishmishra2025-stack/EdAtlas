
from pathlib import Path

import pandas as pd


def load_curated_data():
    project_root = Path(__file__).resolve().parents[3]

    input_path = (
        project_root
        / "data"
        / "curated"
        / "college_scorecard_curated.csv"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Curated dataset not found: {input_path}"
        )

    return pd.read_csv(input_path)

def validate_required_fields(df):
    required_columns = [
        "school_id",
        "school_name",
        "state",
    ]

    errors = 0

    for column in required_columns:
        if column not in df.columns:
            print(f"ERROR: Missing column: {column}")
            errors += 1
            continue

        missing_count = (
            df[column].isna()
            | df[column].astype("string").str.strip().eq("").fillna(False)
        ).sum()

        print(f"{column}: {missing_count} missing values")
        errors += int(missing_count)

    return errors


def validate_unique_school_ids(df):
    if "school_id" not in df.columns:
        print("ERROR: Cannot check uniqueness without school_id")
        return 1

    duplicate_count = df["school_id"].duplicated().sum()

    print(f"Duplicate school IDs: {duplicate_count}")

    return int(duplicate_count)


def validate_numeric_ranges(df):
    numeric_columns = [
        "admission_rate",
        "completion_rate",
        "avg_net_price",
        "median_earnings_10yr",
    ]

    missing_columns = [
        column for column in numeric_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing numeric columns: {missing_columns}"
        )

    invalid_admission = (
        (df["admission_rate"] < 0)
        | (df["admission_rate"] > 1)
    ).sum()

    invalid_completion = (
        (df["completion_rate"] < 0)
        | (df["completion_rate"] > 1)
    ).sum()

    negative_prices = (df["avg_net_price"] < 0).sum()
    negative_earnings = (df["median_earnings_10yr"] < 0).sum()

    print(f"Invalid admission rates: {invalid_admission}")
    print(f"Invalid completion rates: {invalid_completion}")
    print(f"Negative net prices (warning): {negative_prices}")
    print(f"Negative earnings: {negative_earnings}")

    errors = (
        int(invalid_admission)
        + int(invalid_completion)
        + int(negative_earnings)
    )

    warnings = int(negative_prices)

    return errors, warnings


def main():
    df = load_curated_data()

    print("Running EdAtlas data quality checks...\n")
    print(f"Total records: {len(df)}\n")

    required_errors = validate_required_fields(df)
    duplicate_errors = validate_unique_school_ids(df)
    numeric_errors, warnings = validate_numeric_ranges(df)

    total_errors = (
        required_errors
        + duplicate_errors
        + numeric_errors
    )

    print("\n--- DATA QUALITY SUMMARY ---")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {warnings}")

    if total_errors > 0:
        raise ValueError(
            f"Data quality validation failed: {total_errors} errors"
        )

    print("Data quality validation PASSED")


if __name__ == "__main__":
    main()
