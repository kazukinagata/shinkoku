#!/usr/bin/env python3
"""ふるさと納税 CLI スクリプト."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from shinkoku.db import get_connection  # noqa: E402
from shinkoku.tools.furusato import (  # noqa: E402
    add_furusato_donation,
    delete_furusato_donation,
    list_furusato_donations,
    summarize_furusato_donations,
)


def cmd_add(args: argparse.Namespace) -> dict:
    params = json.loads(Path(args.input).read_text(encoding="utf-8"))
    conn = get_connection(args.db_path)
    try:
        donation_id = add_furusato_donation(
            conn=conn,
            fiscal_year=params["fiscal_year"],
            municipality_name=params["municipality_name"],
            amount=params["amount"],
            date=params["date"],
            municipality_prefecture=params.get("municipality_prefecture"),
            receipt_number=params.get("receipt_number"),
            one_stop_applied=params.get("one_stop_applied", False),
            source_file=params.get("source_file"),
        )
        return {"status": "ok", "donation_id": donation_id}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


def cmd_list(args: argparse.Namespace) -> dict:
    conn = get_connection(args.db_path)
    try:
        donations = list_furusato_donations(conn, args.fiscal_year)
        return {
            "status": "ok",
            "donations": [d.model_dump() for d in donations],
            "count": len(donations),
        }
    finally:
        conn.close()


def cmd_delete(args: argparse.Namespace) -> dict:
    conn = get_connection(args.db_path)
    try:
        deleted = delete_furusato_donation(conn, args.donation_id)
        if not deleted:
            return {"status": "error", "message": f"Donation {args.donation_id} not found"}
        return {"status": "ok", "donation_id": args.donation_id}
    finally:
        conn.close()


def cmd_summary(args: argparse.Namespace) -> dict:
    conn = get_connection(args.db_path)
    try:
        summary = summarize_furusato_donations(
            conn, args.fiscal_year, estimated_limit=args.estimated_limit
        )
        return {"status": "ok", **summary.model_dump()}
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ふるさと納税 CLI")
    sub = parser.add_subparsers(dest="command")

    # add
    p = sub.add_parser("add", help="寄附を登録")
    p.add_argument("--db-path", required=True)
    p.add_argument("--input", required=True, help="JSON ファイルパス")
    p.set_defaults(func=cmd_add)

    # list
    p = sub.add_parser("list", help="寄附一覧")
    p.add_argument("--db-path", required=True)
    p.add_argument("--fiscal-year", required=True, type=int)
    p.set_defaults(func=cmd_list)

    # delete
    p = sub.add_parser("delete", help="寄附を削除")
    p.add_argument("--db-path", required=True)
    p.add_argument("--donation-id", required=True, type=int)
    p.set_defaults(func=cmd_delete)

    # summary
    p = sub.add_parser("summary", help="寄附集計")
    p.add_argument("--db-path", required=True)
    p.add_argument("--fiscal-year", required=True, type=int)
    p.add_argument("--estimated-limit", type=int, default=None)
    p.set_defaults(func=cmd_summary)

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
