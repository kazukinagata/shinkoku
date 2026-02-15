"""Test script to generate overlay PDFs for Schedule 3, Schedule 4, and Income/Expense Statement.

Generates merged PDFs with dummy data to visually verify coordinate alignment.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shinkoku.tools.pdf_coordinates import (  # noqa: E402
    INCOME_EXPENSE_STATEMENT,
    SCHEDULE_3_FORM,
    SCHEDULE_4_FORM,
)
from shinkoku.tools.pdf_utils import (  # noqa: E402
    create_overlay,
    get_font_name,
    merge_overlay,
    pdf_to_images,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "fit_test_other"
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "r07"

# Page sizes from the actual PDFs
SCHEDULE_PAGE_SIZE = (579.672, 814.791)  # 03.pdf / 04.pdf
INCOME_EXPENSE_PAGE_SIZE = (842.0, 595.0)  # 05_ie.pdf (portrait+rotate90 = landscape visual)


def extract_page(src_pdf: str, page_idx: int, out_pdf: str) -> str:
    """Extract a single page from a multi-page PDF."""
    reader = PdfReader(src_pdf)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_idx])
    Path(out_pdf).parent.mkdir(parents=True, exist_ok=True)
    with open(out_pdf, "wb") as f:
        writer.write(f)
    return out_pdf


def build_fields(coord_dict: dict[str, dict]) -> list[dict]:
    """Build field list from coordinate dict with dummy values."""
    fields = []
    for name, spec in coord_dict.items():
        field = dict(spec)
        ftype = field.get("type", "text")
        if ftype == "digit_cells":
            field["value"] = "8" * field.get("num_cells", 8)
        elif ftype == "number":
            field["value"] = 8888888
        elif ftype == "checkbox":
            field["value"] = True
        else:
            # text — use abbreviated field name
            label = name[:20]
            field["value"] = label
        fields.append(field)
    return fields


def build_label_overlay(
    coord_dict: dict[str, dict],
    page_size: tuple[float, float],
) -> bytes:
    """Create an overlay with small red labels next to each field for identification."""
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

        c.setFillColorRGB(1, 0, 0)
        c.setFont(fn, 5)
        c.drawString(label_x, label_y, name)
        c.setFillColorRGB(0, 0, 0)

    c.save()
    return buf.getvalue()


def test_form(
    form_name: str,
    coord_dict: dict[str, dict],
    template_pdf: str,
    page_size: tuple[float, float],
) -> None:
    """Generate overlay, merge with template, convert to images."""
    print(f"=== {form_name} ===")
    out_dir = OUTPUT_DIR / form_name
    out_dir.mkdir(parents=True, exist_ok=True)

    fields = build_fields(coord_dict)
    print(f"  Fields: {len(fields)}")

    overlay_bytes = create_overlay(fields, page_size=page_size)
    merged_pdf = str(out_dir / f"{form_name}_merged.pdf")
    merge_overlay(template_pdf, overlay_bytes, merged_pdf)
    print(f"  Merged PDF: {merged_pdf}")

    # Add label overlay
    label_bytes = build_label_overlay(coord_dict, page_size)
    final_pdf = str(out_dir / f"{form_name}_final.pdf")
    merge_overlay(merged_pdf, label_bytes, final_pdf)
    print(f"  Final PDF: {final_pdf}")

    images = pdf_to_images(final_pdf, str(out_dir / "images"), dpi=200)
    for img in images:
        print(f"  Image: {img}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract single pages from multi-page NTA PDFs
    # 02.pdf = 第三表（分離課税用）, 03.pdf = 第四表（損失申告用）
    sched3_template = extract_page(
        str(TEMPLATE_DIR / "02.pdf"), 0, str(OUTPUT_DIR / "02_page1.pdf")
    )
    sched4_template = extract_page(
        str(TEMPLATE_DIR / "03.pdf"), 0, str(OUTPUT_DIR / "03_page1.pdf")
    )
    # 05_ie.pdf = 収支内訳書（一般用） — FA7001
    ie_template = extract_page(
        str(TEMPLATE_DIR / "05_ie.pdf"), 0, str(OUTPUT_DIR / "05_ie_page1.pdf")
    )

    test_form(
        "schedule_3",
        SCHEDULE_3_FORM,
        sched3_template,
        SCHEDULE_PAGE_SIZE,
    )

    test_form(
        "schedule_4",
        SCHEDULE_4_FORM,
        sched4_template,
        SCHEDULE_PAGE_SIZE,
    )

    test_form(
        "income_expense",
        INCOME_EXPENSE_STATEMENT,
        ie_template,
        INCOME_EXPENSE_PAGE_SIZE,
    )

    print("\nDone! Check output/fit_test_other/")


if __name__ == "__main__":
    main()
