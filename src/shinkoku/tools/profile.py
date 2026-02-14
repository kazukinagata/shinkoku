"""Taxpayer profile tools.

Loads taxpayer information from config YAML.
my_number is never exposed in tool output — only has_my_number flag.
"""

from __future__ import annotations

from shinkoku.config import load_config


def get_taxpayer_profile(*, config_path: str) -> dict:
    """Load taxpayer profile from config. Masks my_number."""
    config = load_config(config_path)

    taxpayer = config.taxpayer
    address = config.address
    business = config.business
    filing = config.filing

    result: dict = {
        "taxpayer": {
            "last_name": taxpayer.last_name,
            "first_name": taxpayer.first_name,
            "last_name_kana": taxpayer.last_name_kana,
            "first_name_kana": taxpayer.first_name_kana,
            "full_name": f"{taxpayer.last_name} {taxpayer.first_name}".strip(),
            "gender": taxpayer.gender,
            "date_of_birth": taxpayer.date_of_birth,
            "phone": taxpayer.phone,
            "has_my_number": taxpayer.my_number is not None and len(taxpayer.my_number) == 12,
            "widow_status": taxpayer.widow_status,
            "disability_status": taxpayer.disability_status,
            "working_student": taxpayer.working_student,
        },
        "address": address.model_dump(),
        "business_address": (
            config.business_address.model_dump() if config.business_address else None
        ),
        "business": business.model_dump(),
        "filing": filing.model_dump(),
        "tax_year": config.tax_year,
        "db_path": config.db_path,
        "output_dir": config.output_dir,
    }
    return result


def register(mcp) -> None:
    """Register profile tools with the MCP server."""

    @mcp.tool()
    def profile_get_taxpayer(config_path: str) -> dict:
        """Get taxpayer profile from config file.

        Returns taxpayer info, address, business details, and filing method.
        my_number is never exposed — only has_my_number flag is returned.
        """
        return get_taxpayer_profile(config_path=config_path)
