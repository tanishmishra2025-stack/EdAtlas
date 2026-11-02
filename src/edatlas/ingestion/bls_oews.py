
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_PATH = (
    PROJECT_ROOT / "data" / "raw"
    / "bls" / "oesm25st.zip"
)

OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed"
    / "bls_oews_state_2025.csv"
)

EXCEL_MEMBER = "oesm25st/state_M2025_dl.xlsx"

SOURCE_COLUMNS = [
    "PRIM_STATE",
    "AREA_TITLE",
    "AREA_TYPE",
    "OCC_CODE",
    "OCC_TITLE",
    "O_GROUP",
    "TOT_EMP",
    "A_MEAN",
    "A_MEDIAN",
    "H_MEAN",
    "H_MEDIAN",
]

MEASURES = {
    "TOT_EMP": "employment",
    "A_MEAN": "annual_mean_wage",
    "A_MEDIAN": "annual_median_wage",
    "H_MEAN": "hourly_mean_wage",
    "H_MEDIAN": "hourly_median_wage",
}

SPECIAL_CODES = {"*", "**", "#"}


def load_bls_data():
    """Read the BLS May 2025 workbook from its ZIP archive."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    with ZipFile(INPUT_PATH) as archive:
        workbook = archive.read(EXCEL_MEMBER)

    return pd.read_excel(
        BytesIO(workbook),
        sheet_name="state_M2025_dl",
        usecols=SOURCE_COLUMNS,
        dtype={
            "PRIM_STATE": "string",
            "OCC_CODE": "string",
        },
    )


def transform_bls_data(df):
    """Prepare one record per geographic area and occupation."""
    selected = df.loc[df["O_GROUP"].eq("detailed")].copy()

    if selected.empty:
        raise ValueError("No detailed occupations found")

    selected = selected.rename(
        columns={
            "PRIM_STATE": "state",
            "AREA_TITLE": "state_name",
            "AREA_TYPE": "area_type",
            "OCC_CODE": "occupation_code",
            "OCC_TITLE": "occupation_title",
        }
    )

    required = [
        "state",
        "state_name",
        "occupation_code",
        "occupation_title",
    ]

    if selected[required].isna().any().any():
        raise ValueError("Missing occupation identifiers")

    if selected.duplicated(
        ["state", "occupation_code"]
    ).any():
        raise ValueError("Duplicate state and occupation codes")

    selected["reference_year"] = 2025

    for source_column, target_column in MEASURES.items():
        raw_values = selected[source_column].astype("string").str.strip()

        # Preserve original suppression and top-coding symbols.
        selected[f"{target_column}_flag"] = raw_values.where(
            raw_values.isin(SPECIAL_CODES),
            other=pd.NA,
        )

        # Reject unexpected text instead of silently discarding it.
        numeric = pd.to_numeric(raw_values, errors="coerce")

        unexpected = (
            numeric.isna()
            & raw_values.notna()
            & ~raw_values.isin(SPECIAL_CODES)
        )

        if unexpected.any():
            raise ValueError(
                f"Unexpected values in {source_column}: "
                f"{raw_values[unexpected].unique().tolist()[:5]}"
            )

        if numeric.lt(0).any():
            raise ValueError(
                f"Negative estimates in {source_column}"
            )

        selected[target_column] = numeric

    # Employment estimates are counts, not fractional values.
    employment = selected["employment"].dropna()

    if (employment % 1 != 0).any():
        raise ValueError("Non-integer employment estimate")

    selected["employment"] = (
        selected["employment"].astype("Int64")
    )

    output_columns = [
        "reference_year",
        "state",
        "state_name",
        "area_type",
        "occupation_code",
        "occupation_title",
    ]

    for target_column in MEASURES.values():
        output_columns.extend(
            [target_column, f"{target_column}_flag"]
        )

    return (
        selected[output_columns]
        .sort_values(["state", "occupation_code"])
        .reset_index(drop=True)
    )


def main():
    raw = load_bls_data()
    cleaned = transform_bls_data(raw)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cleaned.to_csv(OUTPUT_PATH, index=False)

    print(f"Raw records: {len(raw)}")
    print(f"Detailed occupation records: {len(cleaned)}")
    print(f"Geographic areas: {cleaned['state'].nunique()}")
    print(
        "Missing employment estimates: "
        f"{cleaned['employment'].isna().sum()}"
    )
    print(
        "Top-coded annual mean wages: "
        f"{cleaned['annual_mean_wage_flag'].eq('#').sum()}"
    )
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
