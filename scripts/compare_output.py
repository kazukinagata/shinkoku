"""Compare generated PDF output with benchmark PDF visually.

Converts both PDFs to images and generates side-by-side comparison.

Usage:
    uv run python scripts/compare_output.py output/full_tax_set_2025.pdf benchmark.pdf

Output:
    output/compare/
        page_1_compare.png
        page_2_compare.png
        ...
"""

from __future__ import annotations

import sys
from pathlib import Path

import pypdfium2 as pdfium


def pdf_to_images(
    pdf_path: str,
    output_dir: str,
    dpi: int = 150,
    prefix: str = "page",
) -> list[str]:
    """PDFの各ページをPNG画像に変換する.

    Args:
        pdf_path: PDFファイルのパス.
        output_dir: 画像出力ディレクトリ.
        dpi: 解像度.
        prefix: ファイル名のプレフィックス.

    Returns:
        生成された画像ファイルのパスリスト.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(pdf_path)
    images: list[str] = []

    for i in range(len(pdf)):
        page = pdf[i]
        scale = dpi / 72  # 72 DPI が PDF のデフォルト
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()

        output_path = out / f"{prefix}_{i + 1}.png"
        pil_image.save(str(output_path))
        images.append(str(output_path))

    return images


def create_comparison(
    generated_path: str,
    benchmark_path: str,
    output_dir: str = "output/compare",
    dpi: int = 150,
) -> list[str]:
    """生成PDFとベンチマークPDFの並置比較画像を生成する.

    Args:
        generated_path: 生成されたPDFのパス.
        benchmark_path: ベンチマークPDFのパス.
        output_dir: 比較画像の出力ディレクトリ.
        dpi: 解像度.

    Returns:
        生成された比較画像のパスリスト.
    """
    from PIL import Image, ImageDraw, ImageFont

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 両PDFを画像に変換
    gen_images = pdf_to_images(generated_path, str(out / "generated"), dpi, "gen")
    bench_images = pdf_to_images(benchmark_path, str(out / "benchmark"), dpi, "bench")

    max_pages = max(len(gen_images), len(bench_images))
    comparisons: list[str] = []

    for i in range(max_pages):
        gen_img = Image.open(gen_images[i]) if i < len(gen_images) else None
        bench_img = Image.open(bench_images[i]) if i < len(bench_images) else None

        # 最大サイズに合わせる
        max_w = max(
            gen_img.width if gen_img else 0,
            bench_img.width if bench_img else 0,
        )
        max_h = max(
            gen_img.height if gen_img else 0,
            bench_img.height if bench_img else 0,
        )

        if max_w == 0 or max_h == 0:
            continue

        # 並置画像（左: 生成, 右: ベンチマーク, 中央に区切り線）
        gap = 20
        label_height = 30
        canvas_w = max_w * 2 + gap
        canvas_h = max_h + label_height
        canvas_img = Image.new("RGB", (canvas_w, canvas_h), "white")

        # ラベル
        draw = ImageDraw.Draw(canvas_img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except OSError:
            font = ImageFont.load_default()

        draw.text((10, 5), f"Generated (page {i + 1})", fill="blue", font=font)
        draw.text((max_w + gap + 10, 5), f"Benchmark (page {i + 1})", fill="green", font=font)

        # 画像配置
        if gen_img:
            canvas_img.paste(gen_img, (0, label_height))
        if bench_img:
            canvas_img.paste(bench_img, (max_w + gap, label_height))

        # 区切り線
        draw.line(
            [(max_w + gap // 2, 0), (max_w + gap // 2, canvas_h)],
            fill="red",
            width=2,
        )

        compare_path = out / f"page_{i + 1}_compare.png"
        canvas_img.save(str(compare_path))
        comparisons.append(str(compare_path))

        print(f"  [OK] Page {i + 1}: {compare_path.name}")

    return comparisons


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: uv run python scripts/compare_output.py <generated.pdf> <benchmark.pdf>")
        print()
        print("Example:")
        print(
            "  uv run python scripts/compare_output.py output/full_tax_set_2025.pdf benchmark.pdf"
        )
        sys.exit(1)

    generated_path = sys.argv[1]
    benchmark_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "output/compare"

    for path, label in [(generated_path, "生成PDF"), (benchmark_path, "ベンチマークPDF")]:
        if not Path(path).exists():
            print(f"Error: {label}が見つかりません: {path}")
            sys.exit(1)

    print(f"Generated PDF: {generated_path}")
    print(f"Benchmark PDF: {benchmark_path}")
    print(f"Output directory: {output_dir}")
    print()

    comparisons = create_comparison(generated_path, benchmark_path, output_dir)

    print()
    print(f"Generated {len(comparisons)} comparison images.")


if __name__ == "__main__":
    main()
