# -*- coding: utf-8 -*-
"""
PDF 阅读辅助脚本 —— Agent 专用版
用法:
    python read_pdf.py <pdf_path> [--pages 1,2,3] [--out output.txt]

输出：
    将内容写入 txt 文件（默认写到 <pdf同目录>/<pdf名>.txt）
    最后一行打印输出文件路径，方便 Agent 用 view_file 工具读取
"""

import sys
import argparse
from pathlib import Path


def extract_text(pdf_path: str, pages: list[int] | None = None) -> str:
    """使用 PyMuPDF 提取 PDF 文本，返回完整字符串"""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    total = doc.page_count
    target = pages or list(range(1, total + 1))

    lines = [f"文件: {pdf_path}", f"总页数: {total}", ""]

    for n in target:
        if n < 1 or n > total:
            continue
        page = doc[n - 1]
        text = page.get_text("text").strip()
        lines.append(f"\n{'='*60}")
        lines.append(f"  第 {n} 页 / 共 {total} 页")
        lines.append(f"{'='*60}")
        lines.append(text)

    doc.close()
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("--pages", default=None, help="页码，逗号分隔，如 1,2,3")
    parser.add_argument("--out", default=None, help="输出文件路径（默认与PDF同目录）")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"[错误] 找不到文件: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    pages = None
    if args.pages:
        pages = [int(p.strip()) for p in args.pages.split(",")]

    text = extract_text(str(pdf_path), pages)

    # 确定输出路径
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = pdf_path.with_suffix(".txt")

    out_path.write_text(text, encoding="utf-8")

    # 只打印输出文件路径，Agent 用 view_file 读取
    print(str(out_path.resolve()))


if __name__ == "__main__":
    main()
