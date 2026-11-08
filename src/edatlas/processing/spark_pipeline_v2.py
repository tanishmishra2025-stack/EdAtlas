"""Configuration-driven Spark processing pipeline for EdAtlas."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType

from edatlas.processing.spark_pipeline import (
    PROJECT_ROOT,
    BLS_SCHEMA,
    IPEDS_COMPLETIONS_SCHEMA,
    IPEDS_ENROLLMENT_SCHEMA,
    IPEDS_INSTITUTIONS_SCHEMA,
    IPEDS_COMPLETIONS_TOTALS_SCHEMA,
    COLLEGE_SCORECARD_SCHEMA,
    COLLEGE_SCORECARD_CURATED_SCHEMA,
)
from edatlas.processing.spark_validation import validate_dataset


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    source: str
    schema: StructType
    expected_count: int


DATASETS = [
    DatasetConfig(
        "bls_oews_state_2025",
        "data/processed/bls_oews_state_2025.csv",
        BLS_SCHEMA,
        36168,
    ),
    DatasetConfig(
        "ipeds_completions_programs_2024",
        "data/processed/ipeds_completions_programs_2024.csv",
        IPEDS_COMPLETIONS_SCHEMA,
        267595,
    ),
    DatasetConfig(
        "ipeds_enrollment_2024",
        "data/processed/ipeds_enrollment_2024.csv",
        IPEDS_ENROLLMENT_SCHEMA,
        5842,
    ),
    DatasetConfig(
        "ipeds_institutions",
        "data/processed/ipeds_institutions.csv",
        IPEDS_INSTITUTIONS_SCHEMA,
        6072,
    ),
    DatasetConfig(
        "ipeds_completions_totals_2024",
        "data/processed/ipeds_completions_totals_2024.csv",
        IPEDS_COMPLETIONS_TOTALS_SCHEMA,
        19384,
    ),
    DatasetConfig(
        "college_scorecard_processed",
        "data/processed/college_scorecard_processed.csv",
        COLLEGE_SCORECARD_SCHEMA,
        6273,
    ),
    DatasetConfig(
        "college_scorecard_curated",
        "data/curated/college_scorecard_curated.csv",
        COLLEGE_SCORECARD_CURATED_SCHEMA,
        6273,
    ),
]


def publish_parquet(spark, df, output_path: Path, expected_count: int):
    """Write to a temp folder, verify it, then swap it into place."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = output_path.with_name(output_path.name + ".tmp")
    old_path = output_path.with_name(output_path.name + ".old")

    # Recover from a swap that was interrupted on a previous run.
    if old_path.exists() and not output_path.exists():
        old_path.rename(output_path)

    # Clean up leftovers from a previously failed run.
    for leftover in (tmp_path, old_path):
        if leftover.exists():
            shutil.rmtree(leftover)

    try:
        df.write.mode("errorifexists").parquet(str(tmp_path))

        check = spark.read.parquet(str(tmp_path))
        if check.count() != expected_count:
            raise ValueError("Parquet row count does not match source")

        written = [(f.name, f.dataType) for f in check.schema.fields]
        expected = [(f.name, f.dataType) for f in df.schema.fields]
        if written != expected:
            raise ValueError("Parquet schema mismatch")
    except Exception:
        shutil.rmtree(tmp_path, ignore_errors=True)
        raise  # the existing output is untouched

    # Swap: retain the old output until publication succeeds.
    previous_moved = False

    try:
        if output_path.exists():
            output_path.rename(old_path)
            previous_moved = True

        tmp_path.rename(output_path)

    except Exception:
        # Restore the previous output if promotion fails.
        if previous_moved:
            old_path.rename(output_path)

        raise

    finally:
        # Remove staged files left by a failed promotion.
        if tmp_path.exists():
            shutil.rmtree(tmp_path)

    # The new output is published; the backup is no longer needed.
    if old_path.exists():
        shutil.rmtree(old_path)


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("EdAtlas-Spark-V2")
        .getOrCreate()
    )

    try:
        for dataset in DATASETS:
            print(f"\nPROCESSING: {dataset.name}", flush=True)

            input_path = PROJECT_ROOT / dataset.source
            output_path = (
                PROJECT_ROOT
                / "data/processed/parquet_v2"
                / dataset.name
            )

            if not input_path.is_file():
                raise FileNotFoundError(input_path)

            source = (
                spark.read
                .option("header", True)
                .option("mode", "FAILFAST")
                .schema(dataset.schema)
                .csv(str(input_path))
                .cache()
            )

            try:
                source_count = source.count()
                if source_count != dataset.expected_count:
                    raise ValueError(
                        f"{dataset.name}: expected "
                        f"{dataset.expected_count} records, "
                        f"found {source_count}"
                    )

                validate_dataset(dataset.name, source)
                publish_parquet(
                    spark, source, output_path, dataset.expected_count
                )
                print(f"{dataset.name}: PUBLISHED ({source_count} rows)")
            finally:
                source.unpersist()

        print(f"\nALL {len(DATASETS)} DATASETS PUBLISHED SUCCESSFULLY")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
