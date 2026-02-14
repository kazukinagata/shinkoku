"""Tests for master account definitions."""

from shinkoku.master_accounts import MASTER_ACCOUNTS


def test_master_accounts_has_all_categories():
    """All five accounting categories must be present."""
    categories = {a["category"] for a in MASTER_ACCOUNTS}
    assert categories == {"asset", "liability", "equity", "revenue", "expense"}


def test_master_accounts_codes_unique():
    """Account codes must be unique."""
    codes = [a["code"] for a in MASTER_ACCOUNTS]
    assert len(codes) == len(set(codes)), (
        f"Duplicate codes found: {len(codes)} vs {len(set(codes))}"
    )


def test_master_accounts_code_format():
    """All codes must be 4-digit strings."""
    for a in MASTER_ACCOUNTS:
        assert len(a["code"]) == 4, f"Code {a['code']} is not 4 digits"
        assert a["code"].isdigit(), f"Code {a['code']} is not numeric"


def test_master_accounts_code_ranges():
    """Codes must follow the category convention: 1xxx=asset, 2xxx=liability, 3xxx=equity, 4xxx=revenue, 5xxx=expense."""
    prefix_map = {
        "1": "asset",
        "2": "liability",
        "3": "equity",
        "4": "revenue",
        "5": "expense",
    }
    for a in MASTER_ACCOUNTS:
        prefix = a["code"][0]
        assert prefix in prefix_map, f"Code {a['code']} has unexpected prefix {prefix}"
        assert a["category"] == prefix_map[prefix], (
            f"Code {a['code']} prefix {prefix} should map to {prefix_map[prefix]} but has {a['category']}"
        )


def test_master_accounts_tax_categories_valid():
    """tax_category must be one of the allowed values or None."""
    valid = {"taxable", "non_taxable", "exempt", "out_of_scope", None}
    for a in MASTER_ACCOUNTS:
        assert a.get("tax_category") in valid, (
            f"Account {a['code']} {a['name']} has invalid tax_category: {a.get('tax_category')}"
        )


def test_master_accounts_required_fields():
    """Each account must have code, name, category, sub_category keys."""
    required_keys = {"code", "name", "category", "sub_category", "tax_category"}
    for a in MASTER_ACCOUNTS:
        assert required_keys.issubset(a.keys()), (
            f"Account {a.get('code', '?')} is missing keys: {required_keys - a.keys()}"
        )


def test_master_accounts_has_essential_accounts():
    """Must include key accounts needed for sole proprietor blue return."""
    names = {a["name"] for a in MASTER_ACCOUNTS}
    essential = {
        "現金",
        "普通預金",
        "売掛金",
        "事業主貸",
        "事業主借",
        "売上",
        "仕入",
    }
    missing = essential - names
    assert not missing, f"Missing essential accounts: {missing}"


def test_master_accounts_sub_categories_present():
    """Each category should have at least one sub_category value."""
    for cat in ("asset", "liability", "equity", "revenue", "expense"):
        accounts = [a for a in MASTER_ACCOUNTS if a["category"] == cat]
        sub_cats = {a["sub_category"] for a in accounts}
        assert sub_cats, f"Category {cat} has no sub_categories"
        # sub_category should not be all None
        assert sub_cats != {None}, f"Category {cat} has only None sub_categories"


def test_master_accounts_minimum_count():
    """Should have a reasonable number of accounts (at least 40)."""
    assert len(MASTER_ACCOUNTS) >= 40, f"Only {len(MASTER_ACCOUNTS)} accounts defined"
