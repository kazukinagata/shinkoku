"""Tests for document generation module."""
import os
import pytest
from shinkoku.tools.document import (
    generate_bs_pl_pdf,
)
from shinkoku.models import PLResult, PLItem, BSResult, BSItem


@pytest.fixture
def sample_pl():
    """Sample P/L result for PDF generation."""
    return PLResult(
        fiscal_year=2025,
        revenues=[
            PLItem(account_code="4001", account_name="売上", amount=5_000_000),
            PLItem(account_code="4110", account_name="雑収入", amount=100_000),
        ],
        expenses=[
            PLItem(account_code="5140", account_name="通信費", amount=120_000),
            PLItem(account_code="5250", account_name="地代家賃", amount=600_000),
            PLItem(account_code="5200", account_name="減価償却費", amount=200_000),
            PLItem(account_code="5190", account_name="消耗品費", amount=80_000),
        ],
        total_revenue=5_100_000,
        total_expense=1_000_000,
        net_income=4_100_000,
    )


@pytest.fixture
def sample_bs():
    """Sample B/S result for PDF generation."""
    return BSResult(
        fiscal_year=2025,
        assets=[
            BSItem(account_code="1001", account_name="現金", amount=500_000),
            BSItem(account_code="1002", account_name="普通預金", amount=3_000_000),
            BSItem(account_code="1010", account_name="売掛金", amount=200_000),
            BSItem(account_code="1130", account_name="工具器具備品", amount=800_000),
        ],
        liabilities=[
            BSItem(account_code="2030", account_name="未払金", amount=100_000),
        ],
        equity=[
            BSItem(account_code="3001", account_name="元入金", amount=300_000),
            BSItem(account_code="3020", account_name="控除前所得金額", amount=4_100_000),
        ],
        total_assets=4_500_000,
        total_liabilities=100_000,
        total_equity=4_400_000,
    )


class TestGenerateBsPl:
    """Test blue return BS/PL PDF generation."""

    def test_generates_pdf_file(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        assert os.path.exists(result)
        assert result == output

    def test_pdf_not_empty(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        size = os.path.getsize(output)
        assert size > 100  # PDF should have some content

    def test_pdf_starts_with_magic(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        with open(output, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_with_taxpayer_name(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
            taxpayer_name="テスト太郎",
        )
        assert os.path.exists(result)

    def test_creates_parent_directories(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "nested" / "dir" / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_pl_only(self, tmp_path, sample_pl):
        output = str(tmp_path / "pl_only.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=None,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_returns_string_path(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        assert isinstance(result, str)
