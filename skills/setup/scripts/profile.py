#!/usr/bin/env python3
"""納税者プロフィール CLI スクリプト."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from shinkoku.tools.profile import get_taxpayer_profile  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="納税者プロフィール CLI")
    parser.add_argument("--config", required=True, help="設定ファイルパス")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = get_taxpayer_profile(config_path=args.config)
    except Exception as e:
        result = {"status": "error", "message": str(e)}
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
        sys.exit(1)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
