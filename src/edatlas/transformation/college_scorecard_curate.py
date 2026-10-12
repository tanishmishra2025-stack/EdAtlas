from pathlib import Path

import pandas as pd


def load_processed_data():
    project_root = Path(__file__).resolve().parents[3]

    input_path = (
        project_root
        / "data"
        / "processed"
        / "college_scorecard_processed.csv"
    )

    return pd.read_csv(input_path)


def curate_data(df):
    selected_columns = [
        "school_id",
        "school_name",
        "city",
        "state",
        "zip_code",
        "ownership",
        "locale",
        "student_size",
        "admission_rate",
        "avg_net_price",
        "completion_rate",
        "median_earnings_10yr",
        "latitude",
        "longitude",
    ]

    curated_df = df[selected_columns].copy()

    curated_df["admission_rate_pct"] = (
        curated_df["admission_rate"] * 100
    ).round(2)

    curated_df["completion_rate_pct"] = (
        curated_df["completion_rate"] * 100
    ).round(2)

    return curated_df


def save_curated_data(df):
    project_root = Path(__file__).resolve().parents[3]

    output_path = (
        project_root
        / "data"
        / "curated"
        / "college_scorecard_curated.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        output_path,
        index=False,
    )

    print(f"Curated data saved to: {output_path}")


def main():
    df = load_processed_data()

    curated_df = curate_data(df)

    print("Curated columns:")
    print(curated_df.columns.tolist())

    print("\nFirst 5 curated rows:")
    print(curated_df.head())

    save_curated_data(curated_df)


if __name__ == "__main__":
    main()