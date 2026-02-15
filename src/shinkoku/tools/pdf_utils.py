"""PDF generation utilities for tax form overlay.

Uses ReportLab for drawing overlays and pypdf for merging with templates.
"""

from __future__ import annotations

import io
import logging
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
    PdfReader = None  # type: ignore[misc,assignment]
    PdfWriter = None  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


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
    max_width: float | None = None,
) -> None:
    """Draw text at the specified position.

    max_width が指定された場合、テキスト幅が max_width を超えると
    フォントサイズを自動縮小して枠内に収める（最小4pt）。
    """
    fn = font_name or get_font_name()
    if max_width is not None:
        size = font_size
        while size > 4:
            c.setFont(fn, size)
            if c.stringWidth(text, fn, size) <= max_width:
                break
            size -= 0.5
        c.setFont(fn, size)
    else:
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


def draw_digit_cells(
    c: canvas.Canvas,
    x_start: float,
    y: float,
    value: int | str,
    cell_width: float,
    num_cells: int,
    font_size: float = 10,
    font_name: str | None = None,
    right_align: bool = True,
) -> None:
    """桁別セルに1桁ずつ数値を配置する.

    確定申告書の金額欄や郵便番号欄など、グリッドセルに1桁ずつ記入する
    フィールド用の描画関数。

    Args:
        c: ReportLab canvas.
        x_start: 最初のセルの左端x座標.
        y: ベースラインy座標.
        value: 描画する値（int または str）.
        cell_width: セル間隔（pt）.
        num_cells: セル数.
        font_size: フォントサイズ.
        font_name: フォント名.
        right_align: True の場合、右端セルから埋める（金額用）.
    """
    fn = font_name or get_font_name()
    c.setFont(fn, font_size)

    text = str(value)
    # マイナス符号の処理
    is_negative = text.startswith("-")
    if is_negative:
        text = text[1:]

    # カンマを除去
    text = text.replace(",", "")

    digits = list(text)

    if len(digits) > num_cells:
        logger.warning(
            "digit overflow: %s has %d digits but only %d cells — upper digits truncated",
            value,
            len(digits),
            num_cells,
        )

    if right_align:
        # 右端セルから埋める
        start_idx = num_cells - len(digits)
        if is_negative and start_idx > 0:
            start_idx -= 1  # マイナス符号用に1セル確保
    else:
        start_idx = 0

    for i, digit in enumerate(digits):
        cell_idx = start_idx + i
        if is_negative and i == 0 and right_align:
            # マイナス符号を先頭に配置
            x_center = x_start + (start_idx) * cell_width + cell_width / 2
            c.drawCentredString(x_center, y, "-")
            cell_idx = start_idx + 1
            # digit をもう1つ右のセルに
            x_center = x_start + cell_idx * cell_width + cell_width / 2
            c.drawCentredString(x_center, y, digit)
            is_negative = False  # 符号は処理済み
            continue

        if 0 <= cell_idx < num_cells:
            x_center = x_start + cell_idx * cell_width + cell_width / 2
            c.drawCentredString(x_center, y, digit)


def _draw_field(
    c: canvas.Canvas,
    field: dict[str, Any],
) -> None:
    """1つのフィールドを描画する（全タイプ対応）."""
    ftype = field.get("type", "text")
    value = field["value"]
    font_size = field.get("font_size", 9)

    if ftype == "digit_cells":
        draw_digit_cells(
            c,
            field["x_start"],
            field["y"],
            value,
            field["cell_width"],
            field["num_cells"],
            font_size,
            right_align=field.get("right_align", True),
        )
    elif ftype == "text":
        draw_text(
            c,
            field["x"],
            field["y"],
            str(value),
            font_size=font_size,
            max_width=field.get("max_width"),
        )
    elif ftype == "number":
        draw_number(
            c,
            field["x"],
            field["y"],
            int(value),
            font_size=font_size,
            with_comma=field.get("with_comma", True),
        )
    elif ftype == "checkbox":
        draw_checkbox(c, field["x"], field["y"], bool(value))


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
            - type: "text", "number", "checkbox", or "digit_cells"
            - x, y: coordinates (for text/number/checkbox)
            - x_start, y, cell_width, num_cells: (for digit_cells)
            - value: the value to draw
            - font_size: optional
        page_size: Page size tuple.

    Returns:
        PDF bytes of the overlay.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=page_size)

    for field in fields:
        _draw_field(c, field)

    c.save()
    return buf.getvalue()


def create_multi_page_overlay(
    pages: list[list[dict[str, Any]]],
    page_size: tuple[float, float] = A4,
    page_sizes: list[tuple[float, float]] | None = None,
    page_rotations: list[int] | None = None,
) -> bytes:
    """Create a multi-page PDF overlay.

    Args:
        pages: List of pages, each page is a list of field dicts.
        page_size: Default page size tuple.
        page_sizes: Per-page sizes. If provided, overrides page_size for each page.
            landscape 座標系で定義されたサイズを指定する（例: (842, 595)）。
        page_rotations: Per-page rotation in degrees (0 or 90).
            90 の場合、テンプレートが portrait MediaBox + /Rotate=90 であることを示す。
            オーバーレイを portrait サイズで作成し、座標を回転変換してから描画する。

    Returns:
        PDF bytes of the overlay.
    """
    buf = io.BytesIO()
    # 最初のページサイズで初期化（各ページで切り替え可能）
    initial_size = page_sizes[0] if page_sizes else page_size
    c = canvas.Canvas(buf, pagesize=initial_size)

    for idx, page_fields in enumerate(pages):
        rotation = page_rotations[idx] if page_rotations and idx < len(page_rotations) else 0
        if page_sizes and idx < len(page_sizes):
            w, h = page_sizes[idx]
        else:
            w, h = page_size

        if rotation == 90:
            # テンプレートは portrait (h x w) + /Rotate=90 で landscape 表示。
            # オーバーレイを portrait サイズで作成し、座標系を回転して
            # landscape 座標 (w x h) → portrait 物理座標 (h x w) に変換する。
            # /Rotate=90 は表示時に90°CW回転するため、逆変換として
            # translate(W, 0) + rotate(90) で landscape→portrait 変換する。
            physical_w, physical_h = h, w  # portrait: 元の height が width に
            c.setPageSize((physical_w, physical_h))
            c.saveState()
            c.translate(physical_w, 0)
            c.rotate(90)
            # 以降 landscape 座標系 (w x h) で描画可能
        else:
            c.setPageSize((w, h))

        for field in page_fields:
            _draw_field(c, field)

        if rotation == 90:
            c.restoreState()

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


def merge_multi_template_overlay(
    template_paths: list[str],
    overlay_bytes: bytes,
    output_path: str,
) -> str:
    """Merge a multi-page overlay with different template PDFs per page.

    各ページに異なるテンプレートPDFを使用してオーバーレイをマージする。
    確定申告書セットのように、ページごとに異なるNTA用紙を使う場合に使用。

    Args:
        template_paths: テンプレートPDFのパスリスト（ページ順）.
        overlay_bytes: マルチページオーバーレイのPDFバイト.
        output_path: 出力パス.

    Returns:
        出力パス.
    """
    if PdfReader is None or PdfWriter is None:
        raise ImportError("pypdf is required for PDF merging")

    overlay = PdfReader(io.BytesIO(overlay_bytes))
    writer = PdfWriter()

    for i, tmpl_path in enumerate(template_paths):
        if Path(tmpl_path).exists():
            tmpl_reader = PdfReader(tmpl_path)
            page = tmpl_reader.pages[0]
            if i < len(overlay.pages):
                page.merge_page(overlay.pages[i])
            writer.add_page(page)
        elif i < len(overlay.pages):
            # テンプレートがない場合はオーバーレイページをそのまま使用
            writer.add_page(overlay.pages[i])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


# ============================================================
# Standalone PDF Generation
# ============================================================


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
        _draw_field(c, field)

    c.save()
    pdf_bytes = buf.getvalue()

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    return output_path


def generate_standalone_multi_page_pdf(
    pages: list[list[dict[str, Any]]],
    output_path: str,
    page_size: tuple[float, float] = A4,
    page_sizes: list[tuple[float, float]] | None = None,
    titles: list[str] | None = None,
) -> str:
    """Generate a standalone multi-page PDF (no template).

    Args:
        pages: List of pages, each is a list of field dicts.
        output_path: Path to write the PDF.
        page_size: Default page size.
        page_sizes: Per-page sizes (overrides page_size).
        titles: Optional per-page titles.

    Returns:
        The output path.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    initial_size = page_sizes[0] if page_sizes else page_size
    c = canvas.Canvas(buf, pagesize=initial_size)

    for idx, page_fields in enumerate(pages):
        if page_sizes and idx < len(page_sizes):
            c.setPageSize(page_sizes[idx])

        current_size = page_sizes[idx] if page_sizes and idx < len(page_sizes) else page_size
        if titles and idx < len(titles) and titles[idx]:
            fn = get_font_name()
            c.setFont(fn, 14)
            c.drawCentredString(current_size[0] / 2, current_size[1] - 30 * mm, titles[idx])

        for field in page_fields:
            _draw_field(c, field)

        c.showPage()

    c.save()
    pdf_bytes = buf.getvalue()

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    return output_path


# ============================================================
# PDF to Image Conversion
# ============================================================


def pdf_to_images(
    pdf_path: str,
    output_dir: str,
    dpi: int = 150,
) -> list[str]:
    """PDFの各ページをPNG画像に変換する.

    pypdfium2を使用してPDFをページごとの画像に変換する。
    /submit スキルのPDF目視確認ステップで使用。

    Args:
        pdf_path: PDFファイルのパス.
        output_dir: 画像出力ディレクトリ.
        dpi: 解像度（デフォルト150）.

    Returns:
        生成されたPNG画像のパスリスト.
    """
    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise ImportError("pypdfium2 is required for PDF to image conversion")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(pdf_path)
    images: list[str] = []

    for i in range(len(pdf)):
        page = pdf[i]
        scale = dpi / 72
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()

        output_path = out / f"page_{i + 1}.png"
        pil_image.save(str(output_path))
        images.append(str(output_path))

    return images
