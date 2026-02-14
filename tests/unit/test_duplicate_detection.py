"""Tests for duplicate detection logic."""

from __future__ import annotations

from shinkoku.duplicate_detection import (
    check_duplicate_on_insert,
    check_source_file_imported,
    find_duplicate_pairs,
    record_import_source,
)
from shinkoku.hashing import compute_journal_hash
from shinkoku.models import JournalEntry, JournalLine


def _make_entry(
    date: str = "2025-01-15",
    debit_code: str = "1001",
    credit_code: str = "4001",
    amount: int = 10000,
    description: str | None = "test",
) -> JournalEntry:
    return JournalEntry(
        date=date,
        description=description,
        lines=[
            JournalLine(side="debit", account_code=debit_code, amount=amount),
            JournalLine(side="credit", account_code=credit_code, amount=amount),
        ],
    )


def _insert_journal(
    db, entry: JournalEntry, fiscal_year: int = 2025, include_hash: bool = True
) -> int:
    """Insert a journal entry directly into DB (bypassing duplicate check).

    include_hash=False simulates legacy data inserted before duplicate detection.
    """
    content_hash = compute_journal_hash(entry.date, entry.lines) if include_hash else None
    cursor = db.execute(
        "INSERT INTO journals (fiscal_year, date, description, content_hash) VALUES (?, ?, ?, ?)",
        (fiscal_year, entry.date, entry.description, content_hash),
    )
    journal_id = cursor.lastrowid
    for line in entry.lines:
        db.execute(
            "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
            "VALUES (?, ?, ?, ?)",
            (journal_id, line.side, line.account_code, line.amount),
        )
    db.commit()
    return journal_id


class TestCheckDuplicateOnInsert:
    def test_exact_duplicate_detected(self, in_memory_db_with_accounts):
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        entry = _make_entry()
        _insert_journal(db, entry)

        # Same entry should be detected as exact duplicate
        warning = check_duplicate_on_insert(db, 2025, entry)
        assert warning is not None
        assert warning.match_type == "exact"
        assert warning.score == 100

    def test_similar_detected(self, in_memory_db_with_accounts):
        """Same date + same amount but different accounts -> similar."""
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        entry1 = _make_entry(debit_code="1001", credit_code="4001")
        _insert_journal(db, entry1)

        # Same date, same amount, different accounts
        entry2 = _make_entry(debit_code="5190", credit_code="1002")
        warning = check_duplicate_on_insert(db, 2025, entry2)
        assert warning is not None
        assert warning.match_type == "similar"
        assert warning.score == 70

    def test_no_duplicate_clean(self, in_memory_db_with_accounts):
        """Different entry should return None."""
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        entry1 = _make_entry(date="2025-01-15", amount=10000)
        _insert_journal(db, entry1)

        # Different date and amount
        entry2 = _make_entry(date="2025-02-15", amount=20000)
        warning = check_duplicate_on_insert(db, 2025, entry2)
        assert warning is None


class TestSourceFileCheck:
    def test_source_file_check(self, in_memory_db_with_accounts):
        """Record and re-check file import."""
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        file_hash = "abc123def456"

        # Not imported yet
        result = check_source_file_imported(db, 2025, file_hash)
        assert result is None

        # Record import
        source_id = record_import_source(
            db,
            2025,
            file_hash,
            "expenses.csv",
            file_path="/tmp/expenses.csv",
            row_count=10,
        )
        assert source_id > 0

        # Now should be detected
        result = check_source_file_imported(db, 2025, file_hash)
        assert result is not None
        assert result["file_name"] == "expenses.csv"


class TestFindDuplicatePairs:
    def test_find_duplicate_pairs_legacy_exact(self, in_memory_db_with_accounts):
        """Legacy entries (NULL hash) with identical content detected via date+amount+accounts."""
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        entry = _make_entry()
        # Legacy data: inserted without content_hash (before duplicate detection was added)
        id1 = _insert_journal(db, entry, include_hash=False)
        id2 = _insert_journal(db, entry, include_hash=False)

        result = find_duplicate_pairs(db, 2025)
        # Phase 2 detects same date + same amount + same accounts → score 90
        assert result.suspected_count >= 1
        high_score_pairs = [p for p in result.pairs if p.score >= 90]
        assert len(high_score_pairs) >= 1
        pair_ids = {(p.journal_id_a, p.journal_id_b) for p in high_score_pairs}
        assert (min(id1, id2), max(id1, id2)) in pair_ids

    def test_find_duplicate_pairs_similar(self, in_memory_db_with_accounts):
        """Same date/amount but different accounts -> score 70-90."""
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        entry1 = _make_entry(debit_code="1001", credit_code="4001")
        entry2 = _make_entry(debit_code="5190", credit_code="1002")
        _insert_journal(db, entry1)
        _insert_journal(db, entry2)

        result = find_duplicate_pairs(db, 2025)
        # Should find suspected pairs (same date + same debit total)
        assert result.suspected_count >= 1
        suspected = [p for p in result.pairs if 70 <= p.score < 100]
        assert len(suspected) >= 1

    def test_find_duplicate_pairs_threshold_filter(self, in_memory_db_with_accounts):
        """Threshold should filter out low-score pairs."""
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        # Two entries with same date/amount but different accounts -> score 70
        entry1 = _make_entry(debit_code="1001", credit_code="4001")
        entry2 = _make_entry(debit_code="5190", credit_code="1002")
        _insert_journal(db, entry1)
        _insert_journal(db, entry2)

        # With threshold 80, score 70 pairs should be filtered out
        result_high = find_duplicate_pairs(db, 2025, threshold=80)
        low_score = [p for p in result_high.pairs if p.score < 80]
        assert len(low_score) == 0

        # With threshold 60, score 70 pairs should be included
        result_low = find_duplicate_pairs(db, 2025, threshold=60)
        included = [p for p in result_low.pairs if p.score >= 60]
        assert len(included) >= 1
