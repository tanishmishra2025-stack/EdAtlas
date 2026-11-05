
"""Configuration-driven Spark processing pipeline for EdAtlas."""

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
    process_csv_to_parquet,
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

            # Use a separate output folder while testing V2.
            output_path = (
                PROJECT_ROOT
                / "data/processed/parquet_v2"
                / dataset.name
            )

            if not input_path.is_file():
                raise FileNotFoundError(input_path)

                       # Read and validate the source before writing.
            source = (
                spark.read
                .option("header", True)
                .option("mode", "FAILFAST")
                .schema(dataset.schema)
                .csv(str(input_path))
            )

            source_count = source.count()

            if source_count != dataset.expected_count:
                raise ValueError(
                    f"{dataset.name}: expected "
                    f"{dataset.expected_count} records, "
                    f"found {source_count}"
                )

            validate_dataset(dataset.name, source)

            # Only write after source validation passes.
            result = process_csv_to_parquet(
                spark=spark,
                input_path=input_path,
                output_path=output_path,
                schema=dataset.schema,
                expected_count=dataset.expected_count,
            )

        print("\nALL 7 DATASETS VALIDATED SUCCESSFULLY")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
