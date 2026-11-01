
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_PATH = (
    PROJECT_ROOT / "data" / "raw" / "ipeds" / "EF2024A.zip"
)

OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed"
    / "ipeds_enrollment_2024.csv"
)

COLUMNS = [
    "UNITID",
    "EFALEVEL",
    "LINE",
    "SECTION",
    "LSTUDY",
    "XEFTOTLT",
    "EFTOTLT",
    "EFTOTLM",
    "EFTOTLW",
]


def load_enrollment_data():
    """Read IPEDS Fall Enrollment 2024."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"IPEDS enrollment file not found: {INPUT_PATH}"
        )

    return pd.read_csv(
        INPUT_PATH,
        encoding="utf-8-sig",
        usecols=COLUMNS,
    )


def transform_enrollment_data(df):
    """Create one total-enrollment record per institution."""

    selected = df.loc[
        (df["EFALEVEL"] == 1)
        & (df["LINE"] == 29)
        & (df["SECTION"] == 3)
        & (df["LSTUDY"] == 4)
    ].copy()

    if selected.empty:
        raise ValueError("No total-enrollment records found")

    selected = selected.rename(
        columns={
            "UNITID": "school_id",
            "EFTOTLT": "total_enrollment",
            "EFTOTLM": "male_enrollment",
            "EFTOTLW": "female_enrollment",
            "XEFTOTLT": "reporting_flag",
        }
    )

    selected = selected[
        [
            "school_id",
            "total_enrollment",
            "male_enrollment",
            "female_enrollment",
            "reporting_flag",
        ]
    ]

    numeric_columns = [
        "school_id",
        "total_enrollment",
        "male_enrollment",
        "female_enrollment",
    ]

    for column in numeric_columns:
        selected[column] = pd.to_numeric(
            selected[column],
            errors="raise",
        )

    if selected[numeric_columns].isna().any().any():
        raise ValueError("Missing school ID or enrollment count")

    if selected["school_id"].duplicated().any():
        raise ValueError("Duplicate institution IDs found")

    enrollment_columns = [
        "total_enrollment",
        "male_enrollment",
        "female_enrollment",
    ]

    if selected[enrollment_columns].lt(0).any().any():
        raise ValueError("Negative enrollment count found")

    if (
        selected["male_enrollment"]
        + selected["female_enrollment"]
        != selected["total_enrollment"]
    ).any():
        raise ValueError("Enrollment totals do not reconcile")

    selected[numeric_columns] = (
        selected[numeric_columns].astype("int64")
    )

    return selected.sort_values(
        "school_id"
    ).reset_index(drop=True)


def main():
    raw = load_enrollment_data()

    cleaned = transform_enrollment_data(raw)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cleaned.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Raw rows: {len(raw)}")
    print(f"Processed institutions: {len(cleaned)}")
    print(
        f"Total enrollment: "
        f"{cleaned['total_enrollment'].sum()}"
    )
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
