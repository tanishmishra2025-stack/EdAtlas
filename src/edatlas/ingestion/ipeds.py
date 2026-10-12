from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

IPEDS_ZIP_PATH = (
    PROJECT_ROOT / "data" / "raw" / "ipeds" / "HD2024.zip"
)

IPEDS_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ipeds_institutions.csv"
)

IPEDS_COLUMNS = {
    "UNITID": "school_id",
    "INSTNM": "institution_name",
    "CITY": "city",
    "STABBR": "state",
    "CONTROL": "ownership",
    "ICLEVEL": "institution_level",
    "SECTOR": "sector",
    "LOCALE": "locale",
    "INSTSIZE": "institution_size_category",
    "HBCU": "hbcu_status",
    "LATITUDE": "latitude",
    "LONGITUD": "longitude",
}


def load_ipeds_data() -> pd.DataFrame:
    """Read IPEDS institutional data from the ZIP archive."""
    if not IPEDS_ZIP_PATH.exists():
        raise FileNotFoundError(
            f"IPEDS ZIP not found: {IPEDS_ZIP_PATH}"
        )

    return pd.read_csv(
        IPEDS_ZIP_PATH,
        encoding="utf-8-sig",
        usecols=list(IPEDS_COLUMNS),
        low_memory=False,
    )


def transform_ipeds_data(df: pd.DataFrame) -> pd.DataFrame:
    """Select, rename, and validate IPEDS institution fields."""
    cleaned = df.rename(columns=IPEDS_COLUMNS).copy()

    cleaned["school_id"] = pd.to_numeric(
        cleaned["school_id"], errors="raise"
    ).astype("int64")

    if cleaned["school_id"].isna().any():
        raise ValueError("IPEDS contains missing school IDs")

    if cleaned["school_id"].duplicated().any():
        raise ValueError("IPEDS contains duplicate school IDs")

    return cleaned


def save_ipeds_data(df: pd.DataFrame) -> None:
    """Save cleaned data without overwriting College Scorecard CSVs."""
    IPEDS_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    df.to_csv(IPEDS_OUTPUT_PATH, index=False)
    print(f"IPEDS data saved to: {IPEDS_OUTPUT_PATH}")


def main() -> None:
    raw = load_ipeds_data()
    cleaned = transform_ipeds_data(raw)
    save_ipeds_data(cleaned)

    print(f"IPEDS records processed: {len(cleaned)}")
    print(f"IPEDS columns: {list(cleaned.columns)}")


if __name__ == "__main__":
    main()
