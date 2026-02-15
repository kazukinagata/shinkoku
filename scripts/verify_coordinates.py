"""Verify coordinate definitions by drawing markers on template PDFs.

Draws colored markers at each field position on the template PDFs to
allow visual verification that coordinates are correct. Also performs
intersection/overlap checks between fields.

Usage:
    uv run python scripts/verify_coordinates.py templates/ output/verify/

This reads coordinate definitions from pdf_coordinates.py and draws:
- Red rectangles for digit_cells fields
- Blue crosshairs for text fields
- Green crosshairs for number fields
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.colors import red, blue, green, Color
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from shinkoku.tools.pdf_coordinates import (
    INCOME_TAX_P1,
    INCOME_TAX_P2,
    BLUE_RETURN_PL_P1,
    BLUE_RETURN_PL_P2,
    BLUE_RETURN_PL_P3,
    BLUE_RETURN_BS,
    CONSUMPTION_TAX_P1,
    CONSUMPTION_TAX_P2,
)


# フォーム定義とテンプレート名のマッピング
FORMS: list[dict] = [
    {
        "name": "income_tax_p1",
        "coords": INCOME_TAX_P1,
        "size": A4,
        "label": "確定申告書B 第一表",
    },
    {
        "name": "income_tax_p2",
        "coords": INCOME_TAX_P2,
        "size": A4,
        "label": "確定申告書B 第二表",
    },
    {
        "name": "blue_return_pl_p1",
        "coords": BLUE_RETURN_PL_P1,
        "size": landscape(A4),
        "label": "青色申告決算書 損益計算書 P1",
    },
    {
        "name": "blue_return_pl_p2",
        "coords": BLUE_RETURN_PL_P2,
        "size": landscape(A4),
        "label": "青色申告決算書 損益計算書 P2",
    },
    {
        "name": "blue_return_pl_p3",
        "coords": BLUE_RETURN_PL_P3,
        "size": landscape(A4),
        "label": "青色申告決算書 損益計算書 P3",
    },
    {
        "name": "blue_return_bs",
        "coords": BLUE_RETURN_BS,
        "size": landscape(A4),
        "label": "青色申告決算書 貸借対照表",
    },
    {
        "name": "consumption_tax_p1",
        "coords": CONSUMPTION_TAX_P1,
        "size": A4,
        "label": "消費税確定申告書 第一表",
    },
    {
        "name": "consumption_tax_p2",
        "coords": CONSUMPTION_TAX_P2,
        "size": A4,
        "label": "消費税 付表",
    },
]


def _draw_marker(
    c: canvas.Canvas,
    field_name: str,
    field_def: dict,
    label_size: float = 5,
) -> None:
    """フィールド定義に基づきマーカーを描画する."""
    ftype = field_def.get("type", "text")
    font_size = field_def.get("font_size", 9)

    if ftype == "digit_cells":
        # 桁別セル: 赤い矩形を各セルに描画
        c.setStrokeColor(red)
        c.setFillColor(Color(1, 0, 0, alpha=0.1))
        x_start = field_def["x_start"]
        y = field_def["y"]
        cell_width = field_def["cell_width"]
        num_cells = field_def["num_cells"]

        for i in range(num_cells):
            x = x_start + i * cell_width
            c.rect(x - cell_width / 2, y - 2, cell_width, font_size + 4, fill=1)

        # ラベル
        c.setFillColor(red)
        c.setFont("Helvetica", label_size)
        c.drawString(x_start - 5, y + font_size + 6, field_name)

    elif ftype == "checkbox":
        # チェックボックス: 緑の丸
        c.setStrokeColor(green)
        size = field_def.get("size", 8)
        c.circle(field_def["x"] + size / 2, field_def["y"] + size / 2, size / 2)
        c.setFillColor(green)
        c.setFont("Helvetica", label_size)
        c.drawString(field_def["x"] + size + 2, field_def["y"], field_name)

    else:
        # テキスト/数値: 青いクロスヘア
        color = blue if ftype == "text" else green
        c.setStrokeColor(color)
        x = field_def["x"]
        y = field_def["y"]

        # クロスヘア
        c.line(x - 5, y, x + 5, y)
        c.line(x, y - 5, x, y + 5)

        # ラベル
        c.setFillColor(color)
        c.setFont("Helvetica", label_size)
        c.drawString(x + 7, y + 2, field_name)


def _check_overlaps(coords: dict[str, dict]) -> list[str]:
    """フィールド同士の重なりを検出する."""
    warnings: list[str] = []
    fields = list(coords.items())

    for i in range(len(fields)):
        name_a, def_a = fields[i]
        for j in range(i + 1, len(fields)):
            name_b, def_b = fields[j]

            # 同一座標チェック
            if def_a.get("type") == "digit_cells" or def_b.get("type") == "digit_cells":
                continue  # digit_cellsは幅があるので単純比較が難しい

            xa = def_a.get("x", 0)
            ya = def_a.get("y", 0)
            xb = def_b.get("x", 0)
            yb = def_b.get("y", 0)

            if abs(xa - xb) < 5 and abs(ya - yb) < 5:
                warnings.append(f"  OVERLAP: {name_a} と {name_b} が近すぎます ({xa},{ya})")

    return warnings


def verify_form(
    form: dict,
    template_dir: str,
    output_dir: str,
) -> tuple[str, list[str]]:
    """1フォームの座標検証を行う.

    Args:
        form: フォーム定義dict.
        template_dir: テンプレートPDFのディレクトリ.
        output_dir: 出力ディレクトリ.

    Returns:
        (出力パス, 警告リスト) のタプル.
    """
    name = form["name"]
    coords = form["coords"]
    page_size = form["size"]
    label = form["label"]

    out_path = Path(output_dir) / f"verify_{name}.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # テンプレートがあればオーバーレイ、なければ白紙に描画
    template_path = Path(template_dir) / f"{name}.pdf"

    c = canvas.Canvas(str(out_path), pagesize=page_size)

    # タイトル
    c.setFont("Helvetica", 8)
    c.setFillColor(Color(0.5, 0.5, 0.5))
    c.drawString(10, page_size[1] - 15, f"Coordinate Verification: {label} ({name})")

    # 各フィールドのマーカーを描画
    for field_name, field_def in coords.items():
        _draw_marker(c, field_name, field_def)

    c.save()

    # テンプレートが存在すればオーバーレイ
    if template_path.exists():
        try:
            from pypdf import PdfReader, PdfWriter

            template_reader = PdfReader(str(template_path))
            overlay_reader = PdfReader(str(out_path))
            writer = PdfWriter()

            page = template_reader.pages[0]
            if overlay_reader.pages:
                page.merge_page(overlay_reader.pages[0])
            writer.add_page(page)

            with open(str(out_path), "wb") as f:
                writer.write(f)
        except ImportError:
            pass  # pypdfがない場合はオーバーレイなしで出力

    # 重なりチェック
    warnings = _check_overlaps(coords)

    return str(out_path), warnings


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: uv run python scripts/verify_coordinates.py <templates_dir> <output_dir>")
        print()
        print("Example:")
        print("  uv run python scripts/verify_coordinates.py templates/ output/verify/")
        sys.exit(1)

    template_dir = sys.argv[1]
    output_dir = sys.argv[2]

    print(f"Template directory: {template_dir}")
    print(f"Output directory: {output_dir}")
    print()

    total_warnings: list[str] = []

    for form in FORMS:
        path, warnings = verify_form(form, template_dir, output_dir)
        n_fields = len(form["coords"])
        status = "OK" if not warnings else f"WARN ({len(warnings)})"
        print(f"  [{status}] {form['label']}: {n_fields} fields -> {Path(path).name}")

        if warnings:
            for w in warnings:
                print(f"    {w}")
            total_warnings.extend(warnings)

    print()
    if total_warnings:
        print(f"Total warnings: {len(total_warnings)}")
    else:
        print("No overlapping fields detected.")


if __name__ == "__main__":
    main()
