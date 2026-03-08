"""
check_similarity.py - 论文查重初筛工具（中文文本相似度）
用法见 SKILL.md

支持操作：
  self    - 自查：在同一文档内检测高度相似的段落对
  compare - 对比：检测两个文档间相似的段落对
  scan    - 扫描整篇文档，输出各段落与平均相似度（热力图式报告）
"""

import argparse
import sys
import os


def _require_libs():
    missing = []
    try:
        import jieba
    except ImportError:
        missing.append("jieba")
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        missing.append("scikit-learn")
    if missing:
        print(f"[ERROR] 缺少依赖库，请先运行：pip install {' '.join(missing)}", flush=True)
        sys.exit(1)


def tokenize(text):
    """中文分词，返回空格分隔的词序列"""
    import jieba
    words = jieba.cut(text.strip(), cut_all=False)
    return " ".join(w for w in words if w.strip() and len(w) > 1)


def compute_similarity(texts):
    """计算文本列表的 TF-IDF 余弦相似度矩阵"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    tokenized = [tokenize(t) for t in texts]
    # 过滤空文本
    valid = [(i, t) for i, t in enumerate(tokenized) if t.strip()]
    if len(valid) < 2:
        return None, []

    indices = [i for i, _ in valid]
    valid_texts = [t for _, t in valid]

    try:
        vec = TfidfVectorizer(min_df=1)
        tfidf = vec.fit_transform(valid_texts)
        matrix = cosine_similarity(tfidf)
        return matrix, indices
    except Exception as e:
        print(f"[WARN] 相似度计算出错: {e}", flush=True)
        return None, []


def load_paragraphs(filepath, min_len=30):
    """从文本文件或 docx 文件中读取段落"""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(filepath)
            paras = [p.text.strip() for p in doc.paragraphs if len(p.text.strip()) >= min_len]
        except ImportError:
            print("[ERROR] 读取 docx 需要 python-docx：pip install python-docx", flush=True)
            sys.exit(1)
    else:
        # 读取 txt 文件
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        paras = [p.strip() for p in content.split("\n") if len(p.strip()) >= min_len]

    return paras


# ─────────────────────────────────────────────
# 操作：自查（同文档内相似段落检测）
# ─────────────────────────────────────────────
def cmd_self(args):
    filepath = os.path.abspath(args.file)
    if not os.path.exists(filepath):
        print(f"[ERROR] 文件不存在: {filepath}", flush=True)
        sys.exit(1)

    threshold = args.threshold
    min_len = args.min_len

    print(f"[INFO] 读取文件: {filepath}", flush=True)
    paras = load_paragraphs(filepath, min_len=min_len)
    print(f"[INFO] 有效段落数: {len(paras)}，相似度阈值: {threshold}", flush=True)

    if len(paras) < 2:
        print("[WARN] 有效段落数不足，无法分析。", flush=True)
        sys.exit(0)

    matrix, indices = compute_similarity(paras)
    if matrix is None:
        print("[WARN] 相似度计算失败", flush=True)
        sys.exit(1)

    # 找出高相似对
    high_pairs = []
    n = len(indices)
    for i in range(n):
        for j in range(i + 1, n):
            sim = matrix[i][j]
            if sim >= threshold:
                pi, pj = indices[i], indices[j]
                high_pairs.append((sim, pi, pj, paras[pi], paras[pj]))

    high_pairs.sort(reverse=True)

    lines = [
        f"=== 自查报告: {filepath} ===",
        f"有效段落数: {len(paras)}",
        f"相似度阈值: {threshold}",
        f"高相似段落对数: {len(high_pairs)}",
        "",
    ]

    if not high_pairs:
        lines.append("✅ 未发现高相似段落对，查重风险较低。")
    else:
        lines.append(f"⚠️  发现 {len(high_pairs)} 对高相似段落：\n")
        for rank, (sim, pi, pj, text_i, text_j) in enumerate(high_pairs[:50], 1):
            lines.append(f"[{rank:02d}] 相似度: {sim:.1%}  段落 [{pi}] vs 段落 [{pj}]")
            lines.append(f"  段落{pi}: {text_i[:100]}{'...' if len(text_i) > 100 else ''}")
            lines.append(f"  段落{pj}: {text_j[:100]}{'...' if len(text_j) > 100 else ''}")
            lines.append("")

    content = "\n".join(lines)

    if args.out:
        out_path = os.path.abspath(args.out)
    else:
        base = os.path.splitext(filepath)[0]
        out_path = base + "_self_check.txt"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(out_path, flush=True)


# ─────────────────────────────────────────────
# 操作：对比两个文档
# ─────────────────────────────────────────────
def cmd_compare(args):
    file1 = os.path.abspath(args.file1)
    file2 = os.path.abspath(args.file2)
    threshold = args.threshold
    min_len = args.min_len

    for fp in [file1, file2]:
        if not os.path.exists(fp):
            print(f"[ERROR] 文件不存在: {fp}", flush=True)
            sys.exit(1)

    print(f"[INFO] 读取文件 1: {file1}", flush=True)
    paras1 = load_paragraphs(file1, min_len=min_len)
    print(f"[INFO] 读取文件 2: {file2}", flush=True)
    paras2 = load_paragraphs(file2, min_len=min_len)

    print(f"[INFO] 文档1: {len(paras1)} 段，文档2: {len(paras2)} 段", flush=True)

    all_paras = paras1 + paras2
    split = len(paras1)

    matrix, indices = compute_similarity(all_paras)
    if matrix is None:
        print("[WARN] 相似度计算失败", flush=True)
        sys.exit(1)

    # 只找跨文档的高相似对
    idx1 = [i for i in range(len(matrix)) if indices[i] < split]
    idx2 = [i for i in range(len(matrix)) if indices[i] >= split]

    high_pairs = []
    for i in idx1:
        for j in idx2:
            sim = matrix[i][j]
            if sim >= threshold:
                pi = indices[i]
                pj = indices[j] - split
                high_pairs.append((sim, pi, pj, paras1[pi], paras2[pj]))

    high_pairs.sort(reverse=True)

    # 计算整体相似率
    overall = sum(s for s, *_ in high_pairs) / max(len(paras1), 1) if high_pairs else 0

    lines = [
        f"=== 对比报告 ===",
        f"文档1: {file1}（{len(paras1)} 段）",
        f"文档2: {file2}（{len(paras2)} 段）",
        f"相似度阈值: {threshold}",
        f"高相似段落对数: {len(high_pairs)}",
        f"估算相似率: {overall:.1%}",
        "",
    ]

    if not high_pairs:
        lines.append("✅ 未发现高相似内容，两文档差异较大。")
    else:
        lines.append(f"⚠️  发现 {len(high_pairs)} 对相似段落：\n")
        for rank, (sim, pi, pj, text_i, text_j) in enumerate(high_pairs[:50], 1):
            lines.append(f"[{rank:02d}] 相似度: {sim:.1%}")
            lines.append(f"  文档1 段落[{pi}]: {text_i[:120]}{'...' if len(text_i) > 120 else ''}")
            lines.append(f"  文档2 段落[{pj}]: {text_j[:120]}{'...' if len(text_j) > 120 else ''}")
            lines.append("")

    content = "\n".join(lines)

    if args.out:
        out_path = os.path.abspath(args.out)
    else:
        out_path = os.path.abspath("compare_report.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(out_path, flush=True)


# ─────────────────────────────────────────────
# 操作：全文扫描（热力报告）
# ─────────────────────────────────────────────
def cmd_scan(args):
    import numpy as np

    filepath = os.path.abspath(args.file)
    if not os.path.exists(filepath):
        print(f"[ERROR] 文件不存在: {filepath}", flush=True)
        sys.exit(1)

    min_len = args.min_len
    paras = load_paragraphs(filepath, min_len=min_len)

    if len(paras) < 2:
        print("[WARN] 有效段落不足，无法分析。", flush=True)
        sys.exit(0)

    matrix, indices = compute_similarity(paras)
    if matrix is None:
        print("[WARN] 相似度计算失败", flush=True)
        sys.exit(1)

    n = len(indices)
    # 每个段落与其他所有段落的平均相似度（排除自身）
    avg_sims = []
    for i in range(n):
        others = [matrix[i][j] for j in range(n) if j != i]
        avg_sims.append(np.mean(others) if others else 0.0)

    def risk_label(score):
        if score >= 0.6:
            return "🔴 高风险"
        elif score >= 0.35:
            return "🟡 中风险"
        else:
            return "🟢 低风险"

    lines = [
        f"=== 全文扫描报告: {filepath} ===",
        f"有效段落数: {len(paras)}",
        "",
        f"{'段落':<6} {'平均相似度':>8}  {'风险等级':<10}  段落预览",
        "─" * 80,
    ]

    overall_avg = float(np.mean(avg_sims))
    for rank, (i, sim) in enumerate(zip(indices, avg_sims)):
        preview = paras[i][:60].replace("\n", " ")
        lines.append(f"[{i:4d}]  {sim:>8.1%}  {risk_label(sim):<12}  {preview}")

    lines.append("─" * 80)
    lines.append(f"全文平均相似度: {overall_avg:.1%}")
    if overall_avg >= 0.5:
        lines.append("总体评估: ⛔ 整体重复度偏高，建议大幅修改。")
    elif overall_avg >= 0.3:
        lines.append("总体评估: ⚠️  存在中等重复风险，建议针对 🔴 段落进行改写。")
    else:
        lines.append("总体评估: ✅ 整体重复度较低，查重风险可控。")

    content = "\n".join(lines)

    if args.out:
        out_path = os.path.abspath(args.out)
    else:
        base = os.path.splitext(filepath)[0]
        out_path = base + "_scan.txt"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(out_path, flush=True)


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────
def main():
    _require_libs()

    parser = argparse.ArgumentParser(
        description="论文查重初筛工具（中文文本相似度）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # self
    p_self = sub.add_parser("self", help="自查：同文档内高相似段落检测")
    p_self.add_argument("--file", required=True, help="文档路径（.txt 或 .docx）")
    p_self.add_argument("--threshold", type=float, default=0.6, help="相似度阈值（0~1，默认 0.6）")
    p_self.add_argument("--min-len", type=int, default=30, dest="min_len", help="段落最小字符数（默认 30）")
    p_self.add_argument("--out", help="输出报告路径")

    # compare
    p_compare = sub.add_parser("compare", help="对比：检测两个文档间的相似内容")
    p_compare.add_argument("--file1", required=True, help="文档1路径")
    p_compare.add_argument("--file2", required=True, help="文档2路径")
    p_compare.add_argument("--threshold", type=float, default=0.5, help="相似度阈值（默认 0.5）")
    p_compare.add_argument("--min-len", type=int, default=30, dest="min_len")
    p_compare.add_argument("--out", help="输出报告路径")

    # scan
    p_scan = sub.add_parser("scan", help="全文扫描：输出每段风险等级热力报告")
    p_scan.add_argument("--file", required=True, help="文档路径（.txt 或 .docx）")
    p_scan.add_argument("--min-len", type=int, default=30, dest="min_len")
    p_scan.add_argument("--out", help="输出报告路径")

    args = parser.parse_args()

    dispatch = {
        "self": cmd_self,
        "compare": cmd_compare,
        "scan": cmd_scan,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
