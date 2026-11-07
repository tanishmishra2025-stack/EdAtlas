"""Structural tests for the EdAtlas Airflow DAG."""

import ast
from pathlib import Path

DAG_FILE = (
    Path(__file__).resolve().parents[1]
    / "dags"
    / "edatlas_full_refresh.py"
)

EXPECTED_TASKS = [
    "check_raw_files",
    "refresh_college_scorecard",
    "ingest_ipeds_institutions",
    "load_ipeds_institutions",
    "ingest_ipeds_enrollment",
    "load_ipeds_enrollment",
    "ingest_ipeds_completions",
    "load_ipeds_completions",
    "ingest_bls",
    "load_bls",
    "run_spark_pipeline",
    "build_warehouse",
]


def get_tree():
    return ast.parse(DAG_FILE.read_text(encoding="utf-8"))


def test_dag_file_exists():
    assert DAG_FILE.is_file()


def test_all_tasks_defined():
    tree = get_tree()

    task_ids = {
        node.value
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        for node in call.args
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    }

    task_ids.update(
        keyword.value.value
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        for keyword in call.keywords
        if keyword.arg == "task_id"
        and isinstance(keyword.value, ast.Constant)
        and isinstance(keyword.value.value, str)
    )

    assert set(EXPECTED_TASKS).issubset(task_ids)

def test_manual_schedule():
    tree = get_tree()
    schedule_values = [
        keyword.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "schedule"
    ]

    assert any(
        isinstance(value, ast.Constant)
        and value.value is None
        for value in schedule_values
    )


def test_warehouse_follows_spark():
    tree = get_tree()

    dependency_expressions = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.BinOp)
    ]

    def flatten_chain(node):
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, ast.RShift
        ):
            return flatten_chain(node.left) + flatten_chain(node.right)
        if isinstance(node, ast.Name):
            return [node.id]
        return []

    chains = [
        flatten_chain(expression)
        for expression in dependency_expressions
    ]

    assert any(
        "spark" in chain
        and "warehouse_build" in chain
        and chain.index("spark") < chain.index("warehouse_build")
        for chain in chains
    )
