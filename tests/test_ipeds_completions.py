
import pandas as pd
import pytest

from edatlas.ingestion.ipeds_completions import (
    transform_completions_data,
)


def sample_completions():
    return pd.DataFrame({
        "UNITID": [100001, 100001, 100001, 100001],
        "CIPCODE": ["11.0101", "11.0201", "99", "11.0101"],
        "MAJORNUM": [1, 1, 1, 2],
        "AWLEVEL": [5, 5, 5, 5],
        "CTOTALT": [30, 20, 50, 5],
        "CTOTALM": [20, 10, 30, 3],
        "CTOTALW": [10, 10, 20, 2],
        "XCTOTALT": ["R", "R", "R", "R"],
    })


def test_valid_completions():
    programs, totals = transform_completions_data(
        sample_completions()
    )

    assert len(programs) == 2
    assert len(totals) == 1
    assert totals.iloc[0]["total_awards"] == 50


def test_second_major_excluded():
    programs, _ = transform_completions_data(
        sample_completions()
    )

    assert programs["total_awards"].sum() == 50


def test_cip_codes_preserved():
    programs, _ = transform_completions_data(
        sample_completions()
    )

    assert "11.0101" in programs["cip_code"].tolist()


def test_duplicate_records():
    df = sample_completions()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="Duplicate"):
        transform_completions_data(df)


def test_negative_completions():
    df = sample_completions()
    df.loc[0, "CTOTALT"] = -10

    with pytest.raises(ValueError, match="Negative"):
        transform_completions_data(df)


def test_gender_counts_reconcile():
    df = sample_completions()
    df.loc[0, "CTOTALM"] = 15

    with pytest.raises(ValueError, match="reconcile"):
        transform_completions_data(df)


def test_program_totals_reconcile():
    df = sample_completions()
    df.loc[2, "CTOTALT"] = 60
    df.loc[2, "CTOTALW"] = 30

    with pytest.raises(ValueError, match="Program totals"):
        transform_completions_data(df)


def test_original_dataframe_unchanged():
    df = sample_completions()
    original = df.copy(deep=True)

    transform_completions_data(df)

    pd.testing.assert_frame_equal(df, original)
