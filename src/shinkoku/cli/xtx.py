"""xtx ファイル生成 CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from shinkoku.xtx.generate_xtx import (
    generate_all_xtx,
    generate_consumption_tax_xtx,
    generate_income_tax_xtx,
)


def _print_result(result: dict[str, Any]) -> None:
    """生成結果を表示する。"""
    status = result.get("status", "unknown")
    output_path = result.get("output_path", "N/A")
    forms = result.get("forms", [])
    warnings = result.get("warnings", [])

    print(f"Status: {status}")
    print(f"Output: {output_path}")

    if forms:
        print("Forms:")
        for f in forms:
            print(f"  - {f['form_code']}: {f.get('description', '')}")

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")

    if "tax_result" in result:
        print("Tax summary:")
        for k, v in result["tax_result"].items():
            print(f"  {k}: {v:,}")

    print()


def _run(args: argparse.Namespace) -> None:
    # 出力ディレクトリ作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    db_path = args.db_path or ""

    if args.type == "income_tax":
        result = generate_income_tax_xtx(
            config_path=args.config,
            output_dir=str(output_dir),
            db_path_override=db_path,
        )
        _print_result(result)

    elif args.type == "consumption_tax":
        result = generate_consumption_tax_xtx(
            config_path=args.config,
            output_dir=str(output_dir),
            db_path_override=db_path,
        )
        _print_result(result)

    elif args.type == "all":
        results = generate_all_xtx(
            config_path=args.config,
            output_dir=str(output_dir),
            db_path_override=db_path,
        )
        for r in results:
            _print_result(r)


def register(parent_subparsers: argparse._SubParsersAction) -> None:
    """xtx サブコマンドを親パーサーに登録する。"""
    parser = parent_subparsers.add_parser(
        "xtx",
        description="e-Tax xtx ファイル生成",
        help="e-Tax XML 生成",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="shinkoku.config.yaml のパス",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="xtx ファイルの出力先ディレクトリ",
    )
    parser.add_argument(
        "--db-path",
        default="",
        help="DB ファイルパス（省略時は config の db_path を使用）",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["income_tax", "consumption_tax", "all"],
        help="生成する帳票の種類",
    )
    parser.set_defaults(func=_run)
