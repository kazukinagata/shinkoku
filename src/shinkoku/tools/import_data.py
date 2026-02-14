"""Data import tools for the shinkoku MCP server."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from shinkoku.db import get_connection
from shinkoku.duplicate_detection import check_source_file_imported, record_import_source
from shinkoku.hashing import compute_file_hash


def register(mcp) -> None:
    """Register import tools with the MCP server."""

    @mcp.tool()
    def mcp_import_csv(file_path: str) -> dict:
        """Parse a CSV file and return structured candidates."""
        return import_csv(file_path=file_path)

    @mcp.tool()
    def mcp_import_receipt(file_path: str) -> dict:
        """Check receipt file existence and return template for OCR."""
        return import_receipt(file_path=file_path)

    @mcp.tool()
    def mcp_import_invoice(file_path: str) -> dict:
        """Extract text from an invoice PDF."""
        return import_invoice(file_path=file_path)

    @mcp.tool()
    def mcp_import_withholding(file_path: str) -> dict:
        """Extract text from a withholding slip PDF."""
        return import_withholding(file_path=file_path)

    @mcp.tool()
    def mcp_import_furusato_receipt(file_path: str) -> dict:
        """Check furusato receipt file and return template for OCR."""
        return import_furusato_receipt(file_path=file_path)

    @mcp.tool()
    def mcp_import_payment_statement(file_path: str) -> dict:
        """Extract data from a payment statement (支払調書) PDF or image."""
        return import_payment_statement(file_path=file_path)

    @mcp.tool()
    def mcp_import_check_csv_imported(db_path: str, fiscal_year: int, file_path: str) -> dict:
        """Check if a CSV file has already been imported."""
        return import_check_csv_imported(
            db_path=db_path, fiscal_year=fiscal_year, file_path=file_path
        )

    @mcp.tool()
    def mcp_import_record_source(
        db_path: str, fiscal_year: int, file_path: str, row_count: int = 0
    ) -> dict:
        """Record that a file has been imported."""
        return import_record_source(
            db_path=db_path,
            fiscal_year=fiscal_year,
            file_path=file_path,
            row_count=row_count,
        )


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
        "摘要",
        "利用店名",
        "店名",
        "description",
        "内容",
        "取引内容",
        "備考",
        "名称",
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
        "金額",
        "利用金額",
        "amount",
        "支払金額",
        "取引金額",
        "合計",
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
    errors: list[str] = []

    for i, row in enumerate(rows[1:], start=2):
        # Skip empty rows
        if not row or all(not cell.strip() for cell in row):
            continue

        try:
            # Validate we have enough columns
            if (
                date_col is not None
                and date_col >= len(row)
                or desc_col is not None
                and desc_col >= len(row)
                or amount_col is not None
                and amount_col >= len(row)
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

            candidates.append(
                {
                    "row_number": i,
                    "date": date_val,
                    "description": desc_val,
                    "amount": amount_val,
                    "original_data": original,
                }
            )
        except (IndexError, ValueError):
            skipped_rows.append(i)

    # ファイルハッシュ（重複インポート検出用）
    file_hash = compute_file_hash(file_path)

    return {
        "status": "ok",
        "file_path": file_path,
        "file_hash": file_hash,
        "encoding": encoding,
        "total_rows": len(candidates),
        "candidates": candidates,
        "skipped_rows": skipped_rows,
        "errors": errors,
    }


def import_receipt(*, file_path: str) -> dict:
    """Check file existence and return a ReceiptData template.

    OCR is performed by Claude Vision, so this tool only verifies the file
    exists and returns an empty template for Claude to fill in.
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    return {
        "status": "ok",
        "file_path": file_path,
        "date": None,
        "vendor": None,
        "total_amount": None,
        "items": [],
        "tax_included": True,
    }


def _extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF using pdfplumber."""
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception:
        return ""


def import_invoice(*, file_path: str) -> dict:
    """Extract text from an invoice PDF and return InvoiceData template."""
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    extracted_text = _extract_pdf_text(file_path)

    return {
        "status": "ok",
        "file_path": file_path,
        "extracted_text": extracted_text,
        "vendor": None,
        "invoice_number": None,
        "date": None,
        "total_amount": None,
        "tax_amount": None,
    }


def import_withholding(*, file_path: str) -> dict:
    """Extract text from a withholding slip PDF and return template."""
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    extracted_text = _extract_pdf_text(file_path)

    return {
        "status": "ok",
        "file_path": file_path,
        "extracted_text": extracted_text,
        "payer_name": None,
        "payment_amount": 0,
        "withheld_tax": 0,
        "social_insurance": 0,
        "life_insurance_deduction": 0,
        "earthquake_insurance_deduction": 0,
        "housing_loan_deduction": 0,
    }


def import_furusato_receipt(*, file_path: str) -> dict:
    """Check receipt file existence and return FurusatoReceiptData template.

    OCR is performed by Claude Vision, so this tool only verifies the file
    exists and returns an empty template for Claude to fill in.
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    return {
        "status": "ok",
        "file_path": file_path,
        "municipality_name": None,
        "municipality_prefecture": None,
        "address": None,
        "amount": None,
        "date": None,
        "receipt_number": None,
    }


def import_payment_statement(*, file_path: str) -> dict:
    """Check payment statement file and return template for data extraction.

    支払調書（報酬、料金、契約金及び賞金の支払調書）の読み取り。
    PDF の場合はテキスト抽出し、画像の場合は Claude Vision に委任する。
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    extracted_text = ""
    if path.suffix.lower() == ".pdf":
        extracted_text = _extract_pdf_text(file_path)

    return {
        "status": "ok",
        "file_path": file_path,
        "extracted_text": extracted_text,
        "payer_name": None,
        "category": None,  # 区分（報酬/料金/契約金等）
        "gross_amount": None,  # 支払金額
        "withholding_tax": None,  # 源泉徴収税額
    }


def import_check_csv_imported(*, db_path: str, fiscal_year: int, file_path: str) -> dict:
    """Check if a CSV file has already been imported."""
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    file_hash = compute_file_hash(file_path)
    conn = get_connection(db_path)
    try:
        record = check_source_file_imported(conn, fiscal_year, file_hash)
        if record:
            return {
                "status": "already_imported",
                "file_path": file_path,
                "file_hash": file_hash,
                "import_record": record,
            }
        return {
            "status": "not_imported",
            "file_path": file_path,
            "file_hash": file_hash,
        }
    finally:
        conn.close()


def import_record_source(
    *, db_path: str, fiscal_year: int, file_path: str, row_count: int = 0
) -> dict:
    """Record that a file has been imported."""
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    file_hash = compute_file_hash(file_path)
    file_name = path.name
    conn = get_connection(db_path)
    try:
        source_id = record_import_source(
            conn,
            fiscal_year,
            file_hash,
            file_name,
            file_path=file_path,
            row_count=row_count,
        )
        return {
            "status": "ok",
            "import_source_id": source_id,
            "file_hash": file_hash,
            "file_name": file_name,
        }
    finally:
        conn.close()
