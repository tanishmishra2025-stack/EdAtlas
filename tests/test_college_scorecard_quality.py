
import pandas as pd

from edatlas.quality.college_scorecard_quality import (
    validate_required_fields,
    validate_unique_school_ids,
    validate_numeric_ranges,
)


def sample_df():
    return pd.DataFrame([
        {
            "school_id": 1001,
            "school_name": "Test University",
            "state": "IL",
            "admission_rate": 0.75,
            "completion_rate": 0.60,
            "avg_net_price": 15000,
            "median_earnings_10yr": 55000,
        }
    ])


def test_valid_required_fields():
    df = sample_df()

    assert validate_required_fields(df) == 0


def test_missing_school_name():
    df = sample_df()
    df.loc[0, "school_name"] = None

    assert validate_required_fields(df) == 1


def test_duplicate_school_ids():
    df = sample_df()
    df = pd.concat([df, df], ignore_index=True)

    assert validate_unique_school_ids(df) == 1


def test_valid_numeric_ranges():
    df = sample_df()

    errors, warnings = validate_numeric_ranges(df)

    assert errors == 0
    assert warnings == 0


def test_invalid_admission_rate():
    df = sample_df()
    df.loc[0, "admission_rate"] = 1.5

    errors, warnings = validate_numeric_ranges(df)

    assert errors == 1
    assert warnings == 0


def test_negative_net_price_warning():
    df = sample_df()
    df.loc[0, "avg_net_price"] = -500

    errors, warnings = validate_numeric_ranges(df)

    assert errors == 0
    assert warnings == 1


def test_negative_earnings_error():
    df = sample_df()
    df.loc[0, "median_earnings_10yr"] = -1000

    errors, warnings = validate_numeric_ranges(df)

    assert errors == 1
    assert warnings == 0
