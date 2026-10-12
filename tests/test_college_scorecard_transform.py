import pandas as pd

from edatlas.transformation.college_scorecard_transform import (
    transform_data,
)


def sample_data():
    return {
        "results": [
            {
                "id": 1001,
                "school.name": "Test University",
                "school.city": "Springfield",
                "school.state": "IL",
                "school.zip": "01234",
                "school.ownership": 1,
                "school.locale": 12,
                "location.lat": 39.78,
                "location.lon": -89.64,
                "latest.student.size": 5000,
                "latest.admissions.admission_rate.overall": 0.75,
                "latest.cost.avg_net_price.overall": 15000,
                "latest.completion.rate_suppressed.overall": 0.60,
                "latest.earnings.10_yrs_after_entry.median": 55000,
            }
        ]
    }


def test_column_renaming():
    df = transform_data(sample_data())

    assert "school_id" in df.columns
    assert "school_name" in df.columns
    assert "avg_net_price" in df.columns


def test_zip_code_preserved():
    df = transform_data(sample_data())

    assert df.iloc[0]["zip_code"] == "01234"


def test_admission_rate():
    df = transform_data(sample_data())

    assert df.iloc[0]["admission_rate"] == 0.75


def test_duplicate_school_ids_removed():
    data = sample_data()
    data["results"].append(data["results"][0].copy())

    df = transform_data(data)

    assert len(df) == 1
    assert df["school_id"].is_unique


def test_missing_student_size():
    data = sample_data()
    data["results"][0]["latest.student.size"] = None

    df = transform_data(data)

    assert pd.isna(df.iloc[0]["student_size"])
    assert str(df["student_size"].dtype) == "Int64"
