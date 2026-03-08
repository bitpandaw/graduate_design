---
name: read-pdf
description: 使用 Python（PyMuPDF）读取 PDF 文件的文本内容。将内容写入 .txt 文件，Agent 再用 view_file 工具读取，避免终端编码问题。
---

# PDF 阅读 Skill

## 核心设计原则

> **Agent 不应该从终端输出中解析 PDF 内容。**
> 正确流程：脚本把 PDF → 写成 `.txt` 文件 → Agent 用 `view_file` 工具读取文件内容。

这样做的好处：
- ✅ 完全避免终端编码问题（中文乱码、截断等）
- ✅ Agent 能用 `view_file` 工具翻页阅读，不受终端宽度限制
- ✅ 一条命令搞定，简单可靠

## 依赖库

```bash
pip install PyMuPDF
```

## 使用步骤（Agent 必须严格按此执行）

### 第 1 步：运行脚本，提取 PDF 内容到 txt 文件

```bash
python .agents/skills/read-pdf/scripts/read_pdf.py "path/to/file.pdf"
```

脚本会：
1. 读取 PDF 全部内容
2. 写入 `path/to/file.txt`（与 PDF 同目录，同名）
3. 在终端打印输出文件的**绝对路径**

### 第 2 步：用 view_file 工具读取输出文件

从步骤 1 的输出中获取 txt 文件路径，然后调用 `view_file` 工具读取：

```
view_file("path/to/file.txt")
```

### 可选参数

| 参数 | 说明 | 示例 |
|---|---|---|
| `--pages 1,2,3` | 只提取指定页 | `--pages 1,2,5` |
| `--out result.txt` | 自定义输出路径 | `--out C:\tmp\out.txt` |

### 示例

```bash
# 读取全部页
python .agents/skills/read-pdf/scripts/read_pdf.py "graduate_thesis/论文.pdf"
# 输出：D:\code\market\graduate_thesis\论文.txt

# 只读第 1-3 页
python .agents/skills/read-pdf/scripts/read_pdf.py "graduate_thesis/论文.pdf" --pages 1,2,3

# 指定输出路径
python .agents/skills/read-pdf/scripts/read_pdf.py "graduate_thesis/论文.pdf" --out C:\tmp\thesis.txt
```

完成后，Agent 用 `view_file` 读取 txt 文件即可。
