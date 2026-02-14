"""Tests for import_data tools."""

from pathlib import Path

from shinkoku.tools.import_data import (
    import_csv,
    import_receipt,
    import_invoice,
    import_withholding,
)

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


# ============================================================
# Task 12: import_receipt + import_invoice + import_withholding
# ============================================================


class TestImportReceipt:
    def test_receipt_existing_file(self, tmp_path):
        p = tmp_path / "receipt.jpg"
        p.write_bytes(b"\xff\xd8\xff")  # minimal JPEG header
        result = import_receipt(file_path=str(p))
        assert result["status"] == "ok"
        assert result["file_path"] == str(p)
        # Should return a template with None fields for Claude to fill
        assert result["date"] is None
        assert result["vendor"] is None
        assert result["total_amount"] is None
        assert "items" in result

    def test_receipt_file_not_found(self):
        result = import_receipt(file_path="/nonexistent/receipt.jpg")
        assert result["status"] == "error"

    def test_receipt_returns_template(self, tmp_path):
        p = tmp_path / "receipt.png"
        p.write_bytes(b"\x89PNG")
        result = import_receipt(file_path=str(p))
        assert result["tax_included"] is True


class TestImportInvoice:
    def test_invoice_pdf(self, tmp_path):
        # Create a minimal PDF-like file for testing
        # pdfplumber needs a real PDF, so test with a mock approach
        p = tmp_path / "invoice.pdf"
        # We test with a file that pdfplumber cannot parse => extracted_text = ""
        p.write_text("not a real pdf")
        result = import_invoice(file_path=str(p))
        # Even with bad PDF, should return a result (possibly empty text)
        assert result["file_path"] == str(p)

    def test_invoice_file_not_found(self):
        result = import_invoice(file_path="/nonexistent/invoice.pdf")
        assert result["status"] == "error"

    def test_invoice_returns_structure(self, tmp_path):
        p = tmp_path / "invoice.pdf"
        p.write_text("not a real pdf")
        result = import_invoice(file_path=str(p))
        assert "extracted_text" in result
        assert "vendor" in result
        assert "invoice_number" in result


class TestImportWithholding:
    def test_withholding_file_not_found(self):
        result = import_withholding(file_path="/nonexistent/slip.pdf")
        assert result["status"] == "error"

    def test_withholding_returns_structure(self, tmp_path):
        p = tmp_path / "withholding.pdf"
        p.write_text("not a real pdf")
        result = import_withholding(file_path=str(p))
        assert "extracted_text" in result
        assert "payer_name" in result
        assert "payment_amount" in result
        assert "withheld_tax" in result
        assert "social_insurance" in result

    def test_withholding_amounts_default_zero(self, tmp_path):
        p = tmp_path / "withholding.pdf"
        p.write_text("not a real pdf")
        result = import_withholding(file_path=str(p))
        assert result["payment_amount"] == 0
        assert result["withheld_tax"] == 0
        assert result["social_insurance"] == 0


# ============================================================
# import_payment_statement
# ============================================================


class TestImportPaymentStatement:
    def test_file_not_found(self):
        from shinkoku.tools.import_data import import_payment_statement

        result = import_payment_statement(file_path="/nonexistent/statement.pdf")
        assert result["status"] == "error"

    def test_pdf_file(self, tmp_path):
        from shinkoku.tools.import_data import import_payment_statement

        p = tmp_path / "statement.pdf"
        p.write_text("not a real pdf")
        result = import_payment_statement(file_path=str(p))
        assert result["status"] == "ok"
        assert result["file_path"] == str(p)
        assert "extracted_text" in result

    def test_image_file(self, tmp_path):
        from shinkoku.tools.import_data import import_payment_statement

        p = tmp_path / "statement.jpg"
        p.write_bytes(b"\xff\xd8\xff")
        result = import_payment_statement(file_path=str(p))
        assert result["status"] == "ok"
        assert result["extracted_text"] == ""

    def test_template_fields(self, tmp_path):
        from shinkoku.tools.import_data import import_payment_statement

        p = tmp_path / "statement.png"
        p.write_bytes(b"\x89PNG")
        result = import_payment_statement(file_path=str(p))
        assert result["payer_name"] is None
        assert result["category"] is None
        assert result["gross_amount"] is None
        assert result["withholding_tax"] is None
