"""EdAtlas orchestration: initial read-only validation DAG."""

import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT = "/home/tanish_mishra/EdAtlas-git"
PYTHON = f"{PROJECT}/.venv/bin/python"

with DAG(
    dag_id="edatlas_pipeline",
    description="Validate the EdAtlas project and dimensional warehouse",
    start_date=pendulum.datetime(2026, 11, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["edatlas", "data-engineering"],
) as dag:

    check_environment = BashOperator(
        task_id="check_environment",
        bash_command=f"{PYTHON} --version",
    )

    check_source_files = BashOperator(
        task_id="check_source_files",
        bash_command=(
            "test -f data/processed/bls_oews_state_2025.csv && "
            "test -f data/processed/ipeds_institutions.csv && "
            "test -f data/processed/ipeds_enrollment_2024.csv && "
            "test -f data/processed/ipeds_completions_programs_2024.csv && "
            "test -f data/processed/ipeds_completions_totals_2024.csv && "
            "test -f data/processed/college_scorecard_processed.csv && "
            "test -f data/curated/college_scorecard_curated.csv"
        ),
        cwd=PROJECT,
    )

    run_spark_pipeline = BashOperator(
        task_id="run_spark_pipeline",
        bash_command=(
            f"{PYTHON} -m "
            "edatlas.processing.spark_pipeline_v2"
        ),
        cwd=PROJECT,
        execution_timeout=__import__("datetime").timedelta(minutes=30),
    )

    validate_warehouse = BashOperator(
        task_id="validate_warehouse",
        bash_command=(
            f"{PYTHON} -c "
            "'from edatlas.warehouse.build import run_checks; "
            "failures = run_checks(); "
            "assert not failures, failures; "
            "print(\"Warehouse reconciliation passed\")'"
        ),
        cwd=PROJECT,
    )

    check_environment >> check_source_files >> run_spark_pipeline >> validate_warehouse
