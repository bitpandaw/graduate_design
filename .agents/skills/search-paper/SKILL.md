---
name: search-paper
description: 使用 arXiv API 搜索、获取摘要、下载学术论文 PDF。搜索结果写入 .txt 文件，Agent 再用 view_file 工具读取，避免终端编码问题。
---

# 文献搜索 Skill（arXiv）

## 核心设计原则

> **Agent 不应该从终端输出中解析搜索结果。**
> 正确流程：脚本把搜索结果 → 写成 `.txt` 文件 → Agent 用 `view_file` 工具读取。

## 依赖库

```bash
pip install arxiv
```

## 使用步骤（Agent 必须严格按此执行）

所有命令格式：
```bash
python .agents/skills/search-paper/scripts/search_paper.py <command> [options]
```

---

### 命令一：search — 按关键词搜索论文

```bash
python .agents/skills/search-paper/scripts/search_paper.py search \
  --query "large language model" --max 10
```

**Agent 执行后必须立即用 `view_file` 读取输出的 txt 路径。**

输出包含：
- 每篇论文的标题、作者、发布日期、分类
- arXiv ID（用于后续 download/abstract 命令）
- PDF 链接
- 摘要前 200 字符

可选参数：
```bash
--max 20              # 最多返回 20 篇（默认 10）
--sort relevance      # 排序方式：relevance / date / updated
--out results.txt     # 自定义输出路径
--json                # 同时附加 JSON 格式数据（方便解析）
```

---

### 命令二：abstract — 获取指定论文详细摘要

先用 `search` 找到论文 ID，再用 abstract 获取完整摘要。

```bash
python .agents/skills/search-paper/scripts/search_paper.py abstract \
  --id "2301.07041"
```

**执行后用 `view_file` 读取输出的 txt 文件。**

---

### 命令三：download — 下载指定论文 PDF

```bash
python .agents/skills/search-paper/scripts/search_paper.py download \
  --id "2301.07041" --dir "./papers"
```

下载完成后，可用 `read-pdf` skill 读取 PDF 内容。

可选参数：
```bash
--dir "./papers"      # 下载目录（默认当前目录）
--name "my_paper"     # 自定义文件名（不含 .pdf）
```

---

### 命令四：batch — 批量搜索并下载 PDF

```bash
python .agents/skills/search-paper/scripts/search_paper.py batch \
  --query "retrieval augmented generation" --max 5 --dir "./papers"
```

- 自动下载前 N 篇论文的 PDF
- 同时生成 `download_log.txt` 清单文件

---

## 典型工作流：文献综述

```
1. search  → 搜索领域关键词，了解有哪些论文
2. abstract → 对感兴趣的论文获取完整摘要
3. download → 下载重要论文 PDF
4. （使用 read-pdf skill）→ 精读 PDF 全文内容
5. 整理综述笔记
```

## 搜索技巧

| 场景 | 查询示例 |
|---|---|
| 精确短语 | `"knowledge graph"` |
| 多关键词 | `RAG retrieval generation` |
| 指定领域 | `cat:cs.AI transformer` |
| 指定作者 | `au:LeCun deep learning` |
| 近期论文 | 加 `--sort date` |
