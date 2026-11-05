
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    LongType,
    DecimalType,
    DoubleType,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

BLS_SCHEMA = StructType([
    StructField("reference_year", IntegerType(), False),
    StructField("state", StringType(), False),
    StructField("state_name", StringType(), False),
    StructField("area_type", IntegerType(), False),
    StructField("occupation_code", StringType(), False),
    StructField("occupation_title", StringType(), False),
    StructField("employment", LongType(), True),
    StructField("employment_flag", StringType(), True),
    StructField("annual_mean_wage", DecimalType(12, 2), True),
    StructField("annual_mean_wage_flag", StringType(), True),
    StructField("annual_median_wage", DecimalType(12, 2), True),
    StructField("annual_median_wage_flag", StringType(), True),
    StructField("hourly_mean_wage", DecimalType(10, 2), True),
    StructField("hourly_mean_wage_flag", StringType(), True),
    StructField("hourly_median_wage", DecimalType(10, 2), True),
    StructField("hourly_median_wage_flag", StringType(), True),
])

IPEDS_COMPLETIONS_SCHEMA = StructType([
    StructField("school_id", LongType(), False),
    StructField("cip_code", StringType(), False),
    StructField("award_level", IntegerType(), False),
    StructField("total_awards", LongType(), True),
    StructField("male_awards", LongType(), True),
    StructField("female_awards", LongType(), True),
    StructField("reporting_flag", StringType(), True),

])
IPEDS_ENROLLMENT_SCHEMA = StructType([
    StructField("school_id", LongType(), False),
    StructField("total_enrollment", LongType(), True),
    StructField("male_enrollment", LongType(), True),
    StructField("female_enrollment", LongType(), True),
    StructField("reporting_flag", StringType(), True),
])
IPEDS_INSTITUTIONS_SCHEMA = StructType([
    StructField("school_id", LongType(), False),
    StructField("institution_name", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("sector", IntegerType(), True),
    StructField("institution_level", IntegerType(), True),
    StructField("ownership", IntegerType(), True),
    StructField("hbcu_status", IntegerType(), True),
    StructField("locale", IntegerType(), True),
    StructField("institution_size_category", IntegerType(), True),
    StructField("longitude", DecimalType(12, 7), True),
    StructField("latitude", DecimalType(12, 7), True),
])



IPEDS_COMPLETIONS_TOTALS_SCHEMA = StructType([
    StructField("school_id", LongType(), False),
    StructField("award_level", IntegerType(), False),
    StructField("total_awards", LongType(), True),
    StructField("male_awards", LongType(), True),
    StructField("female_awards", LongType(), True),
    StructField("reporting_flag", StringType(), True),
])


COLLEGE_SCORECARD_SCHEMA = StructType([
    StructField("student_size", LongType(), True),
    StructField("admission_rate", DoubleType(), True),
    StructField("avg_net_price", DoubleType(), True),
    StructField("completion_rate", DoubleType(), True),
    StructField("median_earnings_10yr", DoubleType(), True),
    StructField("school_name", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("zip_code", StringType(), True),
    StructField("ownership", IntegerType(), True),
    StructField("locale", DoubleType(), True),
    StructField("school_id", LongType(), False),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
])


COLLEGE_SCORECARD_CURATED_SCHEMA = StructType([
    StructField("school_id", LongType(), False),
    StructField("school_name", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("zip_code", StringType(), True),
    StructField("ownership", IntegerType(), True),
    StructField("locale", DoubleType(), True),
    StructField("student_size", LongType(), True),
    StructField("admission_rate", DoubleType(), True),
    StructField("avg_net_price", DoubleType(), True),
    StructField("completion_rate", DoubleType(), True),
    StructField("median_earnings_10yr", DoubleType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("admission_rate_pct", DoubleType(), True),
    StructField("completion_rate_pct", DoubleType(), True),
])



def process_csv_to_parquet(
    spark,
    input_path,
    output_path,
    schema,
    expected_count=None,
):
    """Convert a CSV dataset to validated Parquet."""
    df = (
        spark.read
        .option("header", True)
        .option("mode", "FAILFAST")
        .schema(schema)
        .csv(str(input_path))
    )

    source_count = df.count()

    if expected_count is not None:
        if source_count != expected_count:
            raise ValueError(
                f"Expected {expected_count} rows, "
                f"found {source_count}"
            )

    df.write.mode("overwrite").parquet(str(output_path))

    result = spark.read.parquet(str(output_path))
    parquet_count = result.count()

    if parquet_count != source_count:
        raise ValueError(
            "Parquet row count does not match source"
        )

    if result.schema != df.schema:
        raise ValueError("Parquet schema mismatch")

    print(f"Source records: {source_count}")
    print(f"Parquet records: {parquet_count}")
    print(f"Columns: {len(result.columns)}")
    print("PARQUET VALIDATION PASSED")

    return result


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("EdAtlas-Spark-Pipeline")
        .getOrCreate()
    )

    try:
        input_path = (
            PROJECT_ROOT
            / "data/processed/bls_oews_state_2025.csv"
        )

        output_path = (
            PROJECT_ROOT
            / "data/processed/parquet/bls_oews_state_2025"
        )

        result = process_csv_to_parquet(
            spark=spark,
            input_path=input_path,
            output_path=output_path,
            schema=BLS_SCHEMA,
            expected_count=36168,
        )

        result.printSchema()


        ipeds_input = (
            PROJECT_ROOT
            / "data/processed/ipeds_completions_programs_2024.csv"
        )

        ipeds_output = (
            PROJECT_ROOT
            / "data/processed/parquet/ipeds_completions_programs_2024"
        )

        completions = process_csv_to_parquet(
            spark=spark,
            input_path=ipeds_input,
            output_path=ipeds_output,
            schema=IPEDS_COMPLETIONS_SCHEMA,
            expected_count=267595,
        )

        # Validate CIP identifiers after the Parquet round trip.
        from pyspark.sql import functions as F

        invalid_cip = completions.filter(
            ~F.col("cip_code").rlike(r"^[0-9]{2}\.[0-9]{4}$")
            | F.col("cip_code").isNull()
        ).count()

        if invalid_cip:
            raise ValueError(
                f"Found {invalid_cip} invalid CIP codes"
            )

        print("IPEDS CIP VALIDATION PASSED")



        enrollment_input = (
            PROJECT_ROOT
            / "data/processed/ipeds_enrollment_2024.csv"
        )

        enrollment_output = (
            PROJECT_ROOT
            / "data/processed/parquet/ipeds_enrollment_2024"
        )

        enrollment = process_csv_to_parquet(
            spark=spark,
            input_path=enrollment_input,
            output_path=enrollment_output,
            schema=IPEDS_ENROLLMENT_SCHEMA,
            expected_count=5842,
        )

        from pyspark.sql import functions as F

        invalid_enrollment = enrollment.filter(
            F.col("total_enrollment").isNull()
            | F.col("male_enrollment").isNull()
            | F.col("female_enrollment").isNull()
            | (
                F.col("total_enrollment")
                != F.col("male_enrollment")
                + F.col("female_enrollment")
            )
            | (F.col("total_enrollment") < 0)
        ).count()

        if invalid_enrollment:
            raise ValueError(
                f"Found {invalid_enrollment} invalid enrollment records"
            )

        print("IPEDS ENROLLMENT VALIDATION PASSED")
        institutions = process_csv_to_parquet(
            spark=spark,
            input_path=PROJECT_ROOT / "data/processed/ipeds_institutions.csv",
            output_path=PROJECT_ROOT / "data/processed/parquet/ipeds_institutions",
            schema=IPEDS_INSTITUTIONS_SCHEMA,
            expected_count=6072,
        )

        invalid_institutions = institutions.filter(
            F.col("school_id").isNull()
            | F.col("state").isNull()
        ).count()

        duplicate_institutions = (
            institutions.groupBy("school_id")
            .count()
            .filter(F.col("count") > 1)
            .count()
        )

        assert invalid_institutions == 0, (
            f"Invalid institutions: {invalid_institutions}"
        )
        assert duplicate_institutions == 0, (
            f"Duplicate institution IDs: {duplicate_institutions}"
        )

        print("IPEDS INSTITUTIONS VALIDATION PASSED")

        totals = process_csv_to_parquet(
            spark=spark,
            input_path=PROJECT_ROOT / "data/processed/ipeds_completions_totals_2024.csv",
            output_path=PROJECT_ROOT / "data/processed/parquet/ipeds_completions_totals_2024",
            schema=IPEDS_COMPLETIONS_TOTALS_SCHEMA,
            expected_count=19384,
        )

        invalid_totals = totals.filter(
            F.col("school_id").isNull()
            | F.col("award_level").isNull()
            | (F.col("total_awards") < 0)
            | (F.col("male_awards") < 0)
            | (F.col("female_awards") < 0)
        ).count()

        duplicate_totals = (
            totals.groupBy("school_id", "award_level")
            .count()
            .filter(F.col("count") > 1)
            .count()
        )

        assert invalid_totals == 0, (
            f"Invalid completion totals: {invalid_totals}"
        )
        assert duplicate_totals == 0, (
            f"Duplicate completion total keys: {duplicate_totals}"
        )

        print("IPEDS COMPLETIONS TOTALS VALIDATION PASSED")


        # College Scorecard: processed dataset
        scorecard = process_csv_to_parquet(
            spark=spark,
            input_path=PROJECT_ROOT / "data/processed/college_scorecard_processed.csv",
            output_path=PROJECT_ROOT / "data/processed/parquet/college_scorecard_processed",
            schema=COLLEGE_SCORECARD_SCHEMA,
            expected_count=6273,
        )

        invalid_scorecard = scorecard.filter(
            F.col("school_id").isNull()
        ).count()

        duplicate_scorecard = (
            scorecard.groupBy("school_id")
            .count()
            .filter(F.col("count") > 1)
            .count()
        )

        assert invalid_scorecard == 0, (
            f"Missing Scorecard IDs: {invalid_scorecard}"
        )
        assert duplicate_scorecard == 0, (
            f"Duplicate Scorecard IDs: {duplicate_scorecard}"
        )

        print("COLLEGE SCORECARD PROCESSED VALIDATION PASSED")

        # College Scorecard: curated dataset
        curated = process_csv_to_parquet(
            spark=spark,
            input_path=PROJECT_ROOT / "data/curated/college_scorecard_curated.csv",
            output_path=PROJECT_ROOT / "data/processed/parquet/college_scorecard_curated",
            schema=COLLEGE_SCORECARD_CURATED_SCHEMA,
            expected_count=6273,
        )

        invalid_curated = curated.filter(
            F.col("school_id").isNull()
        ).count()

        duplicate_curated = (
            curated.groupBy("school_id")
            .count()
            .filter(F.col("count") > 1)
            .count()
        )

        assert invalid_curated == 0, (
            f"Missing curated IDs: {invalid_curated}"
        )
        assert duplicate_curated == 0, (
            f"Duplicate curated IDs: {duplicate_curated}"
        )

        print("COLLEGE SCORECARD CURATED VALIDATION PASSED")


    finally:
        spark.stop()
if __name__ == "__main__":
    main()
