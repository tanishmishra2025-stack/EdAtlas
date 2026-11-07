"""Manual EdAtlas source refresh and Spark processing."""

from datetime import timedelta

import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT = "/home/tanish_mishra/EdAtlas-git"
PYTHON = f"{PROJECT}/.venv/bin/python"


def run_module(task_id, module, prefix=""):
    return BashOperator(
        task_id=task_id,
        bash_command=f"{prefix}{PYTHON} -m {module}",
        cwd=PROJECT,
        execution_timeout=timedelta(minutes=45),
        retries=0,
    )


with DAG(
    dag_id="edatlas_full_refresh",
    description="Refresh EdAtlas sources and process Parquet",
    start_date=pendulum.datetime(2026, 11, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["edatlas", "etl", "manual-refresh"],
) as dag:

    check_raw_files = BashOperator(
        task_id="check_raw_files",
        cwd=PROJECT,
        bash_command=(
            "test -f data/raw/college_scorecard_raw.json && "
            "test -f data/raw/ipeds/HD2024.zip && "
            "test -f data/raw/ipeds/EF2024A.zip && "
            "test -f data/raw/ipeds/C2024_A.zip && "
            "test -f data/raw/bls/oesm25st.zip"
        ),
    )

    scorecard = run_module(
        "refresh_college_scorecard",
        "edatlas.pipeline",
        prefix="EDATLAS_USE_LOCAL_DATA=1 ",
    )

    ipeds = run_module(
        "ingest_ipeds_institutions",
        "edatlas.ingestion.ipeds",
    )
    ipeds_load = run_module(
        "load_ipeds_institutions",
        "edatlas.loading.ipeds_load",
    )

    enrollment = run_module(
        "ingest_ipeds_enrollment",
        "edatlas.ingestion.ipeds_enrollment",
    )
    enrollment_load = run_module(
        "load_ipeds_enrollment",
        "edatlas.loading.ipeds_enrollment_load",
    )

    completions = run_module(
        "ingest_ipeds_completions",
        "edatlas.ingestion.ipeds_completions",
    )
    completions_load = run_module(
        "load_ipeds_completions",
        "edatlas.loading.ipeds_completions_load",
    )

    bls = run_module(
        "ingest_bls",
        "edatlas.ingestion.bls_oews",
    )
    bls_load = run_module(
        "load_bls",
        "edatlas.loading.bls_oews_load",
    )

    spark = run_module(
        "run_spark_pipeline",
        "edatlas.processing.spark_pipeline_v2",
    )

    warehouse_build = run_module(
        "build_warehouse",
        "edatlas.warehouse.build",
    )

    (
        check_raw_files
        >> scorecard
        >> ipeds
        >> ipeds_load
        >> enrollment
        >> enrollment_load
        >> completions
        >> completions_load
        >> bls
        >> bls_load
        >> spark
	>> warehouse_build
    )
