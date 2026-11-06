import pytest
from pyspark.sql import SparkSession

from edatlas.processing.spark_pipeline_v2 import publish_parquet


@pytest.fixture(scope="module")
def spark():
    return (
        SparkSession.builder
        .master("local[2]")
        .appName("EdAtlas-Publish-Tests")
        .getOrCreate()
    )


def test_successful_publish_replaces_output(spark, tmp_path):
    output = tmp_path / "dataset"

    first = spark.createDataFrame([(1,), (2,)], ["id"])
    publish_parquet(spark, first, output, expected_count=2)

    second = spark.createDataFrame([(1,), (2,), (3,)], ["id"])
    publish_parquet(spark, second, output, expected_count=3)

    assert spark.read.parquet(str(output)).count() == 3
    assert not (tmp_path / "dataset.tmp").exists()
    assert not (tmp_path / "dataset.old").exists()


def test_failed_publish_keeps_existing_output(spark, tmp_path):
    output = tmp_path / "dataset"

    good = spark.createDataFrame([(1,), (2,)], ["id"])
    publish_parquet(spark, good, output, expected_count=2)

    bad = spark.createDataFrame([(3,)], ["id"])
    with pytest.raises(ValueError):
        publish_parquet(spark, bad, output, expected_count=99)

    assert spark.read.parquet(str(output)).count() == 2
    assert not (tmp_path / "dataset.tmp").exists()
