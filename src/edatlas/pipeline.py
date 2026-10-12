import os
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

from edatlas.ingestion.college_scorecard import (
    fetch_college_data,
    save_raw_data,
)

from edatlas.transformation.college_scorecard_transform import (
    load_raw_data,
    transform_data,
    save_processed_data,
)

from edatlas.transformation.college_scorecard_curate import (
    curate_data,
    save_curated_data,
)

from edatlas.quality.college_scorecard_quality import (
    validate_required_fields,
    validate_unique_school_ids,
    validate_numeric_ranges,
)

from edatlas.loading.college_scorecard_load import (
    load_to_postgres,
)


def run_pipeline():
    logger.info("Starting EdAtlas ETL Pipeline")

    # Stage 1: Ingestion
    logger.info("\n[1/5] Extracting College Scorecard data...")

    use_local_data = os.getenv("EDATLAS_USE_LOCAL_DATA") == "1"

    if use_local_data:
        print("Using existing local JSON data...")
        raw_data = load_raw_data()
    else:
        if not os.getenv("COLLEGE_SCORECARD_API_KEY"):
            raise ValueError("COLLEGE_SCORECARD_API_KEY is missing")

        raw_data = fetch_college_data()
    record_count = len(raw_data["results"])

    logger.info("Records retrieved: %s", record_count)

    if record_count < 6000:
        raise ValueError(
            f"Unexpectedly low record count: {record_count}. "
            "Pipeline stopped to prevent incomplete loading."
        )

    # Stage 2: Transformation
    logger.info("[2/5] Transforming data...")

    processed_df = transform_data(raw_data)

    if processed_df.empty:
        raise ValueError("Transformation produced no records")

    # Stage 3: Curation
    logger.info("\n[3/5] Curating data...")

    curated_df = curate_data(processed_df)

    # Stage 4: Data quality
    logger.info("\n[4/5] Validating curated data...")

    errors = (
        validate_required_fields(curated_df)
        + validate_unique_school_ids(curated_df)
    )

    numeric_errors, warnings = validate_numeric_ranges(
        curated_df
    )

    errors += numeric_errors

    logger.info(
        "Validation completed: %s errors, %s warnings",
        errors,
        warnings,
    )

    if errors > 0:
        raise ValueError(
            "Data quality checks failed. Pipeline stopped."
        )

    # Save files only after successful validation
    print("\nSaving validated datasets...")

    if not use_local_data:
        save_raw_data(raw_data)
    save_processed_data(processed_df)
    save_curated_data(curated_df)

    # Stage 5: PostgreSQL
    logger.info("\n[5/5] Loading PostgreSQL...")

    load_to_postgres(curated_df)

    logger.info("EdAtlas ETL Pipeline Completed Successfully!")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception:
        logger.exception("EdAtlas ETL Pipeline Failed")
        raise