"""
search_paper.py - 文献搜索工具（基于 arXiv API）
用法见 SKILL.md

支持操作：
  search   - 按关键词搜索论文，输出到 txt
  abstract - 获取指定论文的详细摘要，输出到 txt
  download - 下载指定论文的 PDF
  batch    - 批量下载搜索结果中的 PDF
"""

import argparse
import sys
import os
import json


def _require_arxiv():
    try:
        import arxiv
        return arxiv
    except ImportError:
        print("[ERROR] 缺少依赖库，请先运行：pip install arxiv", flush=True)
        sys.exit(1)


# ─────────────────────────────────────────────
# 操作：搜索论文
# ─────────────────────────────────────────────
def cmd_search(args):
    arxiv = _require_arxiv()

    query = args.query
    max_results = args.max
    sort_by_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "date": arxiv.SortCriterion.SubmittedDate,
        "updated": arxiv.SortCriterion.LastUpdatedDate,
    }
    sort_by = sort_by_map.get(args.sort, arxiv.SortCriterion.Relevance)

    print(f"[INFO] 正在搜索: {query}（最多 {max_results} 条，排序: {args.sort}）...", flush=True)

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by,
    )

    results = list(client.results(search))

    if not results:
        print("[WARN] 未找到相关论文。", flush=True)
        sys.exit(0)

    lines = [
        f"=== 搜索结果: {query} ===",
        f"共找到 {len(results)} 篇论文\n",
    ]

    entries = []
    for i, r in enumerate(results):
        entry = {
            "index": i,
            "id": r.entry_id.split("/")[-1],
            "title": r.title,
            "authors": [a.name for a in r.authors],
            "published": str(r.published.date()),
            "categories": r.categories,
            "abstract": r.summary.replace("\n", " "),
            "pdf_url": r.pdf_url,
            "arxiv_url": r.entry_id,
        }
        entries.append(entry)

        lines.append(f"[{i:02d}] {'─' * 60}")
        lines.append(f"  标题: {entry['title']}")
        lines.append(f"  作者: {', '.join(entry['authors'][:3])}{'等' if len(entry['authors']) > 3 else ''}")
        lines.append(f"  发布: {entry['published']}  分类: {', '.join(entry['categories'][:2])}")
        lines.append(f"  ID:   {entry['id']}")
        lines.append(f"  PDF:  {entry['pdf_url']}")
        lines.append(f"  摘要: {entry['abstract'][:200]}...")
        lines.append("")

    content = "\n".join(lines)

    if args.out:
        out_path = os.path.abspath(args.out)
    else:
        safe_query = query.replace(" ", "_").replace("/", "_")[:30]
        out_path = os.path.abspath(f"search_{safe_query}.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
        if args.json:
            f.write("\n\n=== JSON 数据 ===\n")
            f.write(json.dumps(entries, ensure_ascii=False, indent=2))

    print(out_path, flush=True)


# ─────────────────────────────────────────────
# 操作：获取指定论文摘要
# ─────────────────────────────────────────────
def cmd_abstract(args):
    arxiv = _require_arxiv()

    paper_id = args.id
    print(f"[INFO] 正在获取论文: {paper_id} ...", flush=True)

    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    results = list(client.results(search))

    if not results:
        print(f"[ERROR] 未找到论文: {paper_id}", flush=True)
        sys.exit(1)

    r = results[0]

    lines = [
        f"=== 论文详情 ===",
        f"",
        f"标题: {r.title}",
        f"",
        f"作者: {', '.join([a.name for a in r.authors])}",
        f"",
        f"发布日期: {r.published.date()}",
        f"更新日期: {r.updated.date()}",
        f"",
        f"分类: {', '.join(r.categories)}",
        f"",
        f"arXiv ID: {r.entry_id.split('/')[-1]}",
        f"PDF 链接: {r.pdf_url}",
        f"",
        f"{'─' * 60}",
        f"摘 要:",
        f"{'─' * 60}",
        f"",
        r.summary,
        f"",
    ]

    if r.comment:
        lines.append(f"备注: {r.comment}")

    content = "\n".join(lines)

    if args.out:
        out_path = os.path.abspath(args.out)
    else:
        safe_id = paper_id.replace("/", "_")
        out_path = os.path.abspath(f"abstract_{safe_id}.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(out_path, flush=True)


# ─────────────────────────────────────────────
# 操作：下载指定论文 PDF
# ─────────────────────────────────────────────
def cmd_download(args):
    arxiv = _require_arxiv()

    paper_id = args.id
    out_dir = os.path.abspath(args.dir) if args.dir else os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    print(f"[INFO] 正在下载: {paper_id} → {out_dir} ...", flush=True)

    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    results = list(client.results(search))

    if not results:
        print(f"[ERROR] 未找到论文: {paper_id}", flush=True)
        sys.exit(1)

    r = results[0]
    filename = args.name if args.name else None
    path = r.download_pdf(dirpath=out_dir, filename=filename)

    print(f"[OK] 下载完成: {path}", flush=True)
    print(path, flush=True)


# ─────────────────────────────────────────────
# 操作：批量下载搜索结果
# ─────────────────────────────────────────────
def cmd_batch(args):
    arxiv = _require_arxiv()

    query = args.query
    max_results = args.max
    out_dir = os.path.abspath(args.dir) if args.dir else os.path.join(os.getcwd(), "papers")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[INFO] 批量下载: {query}，最多 {max_results} 篇 → {out_dir}", flush=True)

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    downloaded = []
    for i, r in enumerate(client.results(search)):
        try:
            safe_title = r.title[:50].replace("/", "_").replace(":", "_")
            path = r.download_pdf(dirpath=out_dir, filename=f"{i:02d}_{safe_title}.pdf")
            downloaded.append(str(path))
            print(f"  [{i+1}/{max_results}] ✓ {r.title[:60]}", flush=True)
        except Exception as e:
            print(f"  [{i+1}/{max_results}] ✗ 下载失败: {e}", flush=True)

    # 写入下载清单
    log_path = os.path.join(out_dir, "download_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"搜索词: {query}\n")
        f.write(f"下载数量: {len(downloaded)}\n\n")
        for p in downloaded:
            f.write(p + "\n")

    print(f"\n[OK] 批量下载完成，共 {len(downloaded)} 篇。清单: {log_path}", flush=True)
    print(out_dir, flush=True)


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────
def main():
    _require_arxiv()

    parser = argparse.ArgumentParser(
        description="arXiv 文献搜索与下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search", help="按关键词搜索论文")
    p_search.add_argument("--query", required=True, help="搜索关键词（支持英文/中文拼音）")
    p_search.add_argument("--max", type=int, default=10, help="最多返回条数（默认 10）")
    p_search.add_argument("--sort", choices=["relevance", "date", "updated"], default="relevance")
    p_search.add_argument("--out", help="输出 txt 路径")
    p_search.add_argument("--json", action="store_true", help="同时输出 JSON 格式数据")

    # abstract
    p_abstract = sub.add_parser("abstract", help="获取指定论文摘要")
    p_abstract.add_argument("--id", required=True, help="arXiv 论文 ID（如 2301.07041）")
    p_abstract.add_argument("--out", help="输出 txt 路径")

    # download
    p_download = sub.add_parser("download", help="下载指定论文 PDF")
    p_download.add_argument("--id", required=True, help="arXiv 论文 ID")
    p_download.add_argument("--dir", help="下载目录（默认当前目录）")
    p_download.add_argument("--name", help="自定义文件名（不含 .pdf）")

    # batch
    p_batch = sub.add_parser("batch", help="批量搜索并下载 PDF")
    p_batch.add_argument("--query", required=True, help="搜索关键词")
    p_batch.add_argument("--max", type=int, default=5, help="最多下载篇数（默认 5）")
    p_batch.add_argument("--dir", help="下载目录（默认 ./papers/）")

    args = parser.parse_args()

    dispatch = {
        "search": cmd_search,
        "abstract": cmd_abstract,
        "download": cmd_download,
        "batch": cmd_batch,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
