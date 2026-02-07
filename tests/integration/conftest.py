"""Integration test conftest - fixtures for integration tests."""

import pytest

from shinkoku.db import init_db
from shinkoku.master_accounts import MASTER_ACCOUNTS


@pytest.fixture
def tmp_db(tmp_path):
    """Temporary file-based SQLite database for integration tests."""
    db_path = str(tmp_path / "shinkoku_test.db")
    conn = init_db(db_path)
    yield conn
    conn.close()


@pytest.fixture
def tmp_db_with_accounts(tmp_db):
    """Temporary file DB with master accounts loaded."""
    for a in MASTER_ACCOUNTS:
        tmp_db.execute(
            "INSERT INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    tmp_db.commit()
    return tmp_db
