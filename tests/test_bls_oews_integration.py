
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


@pytest.fixture(scope="module")
def db_connection():
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        pytest.skip("Database URL not configured")

    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.connect() as connection:
            yield connection
    finally:
        engine.dispose()


def test_bls_record_count(db_connection):
    count = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM public.bls_oews_state_2025
        """)
    ).scalar_one()

    assert count == 36168


def test_bls_geographic_coverage(db_connection):
    areas = db_connection.execute(
        text("""
            SELECT COUNT(DISTINCT state)
            FROM public.bls_oews_state_2025
        """)
    ).scalar_one()

    assert areas == 54


def test_bls_unique_occupation_keys(db_connection):
    duplicates = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM (
                SELECT reference_year, state, occupation_code
                FROM public.bls_oews_state_2025
                GROUP BY reference_year, state, occupation_code
                HAVING COUNT(*) > 1
            ) AS duplicate_keys
        """)
    ).scalar_one()

    assert duplicates == 0


def test_bls_missing_value_flags(db_connection):
    result = db_connection.execute(
        text("""
            SELECT
                COUNT(*) FILTER (
                    WHERE employment IS NULL
                      AND employment_flag = '**'
                ) AS suppressed_employment,
                COUNT(*) FILTER (
                    WHERE annual_mean_wage IS NULL
                      AND annual_mean_wage_flag = '#'
                ) AS top_coded_wages,
                COUNT(*) FILTER (
                    WHERE employment IS NULL
                      AND employment_flag IS NULL
                ) AS unflagged_missing_employment
            FROM public.bls_oews_state_2025
        """)
    ).one()

    assert result.suppressed_employment == 1318
    assert result.top_coded_wages == 92
    assert result.unflagged_missing_employment == 0


def test_bls_joins_with_scorecard_by_state(db_connection):
    matched_states = db_connection.execute(
        text("""
            SELECT COUNT(DISTINCT cs.state)
            FROM (
                SELECT DISTINCT state
                FROM public.college_scorecard
            ) AS cs
            INNER JOIN (
                SELECT DISTINCT state
                FROM public.bls_oews_state_2025
                WHERE area_type = 2
            ) AS bls
                ON cs.state = bls.state
        """)
    ).scalar_one()

    assert matched_states > 0
