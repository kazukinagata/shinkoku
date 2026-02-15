"""Integration tests: Tax Calculation -> xtx XML generation flow.

Verifies end-to-end xtx generation from DB data through tax calculation
to valid XML output files.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from shinkoku.models import (
    JournalEntry,
    JournalLine,
)
from shinkoku.tools.ledger import (
    ledger_add_journals_batch,
    ledger_init,
)

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def business_db(tmp_path):
    """DB with realistic freelance business data.

    Revenue: 5,000,000
    Expenses: 1,000,000 (通信費120K, 家賃600K, 消耗品80K, 減価償却200K)
    Net Income: 4,000,000
    """
    db_path = str(tmp_path / "xtx_test.db")
    ledger_init(fiscal_year=2025, db_path=db_path)

    entries = [
        JournalEntry(
            date="2025-01-31",
            description="1月売上",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=2_000_000),
                JournalLine(side="credit", account_code="4001", amount=2_000_000),
            ],
        ),
        JournalEntry(
            date="2025-06-30",
            description="6月売上",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=1_500_000),
                JournalLine(side="credit", account_code="4001", amount=1_500_000),
            ],
        ),
        JournalEntry(
            date="2025-12-31",
            description="12月売上",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=1_500_000),
                JournalLine(side="credit", account_code="4001", amount=1_500_000),
            ],
        ),
        JournalEntry(
            date="2025-01-31",
            description="通信費(年間)",
            lines=[
                JournalLine(side="debit", account_code="5140", amount=120_000),
                JournalLine(side="credit", account_code="1002", amount=120_000),
            ],
        ),
        JournalEntry(
            date="2025-01-31",
            description="家賃(年間)",
            lines=[
                JournalLine(side="debit", account_code="5250", amount=600_000),
                JournalLine(side="credit", account_code="1002", amount=600_000),
            ],
        ),
        JournalEntry(
            date="2025-03-15",
            description="消耗品",
            lines=[
                JournalLine(side="debit", account_code="5190", amount=80_000),
                JournalLine(side="credit", account_code="1001", amount=80_000),
            ],
        ),
        JournalEntry(
            date="2025-12-31",
            description="減価償却費",
            lines=[
                JournalLine(side="debit", account_code="5200", amount=200_000),
                JournalLine(side="credit", account_code="1130", amount=200_000),
            ],
        ),
        JournalEntry(
            date="2025-01-01",
            description="元入金",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=500_000),
                JournalLine(side="credit", account_code="3001", amount=500_000),
            ],
        ),
    ]
    ledger_add_journals_batch(db_path=db_path, fiscal_year=2025, entries=entries)
    return db_path


@pytest.fixture
def config_file(tmp_path):
    """Minimal config YAML for xtx generation."""
    config_path = tmp_path / "shinkoku.config.yaml"
    config_path.write_text(
        """\
tax_year: 2025
db_path: "{db_path}"
output_dir: "{output_dir}"

taxpayer:
  last_name: "山田"
  first_name: "太郎"
  last_name_kana: "ヤマダ"
  first_name_kana: "タロウ"
  gender: "1"
  date_of_birth: "1985-05-15"
  phone: "090-1234-5678"
  my_number: "123456789012"

address:
  postal_code: "1000001"
  prefecture: "東京都"
  city: "千代田区"
  street: "千代田1-1"
  building: ""

business:
  trade_name: "山田技研"
  industry_type: "情報通信業"
  business_description: "ソフトウェア開発"

filing:
  submission_method: "e-tax"
  return_type: "blue"
  blue_return_deduction: 650000
  tax_office_name: "千代田税務署"
""",
        encoding="utf-8",
    )
    return str(config_path)


# ============================================================
# Helper
# ============================================================

_NS = "http://xml.e-tax.nta.go.jp/XSD/shotoku"
_NS_SHOHI = "http://xml.e-tax.nta.go.jp/XSD/shohi"


def _find(root: ET.Element, tag: str, ns: str = _NS) -> ET.Element | None:
    """名前空間付きで要素を検索する。"""
    return root.find(f"{{{ns}}}{tag}")


def _findall(root: ET.Element, tag: str, ns: str = _NS) -> list[ET.Element]:
    return root.findall(f".//{{{ns}}}{tag}")


# ============================================================
# Tests: generate_xtx module functions
# ============================================================


class TestGenerateXtxModule:
    """Test the generate_xtx module functions directly."""

    def test_generate_income_tax_xtx_produces_valid_xml(self, business_db, config_file, tmp_path):
        """所得税 xtx を生成し、有効な XML であることを検証する。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # config のパスを実 DB に差し替え
        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        # xtx ファイルが生成されること
        assert result["status"] == "ok"
        xtx_path = Path(result["output_path"])
        assert xtx_path.exists()
        assert xtx_path.suffix == ".xtx"

        # XML として valid であること
        tree = ET.parse(xtx_path)
        root = tree.getroot()
        assert root.tag == f"{{{_NS}}}DATA"

    def test_income_tax_xtx_contains_form_data(self, business_db, config_file, tmp_path):
        """所得税 xtx に帳票データが含まれていることを検証する。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        xtx_path = Path(result["output_path"])
        tree = ET.parse(xtx_path)
        root = tree.getroot()

        # RKO0010 手続きコード要素が存在すること
        rko = _find(root, "RKO0010")
        assert rko is not None

        # KOA020（申告書B）が含まれること
        koa020_list = _findall(root, "KOA020")
        assert len(koa020_list) >= 1

        # KOA210（青色申告決算書）が含まれること
        koa210_list = _findall(root, "KOA210")
        assert len(koa210_list) >= 1

    def test_income_tax_xtx_has_taxpayer_info(self, business_db, config_file, tmp_path):
        """所得税 xtx に納税者情報（IT部）が含まれることを検証する。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        xtx_path = Path(result["output_path"])
        xml_str = xtx_path.read_text(encoding="utf-8")

        # 納税者名が含まれること
        assert "山田太郎" in xml_str or "山田" in xml_str
        # マイナンバーが含まれること
        assert "123456789012" in xml_str

    def test_income_tax_xtx_business_income_correct(self, business_db, config_file, tmp_path):
        """所得税 xtx の事業所得が PL データに基づいて正しいことを検証する。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        xtx_path = Path(result["output_path"])
        xml_str = xtx_path.read_text(encoding="utf-8")

        # 事業所得 = 5,000,000 - 1,000,000 - 650,000(青色) = 3,350,000
        assert "3350000" in xml_str

        # forms に含まれる帳票一覧
        assert "forms" in result
        form_codes = [f["form_code"] for f in result["forms"]]
        assert "KOA020" in form_codes
        assert "KOA210" in form_codes

    def test_generate_consumption_tax_xtx(self, business_db, config_file, tmp_path):
        """消費税 xtx を生成できることを検証する。"""
        from shinkoku.xtx.generate_xtx import generate_consumption_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_consumption_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        assert result["status"] == "ok"
        xtx_path = Path(result["output_path"])
        assert xtx_path.exists()

        # 消費税 XML として valid
        tree = ET.parse(xtx_path)
        root = tree.getroot()
        assert root.tag == f"{{{_NS_SHOHI}}}DATA"

    def test_generate_all_xtx(self, business_db, config_file, tmp_path):
        """所得税と消費税の両方を一括生成できることを検証する。"""
        from shinkoku.xtx.generate_xtx import generate_all_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        results = generate_all_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        assert len(results) >= 1  # 少なくとも所得税
        for r in results:
            assert r["status"] == "ok"
            assert Path(r["output_path"]).exists()


class TestGenerateXtxW2W5Fields:
    """W2-W5 IT部フィールドが config から xtx に反映されることを検証する。"""

    @pytest.fixture
    def config_with_w2w5(self, tmp_path):
        """W2-W5 フィールドを含む config YAML。"""
        config_path = tmp_path / "w2w5.config.yaml"
        config_path.write_text(
            """\
tax_year: 2025
db_path: "{db_path}"
output_dir: "{output_dir}"

taxpayer:
  last_name: "山田"
  first_name: "太郎"
  last_name_kana: "ヤマダ"
  first_name_kana: "タロウ"
  gender: "1"
  date_of_birth: "1985-05-15"
  phone: "090-1234-5678"
  my_number: "123456789012"

address:
  postal_code: "1000001"
  prefecture: "東京都"
  city: "千代田区"
  street: "千代田1-1"
  building: ""
  address_kana: "ﾄｳｷｮｳﾄ ﾁﾖﾀﾞｸ ﾁﾖﾀﾞ1-1"

business:
  trade_name: "山田技研"
  industry_type: "情報通信業"
  business_description: "ソフトウェア開発"

filing:
  submission_method: "e-tax"
  return_type: "blue"
  blue_return_deduction: 650000
  tax_office_name: "千代田税務署"
  seiribango: "12345678"

refund_account:
  bank_name: "みずほ銀行"
  branch_name: "丸の内支店"
  account_type: "普通"
  account_number: "1234567"
  account_holder: "ﾔﾏﾀﾞ ﾀﾛｳ"
""",
            encoding="utf-8",
        )
        return str(config_path)

    def test_w5_address_kana_in_xtx(self, business_db, config_with_w2w5, tmp_path):
        """W5: 住所フリガナが xtx XML に含まれること。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_with_w2w5).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched_w2w5.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        xtx_path = Path(result["output_path"])
        xml_str = xtx_path.read_text(encoding="utf-8")
        assert "ﾄｳｷｮｳﾄ ﾁﾖﾀﾞｸ ﾁﾖﾀﾞ1-1" in xml_str

    def test_w4_seiribango_in_xtx(self, business_db, config_with_w2w5, tmp_path):
        """W4: 整理番号が SEIRIBANGO 要素として xtx XML に含まれること。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_with_w2w5).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched_w2w5.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        xtx_path = Path(result["output_path"])
        tree = ET.parse(xtx_path)
        root = tree.getroot()
        seiribango = _findall(root, "SEIRIBANGO")
        assert len(seiribango) >= 1
        assert seiribango[0].text == "12345678"

    def test_w2_refund_bank_in_xtx(self, business_db, config_with_w2w5, tmp_path):
        """W2: 還付金融機関が xtx XML に含まれること。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_with_w2w5).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched_w2w5.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
        )

        xtx_path = Path(result["output_path"])
        xml_str = xtx_path.read_text(encoding="utf-8")
        assert "みずほ銀行" in xml_str
        assert "丸の内支店" in xml_str
        assert "KANPU_KINYUKIKAN" in xml_str


class TestGenerateXtxDbPathOverride:
    """--db-path による DB パスのオーバーライドテスト。"""

    def test_db_path_override(self, business_db, config_file, tmp_path):
        """db_path_override を指定すると config の db_path を上書きする。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # config の db_path は存在しないパスにする
        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", "/nonexistent/db.sqlite")
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        # db_path_override で実際の DB を指定すればエラーにならない
        result = generate_income_tax_xtx(
            config_path=str(patched_config),
            output_dir=str(output_dir),
            db_path_override=business_db,
        )

        assert result["status"] == "ok"
        assert Path(result["output_path"]).exists()


class TestGenerateXtxMissingConfig:
    """Error handling tests."""

    def test_missing_config_raises_error(self, tmp_path):
        """存在しない config を指定した場合、FileNotFoundError になること。"""
        from shinkoku.xtx.generate_xtx import generate_income_tax_xtx

        with pytest.raises(FileNotFoundError):
            generate_income_tax_xtx(
                config_path="/nonexistent/config.yaml",
                output_dir=str(tmp_path),
            )


class TestCliScript:
    """Test the CLI script entrypoint."""

    def test_cli_income_tax(self, business_db, config_file, tmp_path):
        """CLI で --type income_tax を指定して xtx 生成できること。"""
        import subprocess

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "scripts/generate_xtx.py",
                "--config",
                str(patched_config),
                "--output-dir",
                str(output_dir),
                "--type",
                "income_tax",
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # xtx ファイルが存在すること
        xtx_files = list(output_dir.glob("*.xtx"))
        assert len(xtx_files) >= 1

    def test_cli_all(self, business_db, config_file, tmp_path):
        """CLI で --type all を指定して全種類の xtx を生成できること。"""
        import subprocess

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", business_db)
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "scripts/generate_xtx.py",
                "--config",
                str(patched_config),
                "--output-dir",
                str(output_dir),
                "--type",
                "all",
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        xtx_files = list(output_dir.glob("*.xtx"))
        assert len(xtx_files) >= 1

    def test_cli_db_path_override(self, business_db, config_file, tmp_path):
        """CLI で --db-path を指定して DB パスをオーバーライドできること。"""
        import subprocess

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # config の db_path は存在しないパスにする
        config_text = Path(config_file).read_text(encoding="utf-8")
        config_text = config_text.replace("{db_path}", "/nonexistent/db.sqlite")
        config_text = config_text.replace("{output_dir}", str(output_dir))
        patched_config = tmp_path / "patched.config.yaml"
        patched_config.write_text(config_text, encoding="utf-8")

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "scripts/generate_xtx.py",
                "--config",
                str(patched_config),
                "--output-dir",
                str(output_dir),
                "--db-path",
                business_db,
                "--type",
                "income_tax",
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        xtx_files = list(output_dir.glob("*.xtx"))
        assert len(xtx_files) >= 1
