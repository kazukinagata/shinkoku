"""Test script to visually verify INCOME_TAX_P1 and INCOME_TAX_P2 coordinate fits.

Draws every field with dummy values onto NTA template PDFs and generates PNG images.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from shinkoku.tools.pdf_coordinates import INCOME_TAX_P1, INCOME_TAX_P2  # noqa: E402
from shinkoku.tools.pdf_utils import (  # noqa: E402
    create_overlay,
    get_font_name,
    merge_overlay,
    pdf_to_images,
)

# NTA r07/01.pdf actual page size (NOT standard A4)
NTA_PAGE_SIZE = (579.672, 814.791)


def build_fields_for_coord_dict(coord_dict: dict[str, dict]) -> list[dict]:
    """Build field list with dummy values for every field in a coordinate dict."""
    fields = []
    for name, spec in coord_dict.items():
        ftype = spec.get("type", "text")
        field = dict(spec)  # copy

        if ftype == "digit_cells":
            field["value"] = 88888888
        elif ftype == "number":
            field["value"] = 8888888
        elif ftype == "checkbox":
            field["value"] = True
        elif ftype == "text":
            field["value"] = name[:20]
        else:
            field["value"] = name[:20]

        fields.append(field)
    return fields


def build_label_overlay(coord_dict: dict[str, dict], page_size: tuple[float, float] = A4) -> bytes:
    """Create an overlay with small labels next to each field for identification."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)
    fn = get_font_name()

    for name, spec in coord_dict.items():
        ftype = spec.get("type", "text")

        if ftype == "digit_cells":
            label_x = spec["x_start"]
            label_y = spec["y"] + 10
        elif ftype in ("text", "number"):
            label_x = spec["x"]
            label_y = spec["y"] + 10
        elif ftype == "checkbox":
            label_x = spec["x"]
            label_y = spec["y"] + 12
        else:
            continue

        # Draw label in red
        c.setFillColorRGB(1, 0, 0)
        c.setFont(fn, 5)
        c.drawString(label_x, label_y, name)
        c.setFillColorRGB(0, 0, 0)

    c.save()
    return buf.getvalue()


def main() -> None:
    templates_dir = project_root / "templates"
    output_dir = project_root / "output" / "fit_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- INCOME_TAX_P1 ---
    print("=== Processing INCOME_TAX_P1 ===")
    p1_template = str(templates_dir / "r07" / "01.pdf")
    p1_fields = build_fields_for_coord_dict(INCOME_TAX_P1)

    # Create main overlay — NTA template is 579.672x814.791, not standard A4
    p1_overlay = create_overlay(p1_fields, page_size=NTA_PAGE_SIZE)
    p1_merged_path = str(output_dir / "income_tax_p1_test.pdf")
    merge_overlay(p1_template, p1_overlay, p1_merged_path)

    # Now merge labels on top
    p1_label_overlay = build_label_overlay(INCOME_TAX_P1, page_size=NTA_PAGE_SIZE)
    p1_final_path = str(output_dir / "income_tax_p1_final.pdf")
    merge_overlay(p1_merged_path, p1_label_overlay, p1_final_path)

    # Convert to PNG
    p1_images = pdf_to_images(p1_final_path, str(output_dir / "p1_images"), dpi=200)
    for img in p1_images:
        print(f"  Generated: {img}")

    # --- INCOME_TAX_P2 ---
    # 第二表は r07/01.pdf のページ1 → 抽出済みの r07/01_p2.pdf を使用
    print("\n=== Processing INCOME_TAX_P2 ===")
    p2_template = str(templates_dir / "r07" / "01_p2.pdf")
    p2_fields = build_fields_for_coord_dict(INCOME_TAX_P2)

    p2_overlay = create_overlay(p2_fields, page_size=NTA_PAGE_SIZE)
    p2_merged_path = str(output_dir / "income_tax_p2_test.pdf")
    merge_overlay(p2_template, p2_overlay, p2_merged_path)

    # Merge labels
    p2_label_overlay = build_label_overlay(INCOME_TAX_P2, page_size=NTA_PAGE_SIZE)
    p2_final_path = str(output_dir / "income_tax_p2_final.pdf")
    merge_overlay(p2_merged_path, p2_label_overlay, p2_final_path)

    p2_images = pdf_to_images(p2_final_path, str(output_dir / "p2_images"), dpi=200)
    for img in p2_images:
        print(f"  Generated: {img}")

    print("\nDone! Check output/fit_test/ for results.")


if __name__ == "__main__":
    main()
