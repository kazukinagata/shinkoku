#!/usr/bin/env python3
"""データ取込 CLI スクリプト."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from shinkoku.tools.import_data import (  # noqa: E402
    import_check_csv_imported,
    import_csv,
    import_deduction_certificate,
    import_furusato_receipt,
    import_invoice,
    import_payment_statement,
    import_receipt,
    import_record_source,
    import_withholding,
)


def cmd_csv(args: argparse.Namespace) -> dict:
    return import_csv(file_path=args.file_path)


def cmd_receipt(args: argparse.Namespace) -> dict:
    return import_receipt(file_path=args.file_path)


def cmd_invoice(args: argparse.Namespace) -> dict:
    return import_invoice(file_path=args.file_path)


def cmd_withholding(args: argparse.Namespace) -> dict:
    return import_withholding(file_path=args.file_path)


def cmd_furusato_receipt(args: argparse.Namespace) -> dict:
    return import_furusato_receipt(file_path=args.file_path)


def cmd_payment_statement(args: argparse.Namespace) -> dict:
    return import_payment_statement(file_path=args.file_path)


def cmd_deduction_certificate(args: argparse.Namespace) -> dict:
    return import_deduction_certificate(file_path=args.file_path)


def cmd_check_imported(args: argparse.Namespace) -> dict:
    return import_check_csv_imported(
        db_path=args.db_path,
        fiscal_year=args.fiscal_year,
        file_path=args.file_path,
    )


def cmd_record_source(args: argparse.Namespace) -> dict:
    return import_record_source(
        db_path=args.db_path,
        fiscal_year=args.fiscal_year,
        file_path=args.file_path,
        row_count=args.row_count,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="データ取込 CLI")
    sub = parser.add_subparsers(dest="command")

    # csv
    p = sub.add_parser("csv", help="CSV ファイルをパースして仕訳候補を返す")
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_csv)

    # receipt
    p = sub.add_parser("receipt", help="レシート画像の存在チェック＋テンプレート返却")
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_receipt)

    # invoice
    p = sub.add_parser("invoice", help="請求書 PDF テキスト抽出")
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_invoice)

    # withholding
    p = sub.add_parser("withholding", help="源泉徴収票 PDF テキスト抽出")
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_withholding)

    # furusato-receipt
    p = sub.add_parser("furusato-receipt", help="ふるさと納税受領証明書テンプレート返却")
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_furusato_receipt)

    # payment-statement
    p = sub.add_parser("payment-statement", help="支払調書テンプレート返却")
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_payment_statement)

    # deduction-certificate
    p = sub.add_parser("deduction-certificate", help="控除証明書テンプレート返却")
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_deduction_certificate)

    # check-imported
    p = sub.add_parser("check-imported", help="CSV インポート済みチェック")
    p.add_argument("--db-path", required=True)
    p.add_argument("--fiscal-year", required=True, type=int)
    p.add_argument("--file-path", required=True)
    p.set_defaults(func=cmd_check_imported)

    # record-source
    p = sub.add_parser("record-source", help="インポート元ファイル記録")
    p.add_argument("--db-path", required=True)
    p.add_argument("--fiscal-year", required=True, type=int)
    p.add_argument("--file-path", required=True)
    p.add_argument("--row-count", type=int, default=0)
    p.set_defaults(func=cmd_record_source)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        result = args.func(args)
    except Exception as e:
        result = {"status": "error", "message": str(e)}

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()

    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
