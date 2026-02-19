"""ふるさと納税 CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shinkoku.db import get_connection
from shinkoku.tools.furusato import (
    add_furusato_donation,
    delete_furusato_donation,
    list_furusato_donations,
    summarize_furusato_donations,
)


def _output(result: dict) -> None:
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    if result.get("status") == "error":
        sys.exit(1)


def cmd_add(args: argparse.Namespace) -> None:
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
        _output({"status": "ok", "donation_id": donation_id})
    except ValueError as e:
        _output({"status": "error", "message": str(e)})
    finally:
        conn.close()


def cmd_list(args: argparse.Namespace) -> None:
    conn = get_connection(args.db_path)
    try:
        donations = list_furusato_donations(conn, args.fiscal_year)
        _output(
            {
                "status": "ok",
                "donations": [d.model_dump() for d in donations],
                "count": len(donations),
            }
        )
    finally:
        conn.close()


def cmd_delete(args: argparse.Namespace) -> None:
    conn = get_connection(args.db_path)
    try:
        deleted = delete_furusato_donation(conn, args.donation_id)
        if not deleted:
            _output({"status": "error", "message": f"Donation {args.donation_id} not found"})
            return
        _output({"status": "ok", "donation_id": args.donation_id})
    finally:
        conn.close()


def cmd_summary(args: argparse.Namespace) -> None:
    conn = get_connection(args.db_path)
    try:
        summary = summarize_furusato_donations(
            conn, args.fiscal_year, estimated_limit=args.estimated_limit
        )
        _output({"status": "ok", **summary.model_dump()})
    finally:
        conn.close()


def register(parent_subparsers: argparse._SubParsersAction) -> None:
    """furusato サブコマンドを親パーサーに登録する。"""
    parser = parent_subparsers.add_parser(
        "furusato",
        description="ふるさと納税 CLI",
        help="ふるさと納税",
    )
    sub = parser.add_subparsers(dest="subcommand")

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

    parser.set_defaults(func=lambda args: parser.print_help() or sys.exit(1))
