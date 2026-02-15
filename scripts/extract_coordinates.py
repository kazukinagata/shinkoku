"""Extract text coordinates from a benchmark PDF using pdfplumber.

Reads all text elements (characters) from each page and outputs JSON field
definitions with coordinates converted to ReportLab's coordinate system
(origin at bottom-left).

Usage:
    uv run --with pdfplumber python scripts/extract_coordinates.py benchmark.pdf coordinates/

Output:
    coordinates/
        page_1.json  # 確定申告書B 第一表
        page_2.json  # 確定申告書B 第二表
        ...

Coordinate conversion:
    pdfplumber: y=0 is top of page, y increases downward
    ReportLab:  y=0 is bottom of page, y increases upward
    reportlab_y = page_height - pdfplumber_top
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pdfplumber


# ページ名マッピング（extract_templates.pyと対応）
PAGE_NAMES = [
    "income_tax_p1",
    "income_tax_p2",
    "blue_return_pl_p1",
    "blue_return_pl_p2",
    "blue_return_pl_p3",
    "blue_return_bs",
    "consumption_tax_p1",
    "consumption_tax_p2",
    "housing_loan_p1",
    "housing_loan_p2",
]


def _detect_digit_cells(
    chars: list[dict],
    tolerance: float = 2.0,
) -> list[dict]:
    """同一行の単一文字列から桁別セルパターンを検出する.

    同じy座標（tolerance内）にある単一文字（数字）が等間隔で並んでいる場合、
    digit_cellsフィールドとして認識する。

    Args:
        chars: pdfplumberのcharオブジェクトリスト.
        tolerance: y座標の許容誤差（pt）.

    Returns:
        検出されたdigit_cellsフィールドのリスト.
    """
    # y座標でグループ化
    rows: dict[float, list[dict]] = {}
    for ch in chars:
        if not ch.get("text", "").strip():
            continue
        y_key = round(ch["top"] / tolerance) * tolerance
        rows.setdefault(y_key, []).append(ch)

    digit_cells: list[dict] = []
    for y_key, row_chars in rows.items():
        # x座標でソート
        row_chars.sort(key=lambda c: c["x0"])

        # 単一文字のみ抽出
        single_chars = [c for c in row_chars if len(c["text"].strip()) == 1]
        if len(single_chars) < 3:
            continue

        # 等間隔チェック
        x_positions = [c["x0"] for c in single_chars]
        intervals = [x_positions[i + 1] - x_positions[i] for i in range(len(x_positions) - 1)]
        if not intervals:
            continue

        avg_interval = sum(intervals) / len(intervals)
        if avg_interval < 5:  # 最小間隔
            continue

        # 間隔のばらつきが小さいか
        max_deviation = max(abs(iv - avg_interval) for iv in intervals)
        if max_deviation > 2.0:
            continue

        # digit_cellsとして記録
        page_height = single_chars[0].get("page_height", 842)
        font_size = float(single_chars[0].get("size", 10))
        reportlab_y = page_height - float(single_chars[0]["top"])

        digit_cells.append(
            {
                "type": "digit_cells",
                "x_start": round(float(x_positions[0]), 1),
                "y": round(reportlab_y, 1),
                "cell_width": round(avg_interval, 1),
                "num_cells": len(single_chars),
                "font_size": round(font_size, 1),
                "sample_text": "".join(c["text"] for c in single_chars),
            }
        )

    return digit_cells


def extract_page_coordinates(page: pdfplumber.page.Page, page_idx: int) -> dict:
    """1ページ分のテキスト座標を抽出する.

    Args:
        page: pdfplumberのページオブジェクト.
        page_idx: ページ番号（0-indexed）.

    Returns:
        ページの座標定義dict.
    """
    width = float(page.width)
    height = float(page.height)

    chars = page.chars
    # ページ高さ情報を各charに付与
    for ch in chars:
        ch["page_height"] = height

    # 全文字要素のReportLab座標変換
    text_elements: list[dict] = []
    for ch in chars:
        if not ch.get("text", "").strip():
            continue
        rl_y = height - float(ch["top"])
        text_elements.append(
            {
                "text": ch["text"],
                "x": round(float(ch["x0"]), 1),
                "y": round(rl_y, 1),
                "font_size": round(float(ch.get("size", 10)), 1),
                "font_name": ch.get("fontname", ""),
            }
        )

    # 桁別セル検出
    digit_cells = _detect_digit_cells(chars)

    # 通常テキスト（ワード単位で結合）
    words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
    text_fields: list[dict] = []
    for w in words:
        rl_y = height - float(w["top"])
        text_fields.append(
            {
                "type": "text",
                "text": w["text"],
                "x": round(float(w["x0"]), 1),
                "y": round(rl_y, 1),
                "width": round(float(w["x1"]) - float(w["x0"]), 1),
                "font_size": round(float(w.get("bottom", 0) - w.get("top", 0)) * 0.75, 1),
            }
        )

    return {
        "page_index": page_idx,
        "page_name": PAGE_NAMES[page_idx] if page_idx < len(PAGE_NAMES) else f"page_{page_idx + 1}",
        "page_size": [round(width, 1), round(height, 1)],
        "orientation": "landscape" if width > height else "portrait",
        "digit_cells": digit_cells,
        "text_fields": text_fields,
        "raw_char_count": len(text_elements),
    }


def extract_all_coordinates(benchmark_path: str, output_dir: str) -> list[str]:
    """ベンチマークPDFから全ページの座標を抽出する.

    Args:
        benchmark_path: ベンチマークPDFのパス.
        output_dir: JSON出力ディレクトリ.

    Returns:
        生成されたJSONファイルのパスリスト.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []

    with pdfplumber.open(benchmark_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            coords = extract_page_coordinates(page, idx)

            name = coords["page_name"]
            output_path = out / f"{name}.json"

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(coords, f, ensure_ascii=False, indent=2)

            n_digits = len(coords["digit_cells"])
            n_text = len(coords["text_fields"])
            print(
                f"  [OK] Page {idx + 1} ({name}): "
                f"{n_digits} digit_cells, {n_text} text_fields, "
                f"{coords['raw_char_count']} raw chars"
            )
            generated.append(str(output_path))

    return generated


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: uv run --with pdfplumber python scripts/extract_coordinates.py "
            "<benchmark.pdf> <output_dir>"
        )
        print()
        print("Example:")
        print(
            "  uv run --with pdfplumber python scripts/extract_coordinates.py "
            "benchmark.pdf coordinates/"
        )
        sys.exit(1)

    benchmark_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not Path(benchmark_path).exists():
        print(f"Error: ベンチマークPDFが見つかりません: {benchmark_path}")
        sys.exit(1)

    print(f"Extracting coordinates from: {benchmark_path}")
    print(f"Output directory: {output_dir}")
    print()

    generated = extract_all_coordinates(benchmark_path, output_dir)

    print()
    print(f"Generated {len(generated)} coordinate JSON files.")


if __name__ == "__main__":
    main()
