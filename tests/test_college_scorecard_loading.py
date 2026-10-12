
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


def test_database_transaction_rollback():
    database_url = os.getenv("EDATLAS_DATABASE_URL")

    if not database_url:
        pytest.skip("EdAtlas database URL not configured")

    engine = create_engine(database_url)

    try:
        # Capture the existing record count.
        with engine.connect() as connection:
            original_count = connection.execute(
                text("SELECT COUNT(*) FROM college_scorecard")
            ).scalar_one()

        # Deliberately trigger a failure inside a transaction.
        with pytest.raises(RuntimeError):
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM college_scorecard")
                )

                raise RuntimeError("Simulated loading failure")

        # Verify that the transaction was rolled back.
        with engine.connect() as connection:
            final_count = connection.execute(
                text("SELECT COUNT(*) FROM college_scorecard")
            ).scalar_one()

        assert final_count == original_count

    finally:
        engine.dispose()
