
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


@pytest.fixture
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


def test_enrollment_table_has_records(db_connection):
    total = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM public.ipeds_enrollment_2024
        """)
    ).scalar_one()

    assert total > 0


def test_enrollment_school_ids_are_unique(db_connection):
    total, unique = db_connection.execute(
        text("""
            SELECT
                COUNT(*),
                COUNT(DISTINCT school_id)
            FROM public.ipeds_enrollment_2024
        """)
    ).one()

    assert total == unique


def test_enrollment_counts_reconcile(db_connection):
    mismatches = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM public.ipeds_enrollment_2024
            WHERE male_enrollment + female_enrollment
                  <> total_enrollment
        """)
    ).scalar_one()

    assert mismatches == 0


def test_enrollment_institutions_match_ipeds(db_connection):
    unmatched = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM public.ipeds_enrollment_2024 e
            LEFT JOIN public.ipeds_institutions ip
                ON e.school_id = ip.school_id
            WHERE ip.school_id IS NULL
        """)
    ).scalar_one()

    assert unmatched == 0


def test_three_table_join(db_connection):
    matched = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM public.college_scorecard cs
            INNER JOIN public.ipeds_institutions ip
                ON cs.school_id = ip.school_id
            INNER JOIN public.ipeds_enrollment_2024 e
                ON ip.school_id = e.school_id
        """)
    ).scalar_one()

    assert matched > 0
