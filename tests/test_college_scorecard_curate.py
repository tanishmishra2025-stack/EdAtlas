
import pandas as pd
import pytest

from edatlas.transformation.college_scorecard_curate import (
    curate_data,
)


@pytest.fixture
def sample_processed_df():
    return pd.DataFrame([
        {
            "school_id": 1001,
            "school_name": "Test University",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "01234",
            "ownership": 1,
            "locale": 12,
            "student_size": 5000,
            "admission_rate": 0.75,
            "avg_net_price": 15000,
            "completion_rate": 0.60,
            "median_earnings_10yr": 55000,
            "latitude": 39.78,
            "longitude": -89.64,
        }
    ])


def test_curated_columns(sample_processed_df):
    curated_df = curate_data(sample_processed_df)

    assert len(curated_df.columns) == 16
    assert "admission_rate_pct" in curated_df.columns
    assert "completion_rate_pct" in curated_df.columns


def test_admission_percentage(sample_processed_df):
    curated_df = curate_data(sample_processed_df)

    assert curated_df.iloc[0]["admission_rate_pct"] == 75.0


def test_completion_percentage(sample_processed_df):
    curated_df = curate_data(sample_processed_df)

    assert curated_df.iloc[0]["completion_rate_pct"] == 60.0


def test_missing_admission_rate(sample_processed_df):
    sample_processed_df.loc[0, "admission_rate"] = None

    curated_df = curate_data(sample_processed_df)

    assert pd.isna(curated_df.iloc[0]["admission_rate_pct"])


def test_original_dataframe_not_modified(sample_processed_df):
    original_columns = sample_processed_df.columns.tolist()

    curate_data(sample_processed_df)

    assert sample_processed_df.columns.tolist() == original_columns
