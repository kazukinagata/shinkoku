"""Tests for import_data tools."""
import os
import pytest
from pathlib import Path

from shinkoku.tools.import_data import import_csv

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "csv"


class TestImportCSV:
    def test_parse_utf8_csv(self):
        csv_path = str(FIXTURES_DIR / "credit_card_simple.csv")
        result = import_csv(file_path=csv_path)
        assert result["status"] == "ok"
        assert result["encoding"] in ("utf-8", "utf-8-sig")
        assert result["total_rows"] == 5
        assert len(result["candidates"]) == 5

    def test_candidate_fields(self):
        csv_path = str(FIXTURES_DIR / "credit_card_simple.csv")
        result = import_csv(file_path=csv_path)
        c = result["candidates"][0]
        assert "row_number" in c
        assert "date" in c
        assert "description" in c
        assert "amount" in c
        assert "original_data" in c

    def test_amounts_are_integer(self):
        csv_path = str(FIXTURES_DIR / "credit_card_simple.csv")
        result = import_csv(file_path=csv_path)
        for c in result["candidates"]:
            assert isinstance(c["amount"], int)

    def test_parse_shift_jis(self, tmp_path):
        content = "利用日,利用店名,利用金額\n2025-02-01,テスト店,1500\n"
        p = tmp_path / "sjis.csv"
        p.write_bytes(content.encode("shift_jis"))
        result = import_csv(file_path=str(p))
        assert result["status"] == "ok"
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["amount"] == 1500

    def test_skip_invalid_rows(self, tmp_path):
        content = "日付,摘要,金額\n2025-01-01,ok,1000\nbad row\n2025-01-02,ok2,2000\n"
        p = tmp_path / "bad.csv"
        p.write_text(content, encoding="utf-8")
        result = import_csv(file_path=str(p))
        assert result["status"] == "ok"
        assert len(result["candidates"]) == 2
        assert len(result["skipped_rows"]) == 1

    def test_file_not_found(self):
        result = import_csv(file_path="/nonexistent/file.csv")
        assert result["status"] == "error"

    def test_empty_csv(self, tmp_path):
        p = tmp_path / "empty.csv"
        p.write_text("日付,摘要,金額\n", encoding="utf-8")
        result = import_csv(file_path=str(p))
        assert result["status"] == "ok"
        assert len(result["candidates"]) == 0
        assert result["total_rows"] == 0

    def test_original_data_preserved(self):
        csv_path = str(FIXTURES_DIR / "credit_card_simple.csv")
        result = import_csv(file_path=csv_path)
        c = result["candidates"][0]
        assert isinstance(c["original_data"], dict)
        assert len(c["original_data"]) > 0

    def test_date_detection(self):
        csv_path = str(FIXTURES_DIR / "credit_card_simple.csv")
        result = import_csv(file_path=csv_path)
        for c in result["candidates"]:
            assert c["date"].startswith("2025-")
