"""Data import tools for the shinkoku MCP server."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path


def register(mcp) -> None:
    """Register import tools with the MCP server."""

    @mcp.tool()
    def mcp_import_csv(file_path: str) -> dict:
        """Parse a CSV file and return structured candidates."""
        return import_csv(file_path=file_path)


def _detect_encoding(file_path: str) -> str:
    """Detect file encoding (UTF-8 or Shift_JIS)."""
    raw = Path(file_path).read_bytes()
    # Try UTF-8 first
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    # Try Shift_JIS
    try:
        raw.decode("shift_jis")
        return "shift_jis"
    except UnicodeDecodeError:
        pass
    # Fallback
    return "utf-8"


def _detect_date_column(headers: list[str]) -> int | None:
    """Find the column index that looks like a date column."""
    date_patterns = ["日付", "利用日", "date", "取引日", "発生日", "年月日"]
    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        for pattern in date_patterns:
            if pattern in h_lower:
                return i
    return 0 if headers else None


def _detect_description_column(headers: list[str]) -> int | None:
    """Find the column index for the description."""
    desc_patterns = [
        "摘要", "利用店名", "店名", "description", "内容",
        "取引内容", "備考", "名称",
    ]
    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        for pattern in desc_patterns:
            if pattern in h_lower:
                return i
    return 1 if len(headers) > 1 else None


def _detect_amount_column(headers: list[str]) -> int | None:
    """Find the column index for the amount."""
    amount_patterns = [
        "金額", "利用金額", "amount", "支払金額", "取引金額", "合計",
    ]
    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        for pattern in amount_patterns:
            if pattern in h_lower:
                return i
    return 2 if len(headers) > 2 else None


def _parse_amount(value: str) -> int | None:
    """Parse an amount string to int. Returns None if unparseable."""
    cleaned = value.strip().replace(",", "").replace("\\", "").replace("¥", "")
    cleaned = re.sub(r"[^\d\-]", "", cleaned)
    if not cleaned or cleaned == "-":
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _normalize_date(value: str) -> str | None:
    """Normalize date to YYYY-MM-DD format."""
    value = value.strip()
    # Already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value
    # YYYY/MM/DD
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", value)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def import_csv(*, file_path: str) -> dict:
    """Parse a CSV file and return CSVImportCandidate list.

    Supports UTF-8 and Shift_JIS encoding.
    Does not guess account codes (that is left to Claude/Skills).
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    encoding = _detect_encoding(file_path)
    try:
        text = path.read_text(encoding=encoding)
    except Exception as e:
        return {"status": "error", "message": f"Read error: {e}"}

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return {
            "status": "ok",
            "file_path": file_path,
            "encoding": encoding,
            "total_rows": 0,
            "candidates": [],
            "skipped_rows": [],
            "errors": [],
        }

    # First row is headers
    headers = [h.strip() for h in rows[0]]
    date_col = _detect_date_column(headers)
    desc_col = _detect_description_column(headers)
    amount_col = _detect_amount_column(headers)

    candidates = []
    skipped_rows = []
    errors = []

    for i, row in enumerate(rows[1:], start=2):
        # Skip empty rows
        if not row or all(not cell.strip() for cell in row):
            continue

        try:
            # Validate we have enough columns
            if (
                date_col is not None and date_col >= len(row)
                or desc_col is not None and desc_col >= len(row)
                or amount_col is not None and amount_col >= len(row)
            ):
                skipped_rows.append(i)
                continue

            date_val = _normalize_date(row[date_col]) if date_col is not None else None
            desc_val = row[desc_col].strip() if desc_col is not None else ""
            amount_val = _parse_amount(row[amount_col]) if amount_col is not None else None

            if date_val is None or amount_val is None:
                skipped_rows.append(i)
                continue

            # Build original_data dict from headers
            original = {}
            for j, h in enumerate(headers):
                if j < len(row):
                    original[h] = row[j].strip()

            candidates.append({
                "row_number": i,
                "date": date_val,
                "description": desc_val,
                "amount": amount_val,
                "original_data": original,
            })
        except (IndexError, ValueError):
            skipped_rows.append(i)

    return {
        "status": "ok",
        "file_path": file_path,
        "encoding": encoding,
        "total_rows": len(candidates),
        "candidates": candidates,
        "skipped_rows": skipped_rows,
        "errors": errors,
    }
