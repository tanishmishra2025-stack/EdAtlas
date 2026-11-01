
import pandas as pd
import pytest

from edatlas.ingestion.ipeds_enrollment import (
    transform_enrollment_data,
)


def sample_enrollment():
    return pd.DataFrame({
        "UNITID": [100001, 100002],
        "EFALEVEL": [1, 1],
        "LINE": [29, 29],
        "SECTION": [3, 3],
        "LSTUDY": [4, 4],
        "XEFTOTLT": ["R", "R"],
        "EFTOTLT": [1000, 500],
        "EFTOTLM": [400, 200],
        "EFTOTLW": [600, 300],
    })


def test_valid_enrollment():
    result = transform_enrollment_data(sample_enrollment())

    assert len(result) == 2
    assert result["total_enrollment"].sum() == 1500


def test_column_renaming():
    result = transform_enrollment_data(sample_enrollment())

    assert "school_id" in result.columns
    assert "total_enrollment" in result.columns
    assert "reporting_flag" in result.columns


def test_duplicate_school_ids():
    df = sample_enrollment()
    df.loc[1, "UNITID"] = 100001

    with pytest.raises(ValueError, match="Duplicate"):
        transform_enrollment_data(df)


def test_negative_enrollment():
    df = sample_enrollment()
    df.loc[0, "EFTOTLT"] = -100

    with pytest.raises(ValueError, match="Negative"):
        transform_enrollment_data(df)


def test_enrollment_mismatch():
    df = sample_enrollment()
    df.loc[0, "EFTOTLM"] = 300

    with pytest.raises(ValueError, match="reconcile"):
        transform_enrollment_data(df)


def test_non_total_rows_excluded():
    df = sample_enrollment()
    df.loc[1, "EFALEVEL"] = 2

    result = transform_enrollment_data(df)

    assert len(result) == 1
    assert result.iloc[0]["school_id"] == 100001


def test_original_dataframe_unchanged():
    df = sample_enrollment()
    original = df.copy(deep=True)

    transform_enrollment_data(df)

    pd.testing.assert_frame_equal(df, original)
