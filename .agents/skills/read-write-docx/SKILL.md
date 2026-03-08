---
name: read-write-docx
description: 使用 Python（docx-editor 库）完整读写 .docx 文件。支持读取内容、带 Track Changes 修订跟踪的文本替换/插入/删除、添加评论批注、管理修订（接受/拒绝）。内容写入 .txt 文件，Agent 再用 view_file 工具读取，避免终端编码问题。
---

# DOCX 读写编辑 Skill

## 核心设计原则

> **Agent 不应该从终端输出中解析 DOCX 内容。**
> 正确流程：脚本把 docx → 写成 `.txt` 文件 → Agent 用 `view_file` 工具读取文件内容。

优势：
- ✅ 完全避免终端编码问题（中文乱码、截断等）
- ✅ Agent 能用 `view_file` 工具翻页阅读
- ✅ **Track Changes 修订跟踪**：替换/插入/删除操作在 Word 里显示为红色标注，导师可审阅
- ✅ **评论批注**：可在指定文本处添加评论，导师可见

## 依赖库

```bash
pip install python-docx docx-editor
```

> 注意：读取用 `python-docx`，修改（Track Changes）用 `docx-editor`，两个都需要安装。

## 脚本路径（正确路径）

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py <command> <file> [options]
```

> ⚠️ 脚本文件名是 `edit_docx.py`，不是 `docx_editor.py`。

---

## 支持的所有命令

| 命令 | 功能 |
|---|---|
| `read` | 读取全文内容 → 写 txt → `view_file` 读取 |
| `info` | 查看段落结构（索引 + 样式）→ 写 txt |
| `replace` | 替换文本（带 Track Changes） |
| `insert` | 在锚点文本后插入内容（带 Track Changes） |
| `delete` | 删除匹配文本（带 Track Changes） |
| `comment` | 在指定文本处添加评论批注 |
| `revisions` | 列出所有 Track Changes 修订记录 → 写 txt |
| `accept` | 接受修订（全部 / 指定 ID / 指定作者） |
| `reject` | 拒绝修订（全部 / 指定作者） |

---

### 命令一：read — 读取全文内容

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py read "path/to/file.docx"
```

输出格式：每段落 `[索引] (样式名) 文本内容`，写入同目录同名 `.txt` 文件。
终端打印输出 txt 文件的**绝对路径**，**Agent 必须立即用 `view_file` 读取**。

可选参数：
```bash
--out result.txt   # 自定义输出路径
```

---

### 命令二：info — 查看文档结构

**在执行 insert/delete 等操作前，必须先运行 info 确认段落索引。**

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py info "path/to/file.docx"
```

输出 `_info.txt`，包含每段落的索引、样式名、前60字符预览。**Agent 必须用 `view_file` 读取。**

---

### 命令三：replace — 替换文本（带 Track Changes）

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py replace "path/to/file.docx" \
  --old "原始文本" \
  --new "替换后文本"
```

可选参数：
```bash
--author "AI Agent"       # 修订作者名（Word里显示）
--out "output.docx"       # 另存为新文件（推荐，保留原文件）
```

---

### 命令四：insert — 在锚点文本后插入（带 Track Changes）

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py insert "path/to/file.docx" \
  --anchor "定位在此文本之后" \
  --text "要插入的新内容"
```

> 注意：`--anchor` 是文本内容定位，不是段落索引号。

可选参数：
```bash
--author "AI Agent"   # 修订作者名
```

---

### 命令五：delete — 删除匹配文本（带 Track Changes）

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py delete "path/to/file.docx" \
  --text "要删除的文本内容"
```

可选参数：
```bash
--author "AI Agent"   # 修订作者名
```

---

### 命令六：comment — 添加评论批注

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py comment "path/to/file.docx" \
  --anchor "要批注的文本" \
  --text "评论内容"
```

可选参数：
```bash
--author "AI Agent"   # 批注作者名
```

---

### 命令七：revisions — 查看 Track Changes 记录

```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py revisions "path/to/file.docx"
```

输出 `_revisions.txt`，列出所有修订记录。**Agent 用 `view_file` 读取。**

---

### 命令八：accept — 接受修订

```bash
# 接受全部修订
python .agents/skills/read-write-docx/scripts/edit_docx.py accept "path/to/file.docx"

# 接受指定 ID 的修订
python .agents/skills/read-write-docx/scripts/edit_docx.py accept "path/to/file.docx" --id 3

# 接受指定作者的全部修订
python .agents/skills/read-write-docx/scripts/edit_docx.py accept "path/to/file.docx" --author "AI Agent"
```

---

### 命令九：reject — 拒绝修订

```bash
# 拒绝全部修订
python .agents/skills/read-write-docx/scripts/edit_docx.py reject "path/to/file.docx"

# 拒绝指定作者的修订
python .agents/skills/read-write-docx/scripts/edit_docx.py reject "path/to/file.docx" --author "AI Agent"
```

---

## 典型工作流：Agent 修改论文

```
1. read      → 读取全文，了解内容（view_file 读取）
2. info      → 查看段落结构和索引（view_file 读取）
3. replace   → 替换错误内容（Track Changes 记录）
4. insert    → 在指定位置插入新段落（Track Changes 记录）
5. comment   → 对某段添加批注建议
6. revisions → 查看所有修订（view_file 读取）
7. accept    → 确认无误后接受所有修订
8. read      → 再次读取，确认最终内容（view_file 读取）
```

## 重要提醒

- 执行 `read` / `info` / `revisions` 后，**必须立即调用 `view_file` 读取输出的 txt 文件**
- 修改操作（replace/insert/delete）推荐使用 `--out` 保存到新文件，保留原始文件
- `insert` 的 `--anchor` 是**文本内容**定位，而非段落索引

## 常用样式名

| 含义 | 样式名 |
|---|---|
| 正文 | `Normal` |
| 一级标题 | `Heading 1` |
| 二级标题 | `Heading 2` |
| 三级标题 | `Heading 3` |
| 列表段落 | `List Paragraph` |
