"""PDF generation utilities for tax form overlay.

Uses ReportLab for drawing overlays and pypdf for merging with templates.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader = None
    PdfWriter = None


# ============================================================
# Font Registration
# ============================================================

_FONT_REGISTERED = False
_FONT_NAME = "Helvetica"  # fallback

# Common IPAex Gothic font paths
_IPAEX_PATHS = [
    "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf",
    "/usr/share/fonts/truetype/ipaexfont-gothic/ipaexg.ttf",
    "/usr/share/fonts/ipaexfont-gothic/ipaexg.ttf",
    "/usr/share/fonts/ipaexg.ttf",
    str(Path.home() / ".fonts" / "ipaexg.ttf"),
    str(Path.home() / "fonts" / "ipaexg.ttf"),
]


def _register_font() -> str:
    """Register IPAex Gothic font if available, else fallback to Helvetica."""
    global _FONT_REGISTERED, _FONT_NAME
    if _FONT_REGISTERED and _FONT_NAME != "Helvetica":
        return _FONT_NAME

    for font_path in _IPAEX_PATHS:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(TTFont("IPAexGothic", font_path))
                _FONT_NAME = "IPAexGothic"
                _FONT_REGISTERED = True
                return _FONT_NAME
            except Exception:
                continue

    # Fallback — don't cache so we retry if font is installed later
    _FONT_NAME = "Helvetica"
    return _FONT_NAME


def get_font_name() -> str:
    """Get the registered font name."""
    return _register_font()


# ============================================================
# Drawing Functions
# ============================================================


def draw_text(
    c: canvas.Canvas,
    x: float,
    y: float,
    text: str,
    font_size: float = 9,
    font_name: str | None = None,
) -> None:
    """Draw text at the specified position."""
    fn = font_name or get_font_name()
    c.setFont(fn, font_size)
    c.drawString(x, y, text)


def draw_number(
    c: canvas.Canvas,
    x: float,
    y: float,
    value: int,
    font_size: float = 9,
    font_name: str | None = None,
    with_comma: bool = True,
) -> None:
    """Draw a number right-aligned at the specified position.

    Args:
        c: ReportLab canvas.
        x: Right edge x-coordinate.
        y: Baseline y-coordinate.
        value: Integer value to draw.
        font_size: Font size.
        font_name: Font name override.
        with_comma: Whether to format with commas.
    """
    fn = font_name or get_font_name()
    c.setFont(fn, font_size)
    if with_comma:
        text = f"{value:,}"
    else:
        text = str(value)
    c.drawRightString(x, y, text)


def draw_checkbox(
    c: canvas.Canvas,
    x: float,
    y: float,
    checked: bool,
    size: float = 3 * mm,
) -> None:
    """Draw a checkbox (filled circle if checked)."""
    if checked:
        c.circle(x + size / 2, y + size / 2, size / 2, fill=1)


# ============================================================
# Overlay Creation and Merging
# ============================================================


def create_overlay(
    fields: list[dict[str, Any]],
    page_size: tuple[float, float] = A4,
) -> bytes:
    """Create a transparent PDF overlay with the specified fields.

    Args:
        fields: List of field dicts, each with:
            - type: "text", "number", or "checkbox"
            - x, y: coordinates
            - value: the value to draw
            - font_size: optional
            - with_comma: optional (for numbers)
        page_size: Page size tuple.

    Returns:
        PDF bytes of the overlay.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)

    for field in fields:
        ftype = field.get("type", "text")
        x = field["x"]
        y = field["y"]
        value = field["value"]
        font_size = field.get("font_size", 9)

        if ftype == "text":
            draw_text(c, x, y, str(value), font_size=font_size)
        elif ftype == "number":
            draw_number(
                c,
                x,
                y,
                int(value),
                font_size=font_size,
                with_comma=field.get("with_comma", True),
            )
        elif ftype == "checkbox":
            draw_checkbox(c, x, y, bool(value))

    c.save()
    return buf.getvalue()


def create_multi_page_overlay(
    pages: list[list[dict[str, Any]]],
    page_size: tuple[float, float] = A4,
) -> bytes:
    """Create a multi-page PDF overlay.

    Args:
        pages: List of pages, each page is a list of field dicts.
        page_size: Page size tuple.

    Returns:
        PDF bytes of the overlay.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)

    for page_fields in pages:
        for field in page_fields:
            ftype = field.get("type", "text")
            x = field["x"]
            y = field["y"]
            value = field["value"]
            font_size = field.get("font_size", 9)

            if ftype == "text":
                draw_text(c, x, y, str(value), font_size=font_size)
            elif ftype == "number":
                draw_number(
                    c,
                    x,
                    y,
                    int(value),
                    font_size=font_size,
                    with_comma=field.get("with_comma", True),
                )
            elif ftype == "checkbox":
                draw_checkbox(c, x, y, bool(value))

        c.showPage()

    c.save()
    return buf.getvalue()


def merge_overlay(
    template_path: str,
    overlay_bytes: bytes,
    output_path: str,
) -> str:
    """Merge an overlay PDF onto a template PDF.

    Args:
        template_path: Path to the template PDF.
        overlay_bytes: PDF bytes of the overlay.
        output_path: Path to write the merged PDF.

    Returns:
        The output path.
    """
    if PdfReader is None or PdfWriter is None:
        raise ImportError("pypdf is required for PDF merging")

    template = PdfReader(template_path)
    overlay = PdfReader(io.BytesIO(overlay_bytes))
    writer = PdfWriter()

    for i, page in enumerate(template.pages):
        if i < len(overlay.pages):
            page.merge_page(overlay.pages[i])
        writer.add_page(page)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def generate_standalone_pdf(
    fields: list[dict[str, Any]],
    output_path: str,
    page_size: tuple[float, float] = A4,
    title: str = "",
) -> str:
    """Generate a standalone PDF (no template) with fields drawn directly.

    Used when no NTA template is available.

    Args:
        fields: List of field dicts.
        output_path: Path to write the PDF.
        page_size: Page size.
        title: Optional title at top of page.

    Returns:
        The output path.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)

    if title:
        fn = get_font_name()
        c.setFont(fn, 14)
        c.drawCentredString(page_size[0] / 2, page_size[1] - 30 * mm, title)

    for field in fields:
        ftype = field.get("type", "text")
        x = field["x"]
        y = field["y"]
        value = field["value"]
        font_size = field.get("font_size", 9)

        if ftype == "text":
            draw_text(c, x, y, str(value), font_size=font_size)
        elif ftype == "number":
            draw_number(
                c,
                x,
                y,
                int(value),
                font_size=font_size,
                with_comma=field.get("with_comma", True),
            )
        elif ftype == "checkbox":
            draw_checkbox(c, x, y, bool(value))

    c.save()
    pdf_bytes = buf.getvalue()

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    return output_path


def generate_standalone_multi_page_pdf(
    pages: list[list[dict[str, Any]]],
    output_path: str,
    page_size: tuple[float, float] = A4,
    titles: list[str] | None = None,
) -> str:
    """Generate a standalone multi-page PDF (no template).

    Args:
        pages: List of pages, each is a list of field dicts.
        output_path: Path to write the PDF.
        page_size: Page size.
        titles: Optional per-page titles.

    Returns:
        The output path.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)

    for idx, page_fields in enumerate(pages):
        if titles and idx < len(titles) and titles[idx]:
            fn = get_font_name()
            c.setFont(fn, 14)
            c.drawCentredString(page_size[0] / 2, page_size[1] - 30 * mm, titles[idx])

        for field in page_fields:
            ftype = field.get("type", "text")
            x = field["x"]
            y = field["y"]
            value = field["value"]
            font_size = field.get("font_size", 9)

            if ftype == "text":
                draw_text(c, x, y, str(value), font_size=font_size)
            elif ftype == "number":
                draw_number(
                    c,
                    x,
                    y,
                    int(value),
                    font_size=font_size,
                    with_comma=field.get("with_comma", True),
                )
            elif ftype == "checkbox":
                draw_checkbox(c, x, y, bool(value))

        c.showPage()

    c.save()
    pdf_bytes = buf.getvalue()

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    return output_path
