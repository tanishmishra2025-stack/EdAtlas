
import pandas as pd
import pytest

from edatlas.ingestion.bls_oews import transform_bls_data


def sample_bls():
    return pd.DataFrame({
        "PRIM_STATE": ["IL", "IL", "CA"],
        "AREA_TITLE": ["Illinois", "Illinois", "California"],
        "AREA_TYPE": [2, 2, 2],
        "OCC_CODE": ["15-1252", "00-0000", "15-1252"],
        "OCC_TITLE": [
            "Software Developers",
            "All Occupations",
            "Software Developers",
        ],
        "O_GROUP": ["detailed", "total", "detailed"],
        "TOT_EMP": [80000, 5000000, "**"],
        "A_MEAN": [125000, 70000, "#"],
        "A_MEDIAN": [120000, 60000, "*"],
        "H_MEAN": [60.10, 33.65, "#"],
        "H_MEDIAN": [57.70, 28.85, "*"],
    })


def test_detailed_occupations_only():
    result = transform_bls_data(sample_bls())

    assert len(result) == 2
    assert result["occupation_code"].eq("15-1252").all()


def test_state_occupation_keys():
    result = transform_bls_data(sample_bls())

    assert result["state"].nunique() == 2
    assert result.duplicated(
        ["state", "occupation_code"]
    ).sum() == 0


def test_suppressed_employment():
    result = transform_bls_data(sample_bls())

    ca = result[result["state"] == "CA"].iloc[0]

    assert pd.isna(ca["employment"])
    assert ca["employment_flag"] == "**"


def test_top_coded_wages():
    result = transform_bls_data(sample_bls())

    ca = result[result["state"] == "CA"].iloc[0]

    assert pd.isna(ca["annual_mean_wage"])
    assert ca["annual_mean_wage_flag"] == "#"


def test_unavailable_wage():
    result = transform_bls_data(sample_bls())

    ca = result[result["state"] == "CA"].iloc[0]

    assert pd.isna(ca["annual_median_wage"])
    assert ca["annual_median_wage_flag"] == "*"


def test_duplicate_keys_rejected():
    df = sample_bls()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="Duplicate"):
        transform_bls_data(df)


def test_negative_employment_rejected():
    df = sample_bls()
    df.loc[0, "TOT_EMP"] = -100

    with pytest.raises(ValueError, match="Negative"):
        transform_bls_data(df)


def test_unexpected_text_rejected():
    df = sample_bls()
    df.loc[0, "A_MEAN"] = "unknown"

    with pytest.raises(ValueError, match="Unexpected"):
        transform_bls_data(df)


def test_original_dataframe_unchanged():
    df = sample_bls()
    original = df.copy(deep=True)

    transform_bls_data(df)

    pd.testing.assert_frame_equal(df, original)
