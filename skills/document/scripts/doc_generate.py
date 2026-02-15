#!/usr/bin/env python3
"""帳票生成 CLI スクリプト."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from shinkoku.models import (  # noqa: E402
    BSItem,
    BSResult,
    ConsumptionTaxResult,
    IncomeTaxResult,
    PLItem,
    PLResult,
    SeparateTaxResult,
)
from shinkoku.tools.document import (  # noqa: E402
    _resolve_config,
    _resolve_taxpayer_name,
    generate_bs_pl_pdf,
    generate_consumption_tax_pdf,
    generate_full_tax_document_set,
    generate_housing_loan_detail_pdf,
    generate_income_expense_statement_pdf,
    generate_income_tax_page2_pdf,
    generate_income_tax_pdf,
    generate_medical_expense_detail_pdf,
    generate_schedule_3_pdf,
    generate_schedule_4_pdf,
)
from shinkoku.tools.pdf_utils import pdf_to_images  # noqa: E402


def _load_json(path: str) -> dict:
    """JSON ファイルを読み込んで dict を返す。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _output_json(data: dict) -> None:
    """dict を JSON として stdout に出力する。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _error_exit(message: str) -> None:
    """エラーメッセージを JSON で stdout に出力して終了する。"""
    _output_json({"status": "error", "message": message})
    sys.exit(1)


def _ensure_output_dir(output_path: str) -> None:
    """出力先ディレクトリを作成する。"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# PL/BS model construction helpers
# ============================================================


def _build_pl_data(params: dict, fiscal_year: int) -> PLResult:
    """dict から PLResult を構築する。"""
    rev_items = [PLItem(**r) for r in (params.get("pl_revenues") or [])]
    exp_items = [PLItem(**e) for e in (params.get("pl_expenses") or [])]
    return PLResult(
        fiscal_year=fiscal_year,
        revenues=rev_items,
        expenses=exp_items,
        total_revenue=sum(r.amount for r in rev_items),
        total_expense=sum(e.amount for e in exp_items),
        net_income=sum(r.amount for r in rev_items) - sum(e.amount for e in exp_items),
    )


def _build_bs_data(params: dict, fiscal_year: int) -> BSResult | None:
    """dict から BSResult を構築する。bs_assets が None なら None を返す。"""
    if params.get("bs_assets") is None:
        return None
    bs_asset_items = [BSItem(**a) for a in (params.get("bs_assets") or [])]
    bs_liab_items = [BSItem(**li) for li in (params.get("bs_liabilities") or [])]
    bs_eq_items = [BSItem(**e) for e in (params.get("bs_equity") or [])]
    return BSResult(
        fiscal_year=fiscal_year,
        assets=bs_asset_items,
        liabilities=bs_liab_items,
        equity=bs_eq_items,
        total_assets=sum(i.amount for i in bs_asset_items),
        total_liabilities=sum(i.amount for i in bs_liab_items),
        total_equity=sum(i.amount for i in bs_eq_items),
    )


# ============================================================
# Subcommand handlers
# ============================================================


def _handle_bs_pl(args: argparse.Namespace) -> None:
    """bs-pl: 青色申告決算書（BS/PL）PDF 生成。"""
    params = _load_json(args.input)
    fiscal_year = params["fiscal_year"]
    taxpayer_name = _resolve_taxpayer_name(params.get("taxpayer_name", ""), args.config_path)

    pl_data = _build_pl_data(params, fiscal_year)
    bs_data = _build_bs_data(params, fiscal_year)

    _ensure_output_dir(args.output_path)
    path = generate_bs_pl_pdf(
        pl_data=pl_data,
        bs_data=bs_data,
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path, "pages": 2 if bs_data else 1})


def _handle_income_tax(args: argparse.Namespace) -> None:
    """income-tax: 確定申告書B 第一表 PDF 生成。"""
    params = _load_json(args.input)
    taxpayer_name = _resolve_taxpayer_name(params.pop("taxpayer_name", ""), args.config_path)

    tax_result = IncomeTaxResult(**params)
    _ensure_output_dir(args.output_path)
    path = generate_income_tax_pdf(
        tax_result=tax_result,
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
        config_path=args.config_path,
    )
    _output_json({"output_path": path})


def _handle_consumption_tax(args: argparse.Namespace) -> None:
    """consumption-tax: 消費税確定申告書 PDF 生成。"""
    params = _load_json(args.input)
    taxpayer_name = _resolve_taxpayer_name(params.pop("taxpayer_name", ""), args.config_path)

    tax_result = ConsumptionTaxResult(**params)
    _ensure_output_dir(args.output_path)
    path = generate_consumption_tax_pdf(
        tax_result=tax_result,
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path})


def _handle_medical_expense(args: argparse.Namespace) -> None:
    """medical-expense: 医療費控除の明細書 PDF 生成。"""
    params = _load_json(args.input)
    taxpayer_name = _resolve_taxpayer_name(params.get("taxpayer_name", ""), args.config_path)

    _ensure_output_dir(args.output_path)
    path = generate_medical_expense_detail_pdf(
        expenses=params.get("expenses", []),
        fiscal_year=params["fiscal_year"],
        total_income=params.get("total_income", 0),
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path})


def _handle_housing_loan(args: argparse.Namespace) -> None:
    """housing-loan: 住宅ローン控除計算明細書 PDF 生成。"""
    params = _load_json(args.input)
    taxpayer_name = _resolve_taxpayer_name(params.get("taxpayer_name", ""), args.config_path)

    _ensure_output_dir(args.output_path)
    path = generate_housing_loan_detail_pdf(
        housing_detail=params.get("housing_detail", {}),
        credit_amount=params.get("credit_amount", 0),
        fiscal_year=params["fiscal_year"],
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path})


def _handle_schedule_3(args: argparse.Namespace) -> None:
    """schedule-3: 第三表（分離課税）PDF 生成。"""
    params = _load_json(args.input)
    taxpayer_name = _resolve_taxpayer_name(params.pop("taxpayer_name", ""), args.config_path)

    tax_result = SeparateTaxResult(**params)
    _ensure_output_dir(args.output_path)
    path = generate_schedule_3_pdf(
        tax_result=tax_result,
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path})


def _handle_schedule_4(args: argparse.Namespace) -> None:
    """schedule-4: 第四表（損失申告）PDF 生成。"""
    params = _load_json(args.input)
    taxpayer_name = _resolve_taxpayer_name(params.get("taxpayer_name", ""), args.config_path)

    _ensure_output_dir(args.output_path)
    path = generate_schedule_4_pdf(
        losses=params.get("losses", []),
        fiscal_year=params["fiscal_year"],
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path})


def _handle_income_expense(args: argparse.Namespace) -> None:
    """income-expense: 収支内訳書（白色申告用）PDF 生成。"""
    params = _load_json(args.input)
    fiscal_year = params["fiscal_year"]
    taxpayer_name = _resolve_taxpayer_name(params.get("taxpayer_name", ""), args.config_path)

    pl_data = _build_pl_data(params, fiscal_year)

    _ensure_output_dir(args.output_path)
    path = generate_income_expense_statement_pdf(
        pl_data=pl_data,
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path})


def _handle_income_tax_p2(args: argparse.Namespace) -> None:
    """income-tax-p2: 確定申告書B 第二表 PDF 生成。"""
    params = _load_json(args.input)
    taxpayer_name = _resolve_taxpayer_name(params.get("taxpayer_name", ""), args.config_path)

    _ensure_output_dir(args.output_path)
    path = generate_income_tax_page2_pdf(
        income_details=params.get("income_details"),
        social_insurance_details=params.get("social_insurance_details"),
        dependents=params.get("dependents"),
        spouse=params.get("spouse"),
        housing_loan_move_in_date=params.get("housing_loan_move_in_date", ""),
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
    )
    _output_json({"output_path": path})


def _handle_full_set(args: argparse.Namespace) -> None:
    """full-set: 全帳票セット一括生成。"""
    params = _load_json(args.input)
    fiscal_year = params["fiscal_year"]
    taxpayer_name = _resolve_taxpayer_name(params.get("taxpayer_name", ""), args.config_path)

    # IncomeTaxResult の構築
    income_tax_params = {
        k: params[k]
        for k in [
            "fiscal_year",
            "salary_income_after_deduction",
            "business_income",
            "total_income",
            "total_income_deductions",
            "taxable_income",
            "income_tax_base",
            "total_tax_credits",
            "income_tax_after_credits",
            "reconstruction_tax",
            "total_tax",
            "withheld_tax",
            "tax_due",
        ]
        if k in params
    }
    income_tax_params.setdefault("fiscal_year", fiscal_year)
    income_tax = IncomeTaxResult(**income_tax_params)

    # PL/BS
    pl_data = _build_pl_data(params, fiscal_year)
    bs_data = _build_bs_data(params, fiscal_year)

    # ConsumptionTaxResult (optional)
    consumption_tax = None
    if params.get("consumption_method"):
        consumption_tax = ConsumptionTaxResult(
            fiscal_year=fiscal_year,
            method=params["consumption_method"],
            taxable_sales_total=params.get("consumption_taxable_sales_total", 0),
            tax_on_sales=params.get("consumption_tax_on_sales", 0),
            tax_on_purchases=params.get("consumption_tax_on_purchases", 0),
            tax_due=params.get("consumption_tax_due", 0),
            local_tax_due=params.get("consumption_local_tax_due", 0),
            total_due=params.get("consumption_total_due", 0),
        )

    config = _resolve_config(args.config_path)

    _ensure_output_dir(args.output_path)
    path = generate_full_tax_document_set(
        income_tax=income_tax,
        pl_data=pl_data,
        bs_data=bs_data,
        consumption_tax=consumption_tax,
        income_details=params.get("income_details"),
        social_insurance_details=params.get("social_insurance_details"),
        dependents=params.get("dependents"),
        spouse=params.get("spouse"),
        housing_loan_move_in_date=params.get("housing_loan_move_in_date", ""),
        output_path=args.output_path,
        taxpayer_name=taxpayer_name,
        config=config,
    )

    num_pages = 3  # P1 + P2 + PL
    if bs_data:
        num_pages += 1
    if consumption_tax:
        num_pages += 2

    _output_json({"output_path": path, "pages": num_pages})


def _handle_preview(args: argparse.Namespace) -> None:
    """preview: PDF をページごとの画像に変換。"""
    output_dir = args.output_dir or "output/preview"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    images = pdf_to_images(args.pdf_path, output_dir, args.dpi)
    _output_json({"images": images, "num_pages": len(images)})


# ============================================================
# CLI setup
# ============================================================


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="帳票生成 CLI")
    sub = parser.add_subparsers(dest="command")

    # input + output-path + config-path を共有する subcommand
    for name in [
        "bs-pl",
        "income-tax",
        "consumption-tax",
        "medical-expense",
        "housing-loan",
        "schedule-3",
        "schedule-4",
        "income-expense",
        "income-tax-p2",
        "full-set",
    ]:
        p = sub.add_parser(name)
        p.add_argument("--input", required=True, help="入力 JSON ファイルパス")
        p.add_argument("--output-path", required=True, help="出力 PDF ファイルパス")
        p.add_argument("--config-path", default=None, help="設定 YAML ファイルパス")

    # preview は別のインターフェース
    p = sub.add_parser("preview")
    p.add_argument("--pdf-path", required=True, help="プレビュー対象 PDF パス")
    p.add_argument("--output-dir", default=None, help="画像出力ディレクトリ")
    p.add_argument("--dpi", type=int, default=150, help="解像度 (DPI)")

    return parser


_HANDLERS: dict[str, callable] = {
    "bs-pl": _handle_bs_pl,
    "income-tax": _handle_income_tax,
    "consumption-tax": _handle_consumption_tax,
    "medical-expense": _handle_medical_expense,
    "housing-loan": _handle_housing_loan,
    "schedule-3": _handle_schedule_3,
    "schedule-4": _handle_schedule_4,
    "income-expense": _handle_income_expense,
    "income-tax-p2": _handle_income_tax_p2,
    "full-set": _handle_full_set,
    "preview": _handle_preview,
}


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _HANDLERS.get(args.command)
    if handler is None:
        _error_exit(f"Unknown command: {args.command}")

    try:
        handler(args)
    except Exception as e:
        _error_exit(str(e))


if __name__ == "__main__":
    main()
