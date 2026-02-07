"""Integration tests: CSV import -> journal registration flow.

Verifies that data imported via import_csv() can be correctly
converted to JournalEntry objects and stored via ledger tools.
"""

import pytest

from shinkoku.tools.import_data import import_csv
from shinkoku.tools.ledger import (
    ledger_init,
    ledger_add_journals_batch,
    ledger_search,
)
from shinkoku.models import JournalEntry, JournalLine, JournalSearchParams


@pytest.fixture
def csv_fixture(tmp_path):
    """Create a temporary CSV file with business expense data."""
    content = (
        "利用日,利用店名,利用金額\n"
        "2025-01-10,Amazon.co.jp,5000\n"
        "2025-01-15,サーバー代,3000\n"
        "2025-02-01,文房具店,1500\n"
        "2025-02-20,ドメイン更新,2000\n"
        "2025-03-10,コワーキングスペース,8000\n"
    )
    csv_path = tmp_path / "expenses.csv"
    csv_path.write_text(content, encoding="utf-8")
    return str(csv_path)


class TestImportToLedger:
    """Test CSV import -> ledger registration pipeline."""

    def test_csv_parsed_then_registered(self, tmp_path, csv_fixture):
        """Full flow: parse CSV -> create JournalEntry objects -> batch register."""
        # Step 1: Parse CSV
        csv_result = import_csv(file_path=csv_fixture)
        assert csv_result["status"] == "ok"
        assert csv_result["total_rows"] == 5
        candidates = csv_result["candidates"]

        # Step 2: Convert candidates to JournalEntry objects
        # Simulate what Claude would do: assign account codes based on description
        account_mapping = {
            "Amazon.co.jp": "5190",       # 消耗品費
            "サーバー代": "5140",          # 通信費
            "文房具店": "5190",            # 消耗品費
            "ドメイン更新": "5140",        # 通信費
            "コワーキングスペース": "5250",  # 地代家賃
        }

        entries = []
        for c in candidates:
            account_code = account_mapping.get(c["description"], "5270")  # default: 雑費
            entry = JournalEntry(
                date=c["date"],
                description=c["description"],
                source="csv_import",
                lines=[
                    JournalLine(side="debit", account_code=account_code, amount=c["amount"]),
                    JournalLine(side="credit", account_code="1002", amount=c["amount"]),
                ],
            )
            entries.append(entry)

        assert len(entries) == 5

        # Step 3: Initialize ledger and batch register
        db_path = str(tmp_path / "test.db")
        init_result = ledger_init(fiscal_year=2025, db_path=db_path)
        assert init_result["status"] == "ok"

        batch_result = ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries,
        )
        assert batch_result["status"] == "ok"
        assert batch_result["count"] == 5

        # Step 4: Verify all entries are stored correctly
        params = JournalSearchParams(fiscal_year=2025)
        search_result = ledger_search(db_path=db_path, params=params)
        assert search_result["total_count"] == 5

        # Verify amounts match original CSV
        stored_amounts = sorted(
            [j["lines"][0]["amount"] for j in search_result["journals"]]
        )
        original_amounts = sorted([c["amount"] for c in candidates])
        assert stored_amounts == original_amounts

    def test_csv_source_filter(self, tmp_path, csv_fixture):
        """Verify that csv_import source is properly set and searchable."""
        csv_result = import_csv(file_path=csv_fixture)
        candidates = csv_result["candidates"]

        entries = [
            JournalEntry(
                date=c["date"],
                description=c["description"],
                source="csv_import",
                lines=[
                    JournalLine(side="debit", account_code="5270", amount=c["amount"]),
                    JournalLine(side="credit", account_code="1002", amount=c["amount"]),
                ],
            )
            for c in candidates
        ]

        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries,
        )

        # Search by source
        params = JournalSearchParams(fiscal_year=2025, source="csv_import")
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 5

        # Search by non-existent source returns 0
        params_manual = JournalSearchParams(fiscal_year=2025, source="manual")
        result_manual = ledger_search(db_path=db_path, params=params_manual)
        assert result_manual["total_count"] == 0

    def test_csv_date_range_search_after_import(self, tmp_path, csv_fixture):
        """Verify date-range search works on imported data."""
        csv_result = import_csv(file_path=csv_fixture)
        candidates = csv_result["candidates"]

        entries = [
            JournalEntry(
                date=c["date"],
                description=c["description"],
                source="csv_import",
                lines=[
                    JournalLine(side="debit", account_code="5270", amount=c["amount"]),
                    JournalLine(side="credit", account_code="1002", amount=c["amount"]),
                ],
            )
            for c in candidates
        ]

        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries,
        )

        # January only (2 entries: Jan 10, Jan 15)
        params = JournalSearchParams(
            fiscal_year=2025,
            date_from="2025-01-01",
            date_to="2025-01-31",
        )
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 2

        # February only (2 entries: Feb 1, Feb 20)
        params = JournalSearchParams(
            fiscal_year=2025,
            date_from="2025-02-01",
            date_to="2025-02-28",
        )
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 2

    def test_csv_amounts_preserved_as_integers(self, tmp_path, csv_fixture):
        """All amounts should remain int through the entire pipeline."""
        csv_result = import_csv(file_path=csv_fixture)

        for c in csv_result["candidates"]:
            assert isinstance(c["amount"], int)

        entries = [
            JournalEntry(
                date=c["date"],
                description=c["description"],
                source="csv_import",
                lines=[
                    JournalLine(side="debit", account_code="5270", amount=c["amount"]),
                    JournalLine(side="credit", account_code="1002", amount=c["amount"]),
                ],
            )
            for c in csv_result["candidates"]
        ]

        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries,
        )

        params = JournalSearchParams(fiscal_year=2025)
        search_result = ledger_search(db_path=db_path, params=params)
        for journal in search_result["journals"]:
            for line in journal["lines"]:
                assert isinstance(line["amount"], int)

    def test_shift_jis_csv_import_to_ledger(self, tmp_path):
        """Verify Shift-JIS encoded CSV can be imported and registered."""
        content = "利用日,利用店名,利用金額\n2025-03-01,テスト店舗,9800\n"
        csv_path = tmp_path / "sjis.csv"
        csv_path.write_bytes(content.encode("shift_jis"))

        csv_result = import_csv(file_path=str(csv_path))
        assert csv_result["status"] == "ok"
        assert len(csv_result["candidates"]) == 1

        c = csv_result["candidates"][0]
        entry = JournalEntry(
            date=c["date"],
            description=c["description"],
            source="csv_import",
            lines=[
                JournalLine(side="debit", account_code="5270", amount=c["amount"]),
                JournalLine(side="credit", account_code="1001", amount=c["amount"]),
            ],
        )

        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        result = ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=[entry],
        )
        assert result["status"] == "ok"
        assert result["count"] == 1

        params = JournalSearchParams(fiscal_year=2025)
        found = ledger_search(db_path=db_path, params=params)
        assert found["journals"][0]["description"] == "テスト店舗"
        assert found["journals"][0]["lines"][0]["amount"] == 9800
