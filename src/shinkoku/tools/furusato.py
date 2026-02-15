"""Furusato nozei (hometown tax donation) management tools."""

from __future__ import annotations

import re
import sqlite3

from shinkoku.models import FurusatoDonationRecord, FurusatoDonationSummary
from shinkoku.tools.tax_calc import calc_furusato_deduction

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ============================================================
# Business Logic (pure functions)
# ============================================================


def add_furusato_donation(
    conn: sqlite3.Connection,
    fiscal_year: int,
    municipality_name: str,
    amount: int,
    date: str,
    municipality_prefecture: str | None = None,
    receipt_number: str | None = None,
    one_stop_applied: bool = False,
    source_file: str | None = None,
) -> int:
    """Add a furusato donation record. Returns the donation id."""
    if not _DATE_PATTERN.match(date):
        raise ValueError(f"日付の形式が不正です (YYYY-MM-DD): {date}")

    # 重複チェック: 同一自治体・同一日付・同一金額の寄附がないか
    existing = conn.execute(
        "SELECT id FROM furusato_donations "
        "WHERE fiscal_year = ? AND municipality_name = ? AND date = ? AND amount = ?",
        (fiscal_year, municipality_name, date, amount),
    ).fetchone()
    if existing:
        raise ValueError(f"同一の寄附が既に登録されています (ID: {existing[0]})")

    cursor = conn.execute(
        "INSERT INTO furusato_donations "
        "(fiscal_year, municipality_name, municipality_prefecture, "
        "amount, date, receipt_number, one_stop_applied, source_file) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            fiscal_year,
            municipality_name,
            municipality_prefecture,
            amount,
            date,
            receipt_number,
            1 if one_stop_applied else 0,
            source_file,
        ),
    )
    conn.commit()
    donation_id: int = cursor.lastrowid  # type: ignore[assignment]
    return donation_id


def list_furusato_donations(
    conn: sqlite3.Connection, fiscal_year: int
) -> list[FurusatoDonationRecord]:
    """List all furusato donations for a fiscal year."""
    rows = conn.execute(
        "SELECT id, fiscal_year, municipality_name, municipality_prefecture, "
        "amount, date, receipt_number, one_stop_applied, source_file "
        "FROM furusato_donations WHERE fiscal_year = ? ORDER BY date",
        (fiscal_year,),
    ).fetchall()
    return [
        FurusatoDonationRecord(
            id=r[0],
            fiscal_year=r[1],
            municipality_name=r[2],
            municipality_prefecture=r[3],
            amount=r[4],
            date=r[5],
            receipt_number=r[6],
            one_stop_applied=bool(r[7]),
            source_file=r[8],
        )
        for r in rows
    ]


def delete_furusato_donation(conn: sqlite3.Connection, donation_id: int) -> bool:
    """Delete a furusato donation. Returns True if deleted."""
    row = conn.execute("SELECT id FROM furusato_donations WHERE id = ?", (donation_id,)).fetchone()
    if row is None:
        return False
    conn.execute("DELETE FROM furusato_donations WHERE id = ?", (donation_id,))
    conn.commit()
    return True


def summarize_furusato_donations(
    conn: sqlite3.Connection,
    fiscal_year: int,
    estimated_limit: int | None = None,
) -> FurusatoDonationSummary:
    """Summarize furusato donations and compute deduction."""
    donations = list_furusato_donations(conn, fiscal_year)
    total_amount = sum(d.amount for d in donations)
    donation_count = len(donations)
    municipalities = {d.municipality_name for d in donations}
    municipality_count = len(municipalities)
    deduction_amount = calc_furusato_deduction(total_amount)
    one_stop_count = sum(1 for d in donations if d.one_stop_applied)

    over_limit = False
    if estimated_limit is not None and total_amount > estimated_limit:
        over_limit = True

    # 副業で確定申告が必要なユーザー向けのため、常に True
    # ワンストップ特例は確定申告すると無効化される
    needs_tax_return = True

    return FurusatoDonationSummary(
        fiscal_year=fiscal_year,
        total_amount=total_amount,
        donation_count=donation_count,
        municipality_count=municipality_count,
        deduction_amount=deduction_amount,
        estimated_limit=estimated_limit,
        over_limit=over_limit,
        one_stop_count=one_stop_count,
        needs_tax_return=needs_tax_return,
        donations=donations,
    )
