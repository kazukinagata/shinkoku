"""納税者プロフィール CLI."""

from __future__ import annotations

import argparse
import json
import sys

from shinkoku.tools.profile import get_taxpayer_profile


def register(parent_subparsers: argparse._SubParsersAction) -> None:
    """profile サブコマンドを親パーサーに登録する。"""
    parser = parent_subparsers.add_parser(
        "profile",
        description="納税者プロフィール CLI",
        help="プロファイル取得",
    )
    parser.add_argument("--config", required=True, help="設定ファイルパス")
    parser.set_defaults(func=_run)


def _run(args: argparse.Namespace) -> None:
    try:
        result = get_taxpayer_profile(config_path=args.config)
    except Exception as e:
        result = {"status": "error", "message": str(e)}
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
        sys.exit(1)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
