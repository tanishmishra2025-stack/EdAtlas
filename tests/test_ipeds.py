import pandas as pd
import pytest

from edatlas.ingestion.ipeds import transform_ipeds_data


def make_sample_data():
    return pd.DataFrame(
        {
            "UNITID": [100654, 100663],
            "INSTNM": ["University A", "University B"],
            "STABBR": ["AL", "AL"],
            "CONTROL": [1, 1],
        }
    )


def test_school_id_renaming():
    result = transform_ipeds_data(make_sample_data())

    assert "school_id" in result.columns
    assert result["school_id"].tolist() == [100654, 100663]


def test_institution_name_renaming():
    result = transform_ipeds_data(make_sample_data())

    assert "institution_name" in result.columns


def test_duplicate_school_ids():
    data = make_sample_data()
    data.loc[1, "UNITID"] = 100654

    with pytest.raises(ValueError):
        transform_ipeds_data(data)


def test_missing_school_ids():
    data = make_sample_data()
    data.loc[1, "UNITID"] = None

    with pytest.raises((ValueError, TypeError)):
        transform_ipeds_data(data)


def test_original_dataframe_unchanged():
    data = make_sample_data()
    original = data.copy(deep=True)

    transform_ipeds_data(data)

    pd.testing.assert_frame_equal(data, original)
