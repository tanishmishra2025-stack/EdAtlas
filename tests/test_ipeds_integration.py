
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


@pytest.fixture
def db_connection():
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        pytest.skip("EDATLAS_DATABASE_URL is not configured")

    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            yield connection
    finally:
        engine.dispose()


def test_ipeds_table_has_records(db_connection):
    total = db_connection.execute(
        text("SELECT COUNT(*) FROM ipeds_institutions")
    ).scalar_one()

    assert total > 0


def test_ipeds_school_ids_are_unique(db_connection):
    total, unique = db_connection.execute(
        text("""
            SELECT COUNT(*), COUNT(DISTINCT school_id)
            FROM ipeds_institutions
        """)
    ).one()

    assert total == unique


def test_college_scorecard_ipeds_join(db_connection):
    matched = db_connection.execute(
        text("""
            SELECT COUNT(*)
            FROM college_scorecard cs
            INNER JOIN ipeds_institutions ip
                ON cs.school_id = ip.school_id
        """)
    ).scalar_one()

    assert matched > 0
