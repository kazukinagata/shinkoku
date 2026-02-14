"""Hash computation for duplicate detection."""

from __future__ import annotations

import hashlib

from shinkoku.models import JournalLine


def compute_journal_hash(date: str, lines: list[JournalLine]) -> str:
    """Compute SHA-256 content hash of a journal entry.

    Hash is computed from date + normalized (sorted) journal lines.
    Description is intentionally excluded — same transaction with different
    descriptions should still be detected as duplicate.
    """
    # Normalize: sort lines by (side, account_code, amount) for order-independence
    sorted_lines = sorted(lines, key=lambda ln: (ln.side, ln.account_code, ln.amount))
    parts = [date]
    for line in sorted_lines:
        parts.append(f"{line.side}:{line.account_code}:{line.amount}")
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of file contents."""
    from pathlib import Path

    content = Path(file_path).read_bytes()
    return hashlib.sha256(content).hexdigest()
