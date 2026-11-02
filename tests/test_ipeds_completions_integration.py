
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


@pytest.fixture(scope="module")
def db_connection():
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        pytest.skip("EDATLAS_DATABASE_URL is not configured")

    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.connect() as connection:
            yield connection
    finally:
        engine.dispose()


def test_program_record_count(db_connection):
    total = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM public.ipeds_completions_programs_2024
        """)
    ).scalar_one()

    assert total == 267595


def test_institution_award_total_count(db_connection):
    total = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM public.ipeds_completions_totals_2024
        """)
    ).scalar_one()

    assert total == 19384


def test_program_identifiers_are_unique(db_connection):
    duplicates = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM (
                SELECT school_id, cip_code, award_level
                FROM public.ipeds_completions_programs_2024
                GROUP BY school_id, cip_code, award_level
                HAVING COUNT(*) > 1
            ) AS duplicate_keys
        """)
    ).scalar_one()

    assert duplicates == 0


def test_program_awards_reconcile_with_totals(db_connection):
    discrepancies = db_connection.execute(
        text("""
            WITH program_sums AS (
                SELECT
                    school_id,
                    award_level,
                    SUM(total_awards) AS program_total
                FROM public.ipeds_completions_programs_2024
                GROUP BY school_id, award_level
            )
            SELECT COUNT(*)
            FROM public.ipeds_completions_totals_2024 t
            FULL OUTER JOIN program_sums p
              ON t.school_id = p.school_id
             AND t.award_level = p.award_level
            WHERE t.school_id IS NULL
               OR p.school_id IS NULL
               OR t.total_awards <> p.program_total
        """)
    ).scalar_one()

    assert discrepancies == 0


def test_institution_join(db_connection):
    matched = db_connection.execute(
        text("""
            SELECT COUNT(DISTINCT c.school_id)
            FROM public.ipeds_completions_totals_2024 c
            INNER JOIN public.ipeds_institutions i
                ON c.school_id = i.school_id
        """)
    ).scalar_one()

    assert matched > 0
