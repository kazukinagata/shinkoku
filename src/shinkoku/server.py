"""MCP Server entry point for shinkoku."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from shinkoku.tools import ledger, tax_calc, import_data, document, furusato
from shinkoku.tools import profile, separate_tax

mcp = FastMCP("shinkoku", json_response=True)

ledger.register(mcp)
tax_calc.register(mcp)
import_data.register(mcp)
document.register(mcp)
furusato.register(mcp)
profile.register(mcp)
separate_tax.register(mcp)


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
