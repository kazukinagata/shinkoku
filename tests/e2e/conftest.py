"""E2E test conftest - scenario fixtures."""

from pathlib import Path

import pytest


def _load_scenario():
    """Load scenario data from YAML file.

    Falls back to inline Python dict if PyYAML is not installed.
    """
    try:
        import yaml
        yaml_path = Path(__file__).parent.parent / "fixtures" / "scenarios" / "salary_plus_business.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: same data as the YAML file, as a Python dict
        return _salary_plus_business_scenario()


def _salary_plus_business_scenario():
    """Salary + side business scenario as a Python dict."""
    return {
        "scenario": {
            "name": "会社員＋副業シナリオ",
            "description": "給与所得6,000,000円 + 副業（フリーランス開発）のケース",
            "fiscal_year": 2025,
            "taxpayer_name": "テスト太郎",
        },
        "salary": {
            "income": 6_000_000,
            "withheld_tax": 466_800,
        },
        "business": {
            "blue_return_deduction": 650_000,
            "revenues": [
                {"date": "2025-01-31", "description": "ウェブ開発報酬 1月分", "amount": 300_000},
                {"date": "2025-02-28", "description": "ウェブ開発報酬 2月分", "amount": 250_000},
                {"date": "2025-03-31", "description": "ウェブ開発報酬 3月分", "amount": 280_000},
                {"date": "2025-04-30", "description": "ウェブ開発報酬 4月分", "amount": 320_000},
                {"date": "2025-05-31", "description": "ウェブ開発報酬 5月分", "amount": 250_000},
                {"date": "2025-06-30", "description": "ウェブ開発報酬 6月分", "amount": 300_000},
                {"date": "2025-07-31", "description": "ウェブ開発報酬 7月分", "amount": 280_000},
                {"date": "2025-08-31", "description": "ウェブ開発報酬 8月分", "amount": 350_000},
                {"date": "2025-09-30", "description": "ウェブ開発報酬 9月分", "amount": 270_000},
                {"date": "2025-10-31", "description": "ウェブ開発報酬 10月分", "amount": 300_000},
                {"date": "2025-11-30", "description": "ウェブ開発報酬 11月分", "amount": 280_000},
                {"date": "2025-12-31", "description": "ウェブ開発報酬 12月分", "amount": 320_000},
            ],
            "total_revenue": 3_500_000,
            "expenses": [
                {"date": "2025-01-15", "description": "サーバー代", "account_code": "5140", "amount": 36_000},
                {"date": "2025-01-15", "description": "ドメイン代", "account_code": "5140", "amount": 12_000},
                {"date": "2025-03-10", "description": "PC周辺機器", "account_code": "5190", "amount": 50_000},
                {"date": "2025-06-01", "description": "技術書籍", "account_code": "5290", "amount": 30_000},
                {"date": "2025-07-15", "description": "コワーキングスペース（年間）", "account_code": "5250", "amount": 120_000},
                {"date": "2025-09-01", "description": "オンライン研修", "account_code": "5300", "amount": 50_000},
                {"date": "2025-12-31", "description": "通信費（按分50%）", "account_code": "5140", "amount": 60_000},
                {"date": "2025-12-31", "description": "消耗品費（文具等）", "account_code": "5190", "amount": 20_000},
                {"date": "2025-12-31", "description": "支払手数料", "account_code": "5310", "amount": 12_000},
                {"date": "2025-12-31", "description": "雑費", "account_code": "5270", "amount": 10_000},
            ],
            "total_expense": 400_000,
        },
        "deductions": {
            "furusato_nozei": 50_000,
        },
        "expected": {
            "income_tax": {
                "salary_income_after_deduction": 4_360_000,
                "business_income": 2_450_000,
                "total_income": 6_810_000,
                # basic=580,000 (655万超〜2,350万) + furusato=48,000 = 628,000
                "total_income_deductions": 628_000,
                # 6,810,000 - 628,000 = 6,182,000
                "taxable_income": 6_182_000,
                # 6,182,000 * 20% - 427,500 = 808,900
                "income_tax_base": 808_900,
                "total_tax_credits": 0,
                "income_tax_after_credits": 808_900,
                # 808,900 * 21/1000 = 16,986
                "reconstruction_tax": 16_986,
                # (808,900 + 16,986) = 825,886 → 825,800
                "total_tax": 825_800,
                # 825,800 - 466,800 = 359,000
                "tax_due": 359_000,
            },
            "consumption_tax": {
                "taxable_sales_10": 3_850_000,
                "special_20pct": {
                    "tax_on_sales": 350_000,
                    "tax_due": 54_600,
                    "local_tax_due": 15_400,
                    "total_due": 70_000,
                },
            },
        },
    }


@pytest.fixture
def scenario():
    """Load the salary_plus_business scenario."""
    return _load_scenario()
