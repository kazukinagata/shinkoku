"""確定申告自動化 CLI エントリーポイント."""

from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="shinkoku",
        description="確定申告自動化 CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Register all subcommand modules
    from shinkoku.cli import (
        doc_generate,
        furusato,
        import_data,
        ledger,
        profile,
        tax_calc,
        xtx,
    )

    ledger.register(subparsers)
    import_data.register(subparsers)
    tax_calc.register(subparsers)
    doc_generate.register(subparsers)
    furusato.register(subparsers)
    profile.register(subparsers)
    xtx.register(subparsers)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    try:
        args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)
