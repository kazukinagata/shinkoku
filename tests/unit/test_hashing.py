"""Tests for hash computation functions."""

from __future__ import annotations

from shinkoku.hashing import compute_journal_hash, compute_file_hash
from shinkoku.models import JournalLine


class TestComputeJournalHash:
    def test_same_content_same_hash(self):
        """Identical entries produce the same hash."""
        lines = [
            JournalLine(side="debit", account_code="1001", amount=10000),
            JournalLine(side="credit", account_code="4001", amount=10000),
        ]
        h1 = compute_journal_hash("2025-01-15", lines)
        h2 = compute_journal_hash("2025-01-15", lines)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_different_line_order_same_hash(self):
        """Line order doesn't matter — hash is order-independent."""
        lines_a = [
            JournalLine(side="debit", account_code="5140", amount=3000),
            JournalLine(side="debit", account_code="5120", amount=2000),
            JournalLine(side="credit", account_code="1002", amount=5000),
        ]
        lines_b = [
            JournalLine(side="credit", account_code="1002", amount=5000),
            JournalLine(side="debit", account_code="5120", amount=2000),
            JournalLine(side="debit", account_code="5140", amount=3000),
        ]
        h_a = compute_journal_hash("2025-03-01", lines_a)
        h_b = compute_journal_hash("2025-03-01", lines_b)
        assert h_a == h_b

    def test_description_excluded_from_hash(self):
        """Different descriptions should not affect the hash (description not in hash)."""
        lines = [
            JournalLine(side="debit", account_code="1001", amount=10000),
            JournalLine(side="credit", account_code="4001", amount=10000),
        ]
        # compute_journal_hash takes date and lines only, not description
        h1 = compute_journal_hash("2025-01-15", lines)
        h2 = compute_journal_hash("2025-01-15", lines)
        assert h1 == h2

    def test_different_amount_different_hash(self):
        """Different amounts produce different hashes."""
        lines_a = [
            JournalLine(side="debit", account_code="1001", amount=10000),
            JournalLine(side="credit", account_code="4001", amount=10000),
        ]
        lines_b = [
            JournalLine(side="debit", account_code="1001", amount=20000),
            JournalLine(side="credit", account_code="4001", amount=20000),
        ]
        h_a = compute_journal_hash("2025-01-15", lines_a)
        h_b = compute_journal_hash("2025-01-15", lines_b)
        assert h_a != h_b

    def test_different_date_different_hash(self):
        """Different dates produce different hashes."""
        lines = [
            JournalLine(side="debit", account_code="1001", amount=10000),
            JournalLine(side="credit", account_code="4001", amount=10000),
        ]
        h_a = compute_journal_hash("2025-01-15", lines)
        h_b = compute_journal_hash("2025-02-15", lines)
        assert h_a != h_b


class TestComputeFileHash:
    def test_file_hash_consistent(self, tmp_path):
        """Same file content produces same hash."""
        f = tmp_path / "test.csv"
        f.write_text("date,amount\n2025-01-01,1000\n", encoding="utf-8")
        h1 = compute_file_hash(str(f))
        h2 = compute_file_hash(str(f))
        assert h1 == h2
        assert len(h1) == 64

    def test_different_content_different_hash(self, tmp_path):
        """Different file contents produce different hashes."""
        f1 = tmp_path / "a.csv"
        f2 = tmp_path / "b.csv"
        f1.write_text("date,amount\n2025-01-01,1000\n", encoding="utf-8")
        f2.write_text("date,amount\n2025-01-01,2000\n", encoding="utf-8")
        assert compute_file_hash(str(f1)) != compute_file_hash(str(f2))
