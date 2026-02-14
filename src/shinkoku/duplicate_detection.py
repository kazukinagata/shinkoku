"""Duplicate detection logic for journal entries."""

from __future__ import annotations

import sqlite3
from collections import defaultdict

from shinkoku.hashing import compute_journal_hash
from shinkoku.models import (
    DuplicateCheckResult,
    DuplicatePair,
    DuplicateWarning,
    JournalEntry,
)


def check_duplicate_on_insert(
    conn: sqlite3.Connection, fiscal_year: int, entry: JournalEntry
) -> DuplicateWarning | None:
    """Check for duplicates before inserting a journal entry.

    Returns:
        DuplicateWarning if duplicate found, None if clean.
        - match_type="exact": content_hash exact match → should block
        - match_type="similar": same date+amount → warning only
    """
    content_hash = compute_journal_hash(entry.date, entry.lines)

    # Check exact hash match
    row = conn.execute(
        "SELECT id FROM journals WHERE fiscal_year = ? AND content_hash = ?",
        (fiscal_year, content_hash),
    ).fetchone()
    if row:
        return DuplicateWarning(
            match_type="exact",
            score=100,
            existing_journal_id=row[0],
            reason=f"完全一致する仕訳が既に存在します (ID: {row[0]})",
        )

    # Check similar: same date + same total amount
    total_debit = sum(ln.amount for ln in entry.lines if ln.side == "debit")
    rows = conn.execute(
        "SELECT j.id, j.description FROM journals j "
        "INNER JOIN journal_lines jl ON jl.journal_id = j.id "
        "WHERE j.fiscal_year = ? AND j.date = ? AND jl.side = 'debit' "
        "GROUP BY j.id HAVING SUM(jl.amount) = ?",
        (fiscal_year, entry.date, total_debit),
    ).fetchall()
    if rows:
        existing_id = rows[0][0]
        existing_desc = rows[0][1] or ""
        return DuplicateWarning(
            match_type="similar",
            score=70,
            existing_journal_id=existing_id,
            reason=(f"同一日付・同一金額の仕訳が存在します (ID: {existing_id}, '{existing_desc}')"),
        )

    return None


def check_source_file_imported(
    conn: sqlite3.Connection, fiscal_year: int, file_hash: str
) -> dict | None:
    """Check if a source file has already been imported.

    Returns import record dict if already imported, None otherwise.
    """
    row = conn.execute(
        "SELECT id, file_name, imported_at FROM import_sources "
        "WHERE fiscal_year = ? AND file_hash = ?",
        (fiscal_year, file_hash),
    ).fetchone()
    if row:
        return {"id": row[0], "file_name": row[1], "imported_at": row[2]}
    return None


def record_import_source(
    conn: sqlite3.Connection,
    fiscal_year: int,
    file_hash: str,
    file_name: str,
    file_path: str | None = None,
    row_count: int = 0,
) -> int:
    """Record that a file has been imported. Returns the import_source id."""
    cursor = conn.execute(
        "INSERT INTO import_sources (fiscal_year, file_hash, file_name, file_path, row_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (fiscal_year, file_hash, file_name, file_path, row_count),
    )
    conn.commit()
    source_id: int = cursor.lastrowid  # type: ignore[assignment]
    return source_id


def find_duplicate_pairs(
    conn: sqlite3.Connection, fiscal_year: int, threshold: int = 70
) -> DuplicateCheckResult:
    """Scan all journals in a fiscal year for potential duplicates.

    Scoring:
    - 100: exact content_hash match
    - 90: same date + same amounts + partial account code match
    - 70: same date + same total debit amount only

    Returns pairs with score >= threshold.
    """
    pairs: list[DuplicatePair] = []

    # Phase 1: Exact hash duplicates
    hash_groups = conn.execute(
        "SELECT content_hash, GROUP_CONCAT(id) FROM journals "
        "WHERE fiscal_year = ? AND content_hash IS NOT NULL "
        "GROUP BY content_hash HAVING COUNT(*) > 1",
        (fiscal_year,),
    ).fetchall()

    exact_count = 0
    for row in hash_groups:
        ids = [int(x) for x in row[1].split(",")]
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append(
                    DuplicatePair(
                        journal_id_a=ids[i],
                        journal_id_b=ids[j],
                        score=100,
                        reason="content_hash完全一致",
                    )
                )
                exact_count += 1

    # Phase 2: Same date + same total debit (score 70-90)
    journals = conn.execute(
        "SELECT j.id, j.date, j.description, "
        "GROUP_CONCAT(jl.account_code ORDER BY jl.account_code), "
        "SUM(CASE WHEN jl.side='debit' THEN jl.amount ELSE 0 END) as debit_total "
        "FROM journals j "
        "INNER JOIN journal_lines jl ON jl.journal_id = j.id "
        "WHERE j.fiscal_year = ? "
        "GROUP BY j.id",
        (fiscal_year,),
    ).fetchall()

    # Index by (date, debit_total) for O(n) grouping
    groups: dict[tuple[str, int], list[tuple[int, str | None, str | None]]] = defaultdict(list)
    for j in journals:
        key = (j[1], j[4])  # (date, debit_total)
        groups[key].append((j[0], j[2], j[3]))  # (id, description, account_codes)

    # Already-seen pairs from exact matches
    seen = {(p.journal_id_a, p.journal_id_b) for p in pairs}

    suspected_count = 0
    for (date, total), members in groups.items():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j_idx in range(i + 1, len(members)):
                id_a, _, codes_a = members[i]
                id_b, _, codes_b = members[j_idx]
                pair_key = (min(id_a, id_b), max(id_a, id_b))
                if pair_key in seen:
                    continue
                # Score based on account code overlap
                if codes_a and codes_b and codes_a == codes_b:
                    score = 90
                    reason = f"同一日付({date})・同一金額・同一勘定科目"
                else:
                    score = 70
                    reason = f"同一日付({date})・同一金額({total:,}円)"
                if score >= threshold:
                    pairs.append(
                        DuplicatePair(
                            journal_id_a=pair_key[0],
                            journal_id_b=pair_key[1],
                            score=score,
                            reason=reason,
                        )
                    )
                    seen.add(pair_key)
                    suspected_count += 1

    return DuplicateCheckResult(
        pairs=sorted(pairs, key=lambda p: -p.score),
        exact_count=exact_count,
        suspected_count=suspected_count,
    )
