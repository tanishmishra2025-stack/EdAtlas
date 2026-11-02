
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_PATH = (
    PROJECT_ROOT / "data" / "raw" / "ipeds" / "C2024_A.zip"
)

PROGRAM_OUTPUT = (
    PROJECT_ROOT / "data" / "processed"
    / "ipeds_completions_programs_2024.csv"
)

TOTAL_OUTPUT = (
    PROJECT_ROOT / "data" / "processed"
    / "ipeds_completions_totals_2024.csv"
)

SOURCE_COLUMNS = [
    "UNITID",
    "CIPCODE",
    "MAJORNUM",
    "AWLEVEL",
    "CTOTALT",
    "CTOTALM",
    "CTOTALW",
    "XCTOTALT",
]


def load_completions_data():
    """Read the main IPEDS Completions 2024 dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    with ZipFile(INPUT_PATH) as archive:
        with archive.open("c2024_a.csv") as file:
            return pd.read_csv(
                file,
                encoding="utf-8-sig",
                usecols=SOURCE_COLUMNS,
                dtype={"CIPCODE": "string"},
            )


def transform_completions_data(df):
    """Create program-level and award-level completion datasets."""
    primary = df.loc[df["MAJORNUM"].eq(1)].copy()

    primary = primary.rename(columns={
        "UNITID": "school_id",
        "CIPCODE": "cip_code",
        "AWLEVEL": "award_level",
        "CTOTALT": "total_awards",
        "CTOTALM": "male_awards",
        "CTOTALW": "female_awards",
        "XCTOTALT": "reporting_flag",
    })

    primary = primary[
        [
            "school_id",
            "cip_code",
            "award_level",
            "total_awards",
            "male_awards",
            "female_awards",
            "reporting_flag",
        ]
    ]

    if primary.empty:
        raise ValueError("No primary-major completion records")

    numeric_columns = [
        "school_id",
        "award_level",
        "total_awards",
        "male_awards",
        "female_awards",
    ]

    for column in numeric_columns:
        primary[column] = pd.to_numeric(
            primary[column],
            errors="raise",
        )

    if primary[numeric_columns].isna().any().any():
        raise ValueError("Missing required numeric values")

    if primary[
        ["total_awards", "male_awards", "female_awards"]
    ].lt(0).any().any():
        raise ValueError("Negative completion counts")

    if (
        primary["male_awards"] + primary["female_awards"]
        != primary["total_awards"]
    ).any():
        raise ValueError("Completion counts do not reconcile")

    primary[numeric_columns] = primary[
        numeric_columns
    ].astype("int64")

    if primary[
        ["school_id", "cip_code", "award_level"]
    ].duplicated().any():
        raise ValueError("Duplicate completion records")

    totals = primary.loc[
        primary["cip_code"].eq("99")
    ].copy()

    programs = primary.loc[
        primary["cip_code"].ne("99")
    ].copy()

    # Verify detailed program sums against source totals.
    program_sums = programs.groupby(
        ["school_id", "award_level"],
        as_index=False,
    )["total_awards"].sum()

    comparison = totals.merge(
        program_sums,
        on=["school_id", "award_level"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_program_sum"),
    )

    if comparison["total_awards_program_sum"].isna().any():
        raise ValueError("Missing program-level records")

    if (
        comparison["total_awards"]
        != comparison["total_awards_program_sum"]
    ).any():
        raise ValueError("Program totals do not reconcile")

    programs = programs.sort_values(
        ["school_id", "cip_code", "award_level"]
    ).reset_index(drop=True)

    totals = totals.drop(columns=["cip_code"]).sort_values(
        ["school_id", "award_level"]
    ).reset_index(drop=True)

    return programs, totals


def main():
    raw = load_completions_data()

    programs, totals = transform_completions_data(raw)

    PROGRAM_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    programs.to_csv(PROGRAM_OUTPUT, index=False)
    totals.to_csv(TOTAL_OUTPUT, index=False)

    print(f"Raw records: {len(raw)}")
    print(f"Program records: {len(programs)}")
    print(f"Institution-award totals: {len(totals)}")
    print(f"Institutions: {totals['school_id'].nunique()}")
    print(f"Saved programs to: {PROGRAM_OUTPUT}")
    print(f"Saved totals to: {TOTAL_OUTPUT}")


if __name__ == "__main__":
    main()
