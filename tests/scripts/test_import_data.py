"""Tests for import_data.py CLI script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMPORT_SCRIPT = PROJECT_ROOT / "skills" / "journal" / "scripts" / "import_data.py"


def run_import(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(IMPORT_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
    )


# --- csv ---


def test_import_csv(tmp_path: Path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("日付,摘要,金額\n2025-01-15,テスト,1000\n", encoding="utf-8")
    result = run_import("csv", "--file-path", str(csv_file))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert len(output["candidates"]) == 1
    assert output["candidates"][0]["amount"] == 1000


def test_import_csv_file_not_found(tmp_path: Path):
    result = run_import("csv", "--file-path", str(tmp_path / "nonexistent.csv"))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


def test_import_csv_empty(tmp_path: Path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("", encoding="utf-8")
    result = run_import("csv", "--file-path", str(csv_file))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["total_rows"] == 0


# --- receipt ---


def test_import_receipt(tmp_path: Path):
    img = tmp_path / "receipt.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0dummy")
    result = run_import("receipt", "--file-path", str(img))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["file_path"] == str(img)
    assert output["date"] is None


def test_import_receipt_file_not_found(tmp_path: Path):
    result = run_import("receipt", "--file-path", str(tmp_path / "nonexistent.jpg"))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


# --- invoice ---


def test_import_invoice(tmp_path: Path):
    # テキストファイルで代用（pdfplumber は空文字を返す）
    f = tmp_path / "invoice.txt"
    f.write_text("dummy invoice", encoding="utf-8")
    result = run_import("invoice", "--file-path", str(f))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"


def test_import_invoice_not_found(tmp_path: Path):
    result = run_import("invoice", "--file-path", str(tmp_path / "missing.pdf"))
    assert result.returncode == 1


# --- withholding ---


def test_import_withholding(tmp_path: Path):
    f = tmp_path / "withholding.txt"
    f.write_text("dummy", encoding="utf-8")
    result = run_import("withholding", "--file-path", str(f))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"


def test_import_withholding_not_found(tmp_path: Path):
    result = run_import("withholding", "--file-path", str(tmp_path / "missing.pdf"))
    assert result.returncode == 1


# --- furusato-receipt ---


def test_import_furusato_receipt(tmp_path: Path):
    f = tmp_path / "furusato.jpg"
    f.write_bytes(b"\xff\xd8\xff\xe0dummy")
    result = run_import("furusato-receipt", "--file-path", str(f))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["municipality_name"] is None


def test_import_furusato_receipt_not_found(tmp_path: Path):
    result = run_import("furusato-receipt", "--file-path", str(tmp_path / "missing.jpg"))
    assert result.returncode == 1


# --- payment-statement ---


def test_import_payment_statement(tmp_path: Path):
    f = tmp_path / "statement.txt"
    f.write_text("dummy payment statement", encoding="utf-8")
    result = run_import("payment-statement", "--file-path", str(f))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"


def test_import_payment_statement_not_found(tmp_path: Path):
    result = run_import("payment-statement", "--file-path", str(tmp_path / "missing.pdf"))
    assert result.returncode == 1


# --- deduction-certificate ---


def test_import_deduction_certificate(tmp_path: Path):
    f = tmp_path / "cert.txt"
    f.write_text("dummy certificate", encoding="utf-8")
    result = run_import("deduction-certificate", "--file-path", str(f))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["certificate_type"] is None


def test_import_deduction_certificate_not_found(tmp_path: Path):
    result = run_import("deduction-certificate", "--file-path", str(tmp_path / "missing.pdf"))
    assert result.returncode == 1


# --- check-imported ---


def test_check_imported_not_imported(db_path: str, tmp_path: Path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("日付,摘要,金額\n2025-01-15,テスト,1000\n", encoding="utf-8")
    result = run_import(
        "check-imported",
        "--db-path",
        db_path,
        "--fiscal-year",
        "2025",
        "--file-path",
        str(csv_file),
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "not_imported"


def test_check_imported_already_imported(db_path: str, tmp_path: Path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("日付,摘要,金額\n2025-01-15,テスト,1000\n", encoding="utf-8")
    # まず record-source で記録
    run_import(
        "record-source",
        "--db-path",
        db_path,
        "--fiscal-year",
        "2025",
        "--file-path",
        str(csv_file),
        "--row-count",
        "1",
    )
    # check-imported で確認
    result = run_import(
        "check-imported",
        "--db-path",
        db_path,
        "--fiscal-year",
        "2025",
        "--file-path",
        str(csv_file),
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "already_imported"


def test_check_imported_file_not_found(db_path: str, tmp_path: Path):
    result = run_import(
        "check-imported",
        "--db-path",
        db_path,
        "--fiscal-year",
        "2025",
        "--file-path",
        str(tmp_path / "missing.csv"),
    )
    assert result.returncode == 1


# --- record-source ---


def test_record_source(db_path: str, tmp_path: Path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("test data", encoding="utf-8")
    result = run_import(
        "record-source",
        "--db-path",
        db_path,
        "--fiscal-year",
        "2025",
        "--file-path",
        str(csv_file),
        "--row-count",
        "5",
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["import_source_id"] >= 1


def test_record_source_file_not_found(db_path: str, tmp_path: Path):
    result = run_import(
        "record-source",
        "--db-path",
        db_path,
        "--fiscal-year",
        "2025",
        "--file-path",
        str(tmp_path / "missing.csv"),
    )
    assert result.returncode == 1


# --- no subcommand ---


def test_no_subcommand():
    result = run_import()
    assert result.returncode == 1
