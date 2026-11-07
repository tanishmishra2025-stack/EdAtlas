"""Build and verify the EdAtlas dimensional warehouse (dw schema)."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUILD_SQL = PROJECT_ROOT / "sql" / "09_build_warehouse.sql"
CHECK_SQL = PROJECT_ROOT / "sql" / "10_check_warehouse.sql"


def get_engine():
    """Create a database engine from EDATLAS_DATABASE_URL."""
    load_dotenv()
    url = os.getenv("EDATLAS_DATABASE_URL")
    if not url:
        raise RuntimeError("EDATLAS_DATABASE_URL is not set")
    return create_engine(url)


def build_warehouse(engine=None):
    """Drop and rebuild the dw schema from the public source tables.

    The whole build runs in one transaction, so a failure leaves the
    previous warehouse untouched.
    """
    engine = engine or get_engine()
    sql = BUILD_SQL.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.exec_driver_sql(sql)


def run_checks(engine=None):
    """Run the reconciliation checks and return the failed ones.

    An empty list means every check passed.
    """
    engine = engine or get_engine()
    sql = CHECK_SQL.read_text(encoding="utf-8")

    # The first statement in the file is the pass/fail table.
    check_query = sql.split(";")[0]

    with engine.connect() as connection:
        rows = connection.exec_driver_sql(check_query).mappings().all()

    return [dict(row) for row in rows if not row["ok"]]


def main():
    engine = get_engine()

    print("Building warehouse...", flush=True)
    build_warehouse(engine)

    failures = run_checks(engine)
    if failures:
        for failure in failures:
            print(
                f"FAILED: {failure['check_name']} "
                f"(actual={failure['actual']}, "
                f"expected={failure['expected']})"
            )
        raise SystemExit(1)

    print("WAREHOUSE BUILT AND ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
