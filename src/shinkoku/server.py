"""MCP Server entry point for shinkoku."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("shinkoku", json_response=True)


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
