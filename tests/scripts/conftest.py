"""Shared fixtures for CLI script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Initialize a test DB via init_db and return its path."""
    db = str(tmp_path / "test.db")
    # init_db を直接使用して DB を初期化
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    conn = init_db(db)
    # マスタ勘定科目を投入
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts "
            "(code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a.get("tax_category")),
        )
    # テスト用の会計年度を作成
    conn.execute("INSERT OR IGNORE INTO fiscal_years (year) VALUES (?)", (2025,))
    conn.commit()
    conn.close()
    return db


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the unified shinkoku CLI and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "shinkoku.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
    )


def write_json(tmp_path: Path, data: Any, name: str = "input.json") -> str:
    """Write JSON data to a temp file and return path."""
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False))
    return str(path)
