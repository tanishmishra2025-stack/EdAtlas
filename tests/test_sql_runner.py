
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from edatlas.warehouse.build import get_engine


def test_postgres_read_only_transaction_blocks_insert():
    engine = get_engine()

    try:
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(
                    text("SET TRANSACTION READ ONLY")
                )

                with pytest.raises(
                    DBAPIError,
                    match="read-only transaction",
                ):
                    connection.execute(
                        text(
                            "INSERT INTO dw.dim_state "
                            "(state_code, state_name, has_bls_data) "
                            "VALUES ('ZZ', 'Test State', FALSE)"
                        )
                    )
    finally:
        engine.dispose()
