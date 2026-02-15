"""Test script: overlay all BLUE_RETURN coordinate fields onto NTA r07/10.pdf template.

r07/10.pdf is an 8-page PDF (4 pages 提出用 + 4 pages 控用).
Pages 0-3 map to:
  Page 0: 損益計算書 P1 → BLUE_RETURN_PL_P1
  Page 1: 損益計算書 P2 → BLUE_RETURN_PL_P2
  Page 2: 損益計算書 P3 (depreciation/rent) → BLUE_RETURN_PL_P3
  Page 3: 貸借対照表 B/S → BLUE_RETURN_BS

All pages have MediaBox 595x842 with /Rotate=90 (displayed as Landscape 842x595).
Coordinate definitions use landscape coordinates (x: 0-842, y: 0-595 from bottom).
Overlay must transform to portrait MediaBox coordinates and pre-rotate text.
"""

from __future__ import annotations

import io
from pathlib import Path

from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from shinkoku.tools.pdf_coordinates import (
    BLUE_RETURN_BS,
    BLUE_RETURN_PL_P1,
    BLUE_RETURN_PL_P2,
    BLUE_RETURN_PL_P3,
)
from shinkoku.tools.pdf_utils import (
    get_font_name,
    merge_overlay,
    pdf_to_images,
)

TEMPLATE_PATH = "templates/r07/10.pdf"
OUTPUT_DIR = "output/test_blue_return"
OUTPUT_IMG_DIR = f"{OUTPUT_DIR}/images"

# MediaBox dimensions (portrait, before rotation)
MEDIABOX_W = 595.0
MEDIABOX_H = 842.0


def create_rotated_overlay(
    fields: list[dict],
    mediabox_w: float = MEDIABOX_W,
    mediabox_h: float = MEDIABOX_H,
) -> bytes:
    """Create overlay for a /Rotate=90 page.

    Fields use landscape coordinates (x: 0-842, y: 0-595 from bottom-left).
    This function transforms them to portrait MediaBox coordinates and
    pre-rotates text by +90 degrees so it appears upright after the viewer
    applies the page's /Rotate=90.

    Coordinate mapping for /Rotate=90 (CW):
      portrait_x = 595 - landscape_y
      portrait_y = landscape_x
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(mediabox_w, mediabox_h))
    fn = get_font_name()

    for field in fields:
        ftype = field.get("type", "text")
        font_size = field.get("font_size", 9)
        value = field.get("value", "")

        if ftype == "digit_cells":
            # Handle digit_cells: transform each cell position
            lx_start = field["x_start"]
            ly = field["y"]
            cell_width = field["cell_width"]
            num_cells = field["num_cells"]
            text = str(value).replace(",", "")

            # Right-align digits
            digits = list(text)
            start_idx = num_cells - len(digits)

            for i, digit in enumerate(digits):
                cell_idx = start_idx + i
                if 0 <= cell_idx < num_cells:
                    # Center of this cell in landscape coords
                    cell_lx = lx_start + cell_idx * cell_width + cell_width / 2
                    cell_ly = ly
                    # Transform to portrait
                    rx = mediabox_w - cell_ly
                    ry = cell_lx
                    c.saveState()
                    c.translate(rx, ry)
                    c.rotate(90)
                    c.setFont(fn, font_size)
                    c.drawCentredString(0, 0, digit)
                    c.restoreState()

        elif ftype == "text":
            lx = field["x"]
            ly = field["y"]
            rx = mediabox_w - ly
            ry = lx
            c.saveState()
            c.translate(rx, ry)
            c.rotate(90)
            c.setFont(fn, font_size)
            c.drawString(0, 0, str(value))
            c.restoreState()

        elif ftype == "number":
            lx = field["x"]
            ly = field["y"]
            rx = mediabox_w - ly
            ry = lx
            c.saveState()
            c.translate(rx, ry)
            c.rotate(90)
            c.setFont(fn, font_size)
            text = f"{int(value):,}"
            c.drawRightString(0, 0, text)
            c.restoreState()

        elif ftype == "checkbox":
            lx = field["x"]
            ly = field["y"]
            size = field.get("size", 8)
            rx = mediabox_w - ly
            ry = lx
            if value:
                c.saveState()
                c.translate(rx, ry)
                c.rotate(90)
                c.circle(size / 2, size / 2, size / 2, fill=1)
                c.restoreState()

    c.save()
    return buf.getvalue()


def build_fields_for_dict(coord_dict: dict[str, dict]) -> list[dict]:
    """Build overlay field list with dummy values for every coordinate entry."""
    fields = []
    for name, spec in coord_dict.items():
        ftype = spec.get("type", "text")
        field = dict(spec)  # copy all coordinate info

        if ftype == "digit_cells":
            field["value"] = "8" * spec["num_cells"]
        elif ftype == "number":
            field["value"] = 8888888
        elif ftype == "checkbox":
            field["value"] = True
        elif ftype == "text":
            field["value"] = name[:16]
        else:
            field["value"] = name[:16]

        fields.append(field)
    return fields


def extract_page(template_path: str, page_index: int, output_path: str) -> str:
    """Extract a single page from a multi-page PDF."""
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_index])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def main() -> None:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_IMG_DIR).mkdir(parents=True, exist_ok=True)

    page_configs = [
        ("pl_p1", BLUE_RETURN_PL_P1, 0),
        ("pl_p2", BLUE_RETURN_PL_P2, 1),
        ("pl_p3", BLUE_RETURN_PL_P3, 2),
        ("bs", BLUE_RETURN_BS, 3),
    ]

    for label, coords, page_idx in page_configs:
        print(f"\n=== {label} (page {page_idx}) ===")

        # Extract single page from template
        single_page_path = f"{OUTPUT_DIR}/template_page_{page_idx}.pdf"
        extract_page(TEMPLATE_PATH, page_idx, single_page_path)

        # Build test fields with dummy values
        fields = build_fields_for_dict(coords)
        print(f"  Fields: {len(fields)}")

        # Create rotated overlay
        overlay_bytes = create_rotated_overlay(fields)

        # Merge with template page
        merged_path = f"{OUTPUT_DIR}/merged_{label}.pdf"
        merge_overlay(single_page_path, overlay_bytes, merged_path)
        print(f"  Merged: {merged_path}")

        # Convert to PNG
        images = pdf_to_images(merged_path, OUTPUT_IMG_DIR, dpi=200)
        for img in images:
            target = f"{OUTPUT_IMG_DIR}/{label}.png"
            Path(img).rename(target)
            print(f"  PNG: {target}")

    print(f"\nDone! Check output in: {OUTPUT_IMG_DIR}")


if __name__ == "__main__":
    main()
