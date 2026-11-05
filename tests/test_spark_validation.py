
"""Tests for EdAtlas Spark data-quality validation."""

import pytest

from pyspark.sql import SparkSession

from edatlas.processing.spark_validation import validate_dataset


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("EdAtlas-Validation-Tests")
        .getOrCreate()
    )

    yield session

    session.stop()


def test_valid_cip_codes(spark):
    df = spark.createDataFrame(
        [
            (1001, "11.0101"),
            (1002, "01.0999"),
        ],
        ["school_id", "cip_code"],
    )

    validate_dataset(
        "ipeds_completions_programs_2024",
        df,
    )


def test_invalid_cip_code_rejected(spark):
    df = spark.createDataFrame(
        [(1001, "11.01")],
        ["school_id", "cip_code"],
    )

    with pytest.raises(ValueError, match="Invalid IPEDS CIP codes"):
        validate_dataset(
            "ipeds_completions_programs_2024",
            df,
        )


def test_duplicate_institution_rejected(spark):
    df = spark.createDataFrame(
        [
            (1001, "IL"),
            (1001, "IL"),
        ],
        ["school_id", "state"],
    )

    with pytest.raises(ValueError, match="duplicate keys"):
        validate_dataset(
            "ipeds_institutions",
            df,
        )


def test_valid_institutions(spark):
    df = spark.createDataFrame(
        [
            (1001, "IL"),
            (1002, "NY"),
        ],
        ["school_id", "state"],
    )

    validate_dataset("ipeds_institutions", df)


def test_unknown_dataset_rejected(spark):
    df = spark.createDataFrame(
        [(1001,)],
        ["school_id"],
    )

    with pytest.raises(ValueError, match="Unknown dataset"):
        validate_dataset("unknown_dataset", df)
