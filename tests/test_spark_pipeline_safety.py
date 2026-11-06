
"""Safety tests for the configuration-driven Spark pipeline."""

import pytest

from edatlas.processing import spark_pipeline_v2 as pipeline


def test_invalid_source_rejected_before_parquet_write(
    tmp_path, monkeypatch
):
    # Create an isolated test input.
    source = (
        tmp_path
        / "data/processed/ipeds_completions_programs_2024.csv"
    )
    source.parent.mkdir(parents=True)

    source.write_text(
        "school_id,cip_code,award_level,total_awards,"
        "male_awards,female_awards,reporting_flag\n"
        "1001,11.01,1,2,1,1,\n"
    )

    # Run the V2 pipeline against only our test dataset.
    monkeypatch.setattr(
        pipeline,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        pipeline,
        "DATASETS",
        [
            pipeline.DatasetConfig(
                name="ipeds_completions_programs_2024",
                source=(
                    "data/processed/"
                    "ipeds_completions_programs_2024.csv"
                ),
                schema=pipeline.IPEDS_COMPLETIONS_SCHEMA,
                expected_count=1,
            )
        ],
    )

    # The writer must never be called for invalid input.
    def forbidden_write(*args, **kwargs):
        raise AssertionError(
            "Parquet writer was called before validation passed"
        )

    monkeypatch.setattr(
        pipeline,
        "publish_parquet",
        forbidden_write,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IPEDS CIP codes",
    ):
        pipeline.main()
