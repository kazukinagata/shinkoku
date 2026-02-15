"""Tests for furusato.py CLI script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FURUSATO_SCRIPT = PROJECT_ROOT / "skills" / "furusato" / "scripts" / "furusato.py"


def run_furusato(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FURUSATO_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
    )


# --- add ---


def test_add_donation(db_path: str, tmp_path: Path):
    input_file = tmp_path / "donation.json"
    input_file.write_text(
        json.dumps(
            {
                "fiscal_year": 2025,
                "municipality_name": "北海道旭川市",
                "amount": 30000,
                "date": "2025-06-15",
                "municipality_prefecture": "北海道",
            }
        ),
        encoding="utf-8",
    )
    result = run_furusato("add", "--db-path", db_path, "--input", str(input_file))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["donation_id"] >= 1


def test_add_donation_invalid_date(db_path: str, tmp_path: Path):
    input_file = tmp_path / "bad.json"
    input_file.write_text(
        json.dumps(
            {
                "fiscal_year": 2025,
                "municipality_name": "テスト市",
                "amount": 10000,
                "date": "20250615",  # 不正な日付形式
            }
        ),
        encoding="utf-8",
    )
    result = run_furusato("add", "--db-path", db_path, "--input", str(input_file))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


def test_add_donation_duplicate(db_path: str, tmp_path: Path):
    input_file = tmp_path / "dup.json"
    data = {
        "fiscal_year": 2025,
        "municipality_name": "テスト市",
        "amount": 10000,
        "date": "2025-03-01",
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")
    # 1回目: 成功
    result = run_furusato("add", "--db-path", db_path, "--input", str(input_file))
    assert result.returncode == 0
    # 2回目: 重複エラー
    result = run_furusato("add", "--db-path", db_path, "--input", str(input_file))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


# --- list ---


def test_list_empty(db_path: str):
    result = run_furusato("list", "--db-path", db_path, "--fiscal-year", "2025")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["count"] == 0
    assert output["donations"] == []


def test_list_with_donations(db_path: str, tmp_path: Path):
    # 寄附を追加
    input_file = tmp_path / "d.json"
    input_file.write_text(
        json.dumps(
            {
                "fiscal_year": 2025,
                "municipality_name": "テスト市",
                "amount": 20000,
                "date": "2025-04-01",
            }
        ),
        encoding="utf-8",
    )
    run_furusato("add", "--db-path", db_path, "--input", str(input_file))

    result = run_furusato("list", "--db-path", db_path, "--fiscal-year", "2025")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["count"] == 1
    assert output["donations"][0]["municipality_name"] == "テスト市"


# --- delete ---


def test_delete_donation(db_path: str, tmp_path: Path):
    # まず追加
    input_file = tmp_path / "d.json"
    input_file.write_text(
        json.dumps(
            {
                "fiscal_year": 2025,
                "municipality_name": "削除テスト市",
                "amount": 15000,
                "date": "2025-05-01",
            }
        ),
        encoding="utf-8",
    )
    add_result = run_furusato("add", "--db-path", db_path, "--input", str(input_file))
    donation_id = json.loads(add_result.stdout)["donation_id"]

    # 削除
    result = run_furusato("delete", "--db-path", db_path, "--donation-id", str(donation_id))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"


def test_delete_not_found(db_path: str):
    result = run_furusato("delete", "--db-path", db_path, "--donation-id", "9999")
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


# --- summary ---


def test_summary_empty(db_path: str):
    result = run_furusato("summary", "--db-path", db_path, "--fiscal-year", "2025")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["total_amount"] == 0
    assert output["donation_count"] == 0


def test_summary_with_data(db_path: str, tmp_path: Path):
    # 2件追加
    for i, (name, amount) in enumerate([("A市", 30000), ("B市", 20000)]):
        f = tmp_path / f"d{i}.json"
        f.write_text(
            json.dumps(
                {
                    "fiscal_year": 2025,
                    "municipality_name": name,
                    "amount": amount,
                    "date": f"2025-0{i + 1}-15",
                }
            ),
            encoding="utf-8",
        )
        run_furusato("add", "--db-path", db_path, "--input", str(f))

    result = run_furusato("summary", "--db-path", db_path, "--fiscal-year", "2025")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["total_amount"] == 50000
    assert output["donation_count"] == 2
    assert output["municipality_count"] == 2
    # 控除額 = 50000 - 2000 = 48000
    assert output["deduction_amount"] == 48000


def test_summary_with_estimated_limit(db_path: str, tmp_path: Path):
    f = tmp_path / "d.json"
    f.write_text(
        json.dumps(
            {
                "fiscal_year": 2025,
                "municipality_name": "限度額テスト市",
                "amount": 100000,
                "date": "2025-06-01",
            }
        ),
        encoding="utf-8",
    )
    run_furusato("add", "--db-path", db_path, "--input", str(f))

    result = run_furusato(
        "summary",
        "--db-path",
        db_path,
        "--fiscal-year",
        "2025",
        "--estimated-limit",
        "50000",
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["over_limit"] is True


# --- no subcommand ---


def test_no_subcommand():
    result = run_furusato()
    assert result.returncode == 1
