"""Tests for furusato nozei tools."""

from __future__ import annotations

import pytest

from shinkoku.tools.furusato import (
    add_furusato_donation,
    list_furusato_donations,
    delete_furusato_donation,
    summarize_furusato_donations,
)
from shinkoku.tools.tax_calc import calc_furusato_deduction, calc_furusato_deduction_limit


class TestAddFurusatoDonation:
    def test_add_donation(self, sample_furusato_donations):
        db = sample_furusato_donations
        donation_id = add_furusato_donation(
            conn=db,
            fiscal_year=2025,
            municipality_name="東京都渋谷区",
            amount=10000,
            date="2025-11-01",
            municipality_prefecture="東京都",
        )
        assert donation_id > 0

    def test_add_donation_with_all_fields(self, sample_furusato_donations):
        db = sample_furusato_donations
        donation_id = add_furusato_donation(
            conn=db,
            fiscal_year=2025,
            municipality_name="大阪府大阪市",
            amount=50000,
            date="2025-07-15",
            municipality_prefecture="大阪府",
            receipt_number="R-999",
            one_stop_applied=True,
            source_file="/path/to/receipt.jpg",
        )
        assert donation_id > 0
        donations = list_furusato_donations(db, 2025)
        added = [d for d in donations if d.id == donation_id][0]
        assert added.municipality_name == "大阪府大阪市"
        assert added.one_stop_applied is True
        assert added.receipt_number == "R-999"

    def test_invalid_date_format_rejected(self, sample_furusato_donations):
        db = sample_furusato_donations
        with pytest.raises(ValueError, match="日付の形式が不正です"):
            add_furusato_donation(
                conn=db,
                fiscal_year=2025,
                municipality_name="東京都渋谷区",
                amount=10000,
                date="2025/11/01",
            )

    def test_invalid_date_format_no_separator(self, sample_furusato_donations):
        db = sample_furusato_donations
        with pytest.raises(ValueError, match="日付の形式が不正です"):
            add_furusato_donation(
                conn=db,
                fiscal_year=2025,
                municipality_name="東京都渋谷区",
                amount=10000,
                date="not-a-date",
            )


class TestListFurusatoDonations:
    def test_list_existing(self, sample_furusato_donations):
        donations = list_furusato_donations(sample_furusato_donations, 2025)
        assert len(donations) == 3

    def test_list_empty_year(self, in_memory_db_with_accounts):
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2024)")
        db.commit()
        donations = list_furusato_donations(db, 2024)
        assert len(donations) == 0

    def test_list_ordered_by_date(self, sample_furusato_donations):
        donations = list_furusato_donations(sample_furusato_donations, 2025)
        dates = [d.date for d in donations]
        assert dates == sorted(dates)

    def test_amounts_are_int(self, sample_furusato_donations):
        donations = list_furusato_donations(sample_furusato_donations, 2025)
        for d in donations:
            assert isinstance(d.amount, int)


class TestDeleteFurusatoDonation:
    def test_delete_existing(self, sample_furusato_donations):
        donations = list_furusato_donations(sample_furusato_donations, 2025)
        target_id = donations[0].id
        result = delete_furusato_donation(sample_furusato_donations, target_id)
        assert result is True
        remaining = list_furusato_donations(sample_furusato_donations, 2025)
        assert len(remaining) == 2

    def test_delete_nonexistent(self, sample_furusato_donations):
        result = delete_furusato_donation(sample_furusato_donations, 99999)
        assert result is False


class TestSummarizeFurusatoDonations:
    def test_summary_totals(self, sample_furusato_donations):
        summary = summarize_furusato_donations(sample_furusato_donations, 2025)
        assert summary.total_amount == 100000  # 30000 + 50000 + 20000
        assert summary.donation_count == 3
        assert summary.municipality_count == 3

    def test_summary_deduction(self, sample_furusato_donations):
        summary = summarize_furusato_donations(sample_furusato_donations, 2025)
        # 100,000 - 2,000 = 98,000
        assert summary.deduction_amount == 98000

    def test_summary_one_stop_count(self, sample_furusato_donations):
        summary = summarize_furusato_donations(sample_furusato_donations, 2025)
        assert summary.one_stop_count == 1  # 福岡市のみ

    def test_summary_needs_tax_return(self, sample_furusato_donations):
        # 副業ユーザーは常に確定申告が必要
        summary = summarize_furusato_donations(sample_furusato_donations, 2025)
        assert summary.needs_tax_return is True

    def test_summary_over_limit(self, sample_furusato_donations):
        summary = summarize_furusato_donations(
            sample_furusato_donations, 2025, estimated_limit=50000
        )
        assert summary.over_limit is True

    def test_summary_under_limit(self, sample_furusato_donations):
        summary = summarize_furusato_donations(
            sample_furusato_donations, 2025, estimated_limit=200000
        )
        assert summary.over_limit is False

    def test_summary_empty(self, in_memory_db_with_accounts):
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2024)")
        db.commit()
        summary = summarize_furusato_donations(db, 2024)
        assert summary.total_amount == 0
        assert summary.donation_count == 0
        assert summary.deduction_amount == 0


class TestFurusatoDeduction:
    def test_basic_deduction(self):
        assert calc_furusato_deduction(100000) == 98000

    def test_minimum_deduction(self):
        assert calc_furusato_deduction(2001) == 1

    def test_at_threshold(self):
        assert calc_furusato_deduction(2000) == 0

    def test_below_threshold(self):
        assert calc_furusato_deduction(1000) == 0

    def test_zero(self):
        assert calc_furusato_deduction(0) == 0


class TestFurusatoDeductionLimit:
    def test_typical_salary_worker(self):
        # 年収500万、課税所得約250万のケース
        limit = calc_furusato_deduction_limit(
            total_income=3_500_000,
            total_income_deductions=1_000_000,
        )
        # 課税所得250万→税率10%
        # 住民税所得割=250万×10%=25万
        # 上限≈25万×20%÷(100%-10%×1.021-10%)+2,000
        assert limit > 0
        assert isinstance(limit, int)

    def test_zero_income(self):
        limit = calc_furusato_deduction_limit(total_income=0, total_income_deductions=0)
        assert limit == 0

    def test_deductions_exceed_income(self):
        limit = calc_furusato_deduction_limit(
            total_income=1_000_000, total_income_deductions=2_000_000
        )
        assert limit == 0

    def test_explicit_tax_rate(self):
        limit = calc_furusato_deduction_limit(
            total_income=5_000_000,
            total_income_deductions=1_500_000,
            income_tax_rate_percent=10,
        )
        assert limit > 0

    def test_high_income(self):
        limit = calc_furusato_deduction_limit(
            total_income=20_000_000,
            total_income_deductions=3_000_000,
        )
        # High income → higher limit
        assert limit > 100_000
