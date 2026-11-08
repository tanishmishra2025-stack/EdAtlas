from pathlib import Path
"""Failure-safety tests for the EdAtlas Parquet writer."""

import shutil

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.readwriter import DataFrameWriter
from pyspark.sql.types import StructField, StructType, LongType

from edatlas.processing.spark_pipeline import process_csv_to_parquet


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .master("local[1]")
        .appName("EdAtlas-Parquet-Reliability-Test")
        .getOrCreate()
    )
    yield session
    session.stop()


def test_failed_write_preserves_existing_output(
    spark, tmp_path, monkeypatch
):
    source = tmp_path / "sample.csv"
    source.write_text("school_id\n1001\n", encoding="utf-8")

    published = tmp_path / "published"
    published.mkdir()

    marker = published / "existing_data.marker"
    marker.write_text("previous valid output", encoding="utf-8")

    schema = StructType([
        StructField("school_id", LongType(), False)
    ])

    def simulate_write_failure(writer, path, *args, **kwargs):
        if str(path) == str(published):
            shutil.rmtree(published)

        raise RuntimeError("Simulated Parquet write failure")

    monkeypatch.setattr(
        DataFrameWriter,
        "parquet",
        simulate_write_failure,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated Parquet write failure",
    ):
        process_csv_to_parquet(
            spark=spark,
            input_path=source,
            output_path=published,
            schema=schema,
            expected_count=1,
        )

    assert marker.exists(), (
        "Previously published Parquet output was lost"
    )
    assert marker.read_text(encoding="utf-8") == (
        "previous valid output"
    )


def test_successful_write_replaces_previous_output(spark, tmp_path):
    source = tmp_path / "sample.csv"
    source.write_text("school_id\n1001\n1002\n", encoding="utf-8")

    published = tmp_path / "published"
    published.mkdir()

    marker = published / "old_data.marker"
    marker.write_text("old dataset", encoding="utf-8")

    schema = StructType([
        StructField("school_id", LongType(), False)
    ])

    process_csv_to_parquet(
        spark=spark,
        input_path=source,
        output_path=published,
        schema=schema,
        expected_count=2,
    )

    result = spark.read.parquet(str(published))

    assert result.count() == 2
    assert sorted(
        row.school_id for row in result.collect()
    ) == [1001, 1002]

    assert not marker.exists()

    assert not list(tmp_path.glob(".published.staging-*"))
    assert not list(tmp_path.glob(".published.backup-*"))


def test_failed_promotion_restores_previous_output(
    spark, tmp_path, monkeypatch
):
    import os

    source = tmp_path / "sample.csv"
    source.write_text("school_id\n1001\n", encoding="utf-8")

    published = tmp_path / "published"
    published.mkdir()

    marker = published / "old_data.marker"
    marker.write_text("previous valid output", encoding="utf-8")

    schema = StructType([
        StructField("school_id", LongType(), False)
    ])

    original_replace = os.replace

    def simulate_promotion_failure(src, dst):
        src_path = Path(src)
        dst_path = Path(dst)

        if (
            src_path.name.startswith(".published.staging-")
            and dst_path == published
        ):
            raise OSError("Simulated publication failure")

        return original_replace(src, dst)

    monkeypatch.setattr(
        os,
        "replace",
        simulate_promotion_failure,
    )

    with pytest.raises(
        OSError,
        match="Simulated publication failure",
    ):
        process_csv_to_parquet(
            spark=spark,
            input_path=source,
            output_path=published,
            schema=schema,
            expected_count=1,
        )

    assert marker.exists()
    assert marker.read_text(encoding="utf-8") == (
        "previous valid output"
    )

    assert not list(tmp_path.glob(".published.staging-*"))
    assert not list(tmp_path.glob(".published.backup-*"))


def test_v2_failed_promotion_immediately_restores_previous_output(
    spark, tmp_path, monkeypatch
):
    from edatlas.processing.spark_pipeline_v2 import publish_parquet

    published = tmp_path / "published"
    published.mkdir()

    marker = published / "old_data.marker"
    marker.write_text("previous valid output", encoding="utf-8")

    schema = StructType([
        StructField("school_id", LongType(), False)
    ])
    df = spark.createDataFrame([(1001,)], schema=schema)

    original_rename = Path.rename

    def simulate_rename_failure(self, target):
        if self == tmp_path / "published.tmp" and Path(target) == published:
            raise OSError("Simulated V2 publication failure")
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", simulate_rename_failure)

    with pytest.raises(
        OSError,
        match="Simulated V2 publication failure",
    ):
        publish_parquet(
            spark=spark,
            df=df,
            output_path=published,
            expected_count=1,
        )

    assert marker.exists(), "Previous output was not restored"
    assert marker.read_text(encoding="utf-8") == "previous valid output"
    assert not (tmp_path / "published.old").exists()
