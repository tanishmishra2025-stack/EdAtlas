
"""Dataset-specific validation for EdAtlas Spark pipelines."""

from pyspark.sql import functions as F


def require_no_rows(df, condition, message):
    """Raise an error when any row violates a rule."""
    invalid_count = df.filter(condition).count()

    if invalid_count > 0:
        raise ValueError(
            f"{message}: {invalid_count} invalid rows"
        )


def require_unique_keys(df, columns, dataset_name):
    """Verify that a dataset has no duplicate business keys."""
    duplicate_count = (
        df.groupBy(*columns)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    if duplicate_count > 0:
        raise ValueError(
            f"{dataset_name}: {duplicate_count} duplicate keys"
        )


def validate_dataset(dataset_name, df):
    """Run the appropriate quality checks for a dataset."""

    if dataset_name == "bls_oews_state_2025":
        require_no_rows(
            df,
            F.col("reference_year").isNull()
            | F.col("state").isNull()
            | F.col("occupation_code").isNull(),
            "BLS missing required identifiers",
        )

        require_unique_keys(
            df,
            ["reference_year", "state", "occupation_code"],
            dataset_name,
        )

    elif dataset_name == "ipeds_completions_programs_2024":
        require_no_rows(
            df,
            F.col("cip_code").isNull()
            | ~F.col("cip_code").rlike(r"^[0-9]{2}\.[0-9]{4}$"),
            "Invalid IPEDS CIP codes",
        )

    elif dataset_name == "ipeds_enrollment_2024":
        require_no_rows(
            df,
            F.col("total_enrollment").isNull()
            | F.col("male_enrollment").isNull()
            | F.col("female_enrollment").isNull()
            | (
                F.col("total_enrollment")
                != F.col("male_enrollment")
                + F.col("female_enrollment")
            )
            | (F.col("total_enrollment") < 0),
            "Invalid IPEDS enrollment",
        )

    elif dataset_name == "ipeds_institutions":
        require_no_rows(
            df,
            F.col("school_id").isNull()
            | F.col("state").isNull(),
            "Invalid IPEDS institutions",
        )

        require_unique_keys(
            df,
            ["school_id"],
            dataset_name,
        )

    elif dataset_name == "ipeds_completions_totals_2024":
        require_no_rows(
            df,
            F.col("school_id").isNull()
            | F.col("award_level").isNull()
            | (F.col("total_awards") < 0)
            | (F.col("male_awards") < 0)
            | (F.col("female_awards") < 0),
            "Invalid IPEDS completion totals",
        )

        require_unique_keys(
            df,
            ["school_id", "award_level"],
            dataset_name,
        )

    elif dataset_name in (
        "college_scorecard_processed",
        "college_scorecard_curated",
    ):
        require_no_rows(
            df,
            F.col("school_id").isNull(),
            "Missing College Scorecard IDs",
        )

        require_unique_keys(
            df,
            ["school_id"],
            dataset_name,
        )

    else:
        raise ValueError(
            f"Unknown dataset: {dataset_name}"
        )

    print(f"{dataset_name}: VALIDATION PASSED")
