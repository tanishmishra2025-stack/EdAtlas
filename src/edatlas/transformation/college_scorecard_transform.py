import json
from pathlib import Path

import pandas as pd


def load_raw_data():
    project_root = Path(__file__).resolve().parents[3]

    input_path = (
        project_root
        / "data"
        / "raw"
        / "college_scorecard_raw.json"
    )

    with open(input_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def transform_data(data):
    records = data["results"]

    df = pd.DataFrame(records)

    # Rename raw API fields to cleaner column names
    df = df.rename(
        columns={
            "id": "school_id",
            "school.name": "school_name",
            "school.city": "city",
            "school.state": "state",
            "school.zip": "zip_code",
            "school.ownership": "ownership",
            "school.locale": "locale",
            "location.lat": "latitude",
            "location.lon": "longitude",
            "latest.student.size": "student_size",
            "latest.admissions.admission_rate.overall": "admission_rate",
            "latest.cost.avg_net_price.overall": "avg_net_price",
            "latest.completion.rate_suppressed.overall": "completion_rate",
            "latest.earnings.10_yrs_after_entry.median": "median_earnings_10yr",
        }
    )

    # Preserve ZIP codes as text
    df["zip_code"] = df["zip_code"].astype("string")

    # Nullable integer lets us keep missing student sizes without converting
    # the entire column to float.
    df["student_size"] = pd.to_numeric(
        df["student_size"],
        errors="coerce",
    ).astype("Int64")

    # Convert analytical fields to numeric values
    numeric_columns = [
        "admission_rate",
        "avg_net_price",
        "completion_rate",
        "median_earnings_10yr",
        "latitude",
        "longitude",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Ensure school IDs remain unique
    df = df.drop_duplicates(
        subset=["school_id"]
    )

    print("Cleaned columns:")
    print(df.columns.tolist())

    print("\nNull values:")
    print(df.isnull().sum())

    print("\nMissing value percentage:")
    print(
        (df.isnull().mean() * 100)
        .round(2)
    )

    print("\nData types:")
    print(df.dtypes)

    print("\nFirst 5 cleaned rows:")
    print(df.head())

    return df
def save_processed_data(df):
    project_root = Path(__file__).resolve().parents[3]

    output_path = (
        project_root
        / "data"
        / "processed"
        / "college_scorecard_processed.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        output_path,
        index=False,
    )

    print(f"\nProcessed data saved to: {output_path}")


def main():
    data = load_raw_data()

    df = transform_data(data)

    save_processed_data(df)


if __name__ == "__main__":
    main()