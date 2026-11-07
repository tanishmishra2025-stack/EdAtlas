import os

import pytest
from dotenv import load_dotenv

from edatlas.warehouse.build import build_warehouse, get_engine, run_checks

load_dotenv()

pytestmark = pytest.mark.skipif(
    not os.getenv("EDATLAS_DATABASE_URL"),
    reason="EDATLAS_DATABASE_URL is not configured",
)


@pytest.fixture(scope="module")
def engine():
    engine = get_engine()
    build_warehouse(engine)
    return engine


def scalar(engine, sql):
    with engine.connect() as connection:
        return connection.exec_driver_sql(sql).scalar_one()


def test_all_reconciliation_checks_pass(engine):
    assert run_checks(engine) == []


def test_build_is_repeatable(engine):
    build_warehouse(engine)
    assert run_checks(engine) == []


def test_every_institution_comes_from_a_source(engine):
    missing_source = scalar(
        engine,
        "SELECT COUNT(*) FROM dw.dim_institution "
        "WHERE NOT in_ipeds AND NOT in_scorecard",
    )
    assert missing_source == 0


def test_bls_suppression_flags_preserved(engine):
    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            "SELECT "
            "COUNT(*) FILTER (WHERE employment IS NULL), "
            "COUNT(*) FILTER (WHERE employment_flag = '**'), "
            "COUNT(*) FILTER (WHERE annual_mean_wage_flag = '#') "
            "FROM dw.fact_occupation_wages"
        ).one()

    assert tuple(row) == (1318, 1318, 92)


def test_cip_codes_remain_seven_character_strings(engine):
    bad_codes = scalar(
        engine,
        "SELECT COUNT(*) FROM dw.dim_cip WHERE length(cip_code) <> 7",
    )
    assert bad_codes == 0
