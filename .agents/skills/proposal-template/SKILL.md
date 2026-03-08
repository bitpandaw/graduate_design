---
name: proposal-template
description: 生成标准毕业设计开题报告 .docx 模板，并用 JSON 数据填充模板生成正式文档。使用 python-docx + docxtpl（Jinja2）实现。
---

# 开题报告模板 Skill

## 核心设计原则

> 两步工作流：先 `init` 生成模板，再 `fill` 填充数据生成正式文档。

优势：
- ✅ 模板格式一次设定，多次复用
- ✅ Agent 只需准备 JSON 数据，自动填入所有占位符
- ✅ 支持自定义模板（Word 里改格式，脚本填内容）

## 依赖库

```bash
pip install python-docx docxtpl
```

## 使用步骤（Agent 必须严格按此执行）

所有命令格式：
```bash
python .agents/skills/proposal-template/scripts/generate_proposal.py <command> [options]
```

---

### 命令一：init — 创建标准开题报告模板

```bash
python .agents/skills/proposal-template/scripts/generate_proposal.py init \
  --out proposal_template.docx
```

生成包含以下 `{{ 变量 }}` 占位符的模板：
- 封面信息：`project_title`, `student_name`, `student_id`, `major`, `advisor`, `college`, `date`
- 正文部分：`background`, `literature_review`, `research_goals`, `methodology`, `expected_results`, `references`
- 时间安排表：`phase1_time` ~ `phase6_time`, `phase1_task` ~ `phase6_task`
- 审核意见：`advisor_comment`, `sign_date`

**注意：生成后可以用 Word 打开模板，调整字体格式，不要删除 `{{ }}` 占位符。**

---

### 命令二：show — 查看模板中所有变量

```bash
python .agents/skills/proposal-template/scripts/generate_proposal.py show \
  --template proposal_template.docx --out variables.txt
```

**执行后用 `view_file` 读取输出的 txt 文件。**

输出包含：
- 所有 `{{ 变量名 }}` 列表
- 示例 JSON 数据（可直接复制修改）

---

### 命令三：fill — 用 JSON 数据填充模板

**第 1 步**：准备 JSON 数据文件（`proposal_data.json`）：

```json
{
  "project_title": "基于大语言模型的知识图谱问答系统研究",
  "student_name": "张三",
  "student_id": "202301001",
  "major": "计算机科学与技术",
  "advisor": "李教授",
  "college": "信息工程学院",
  "date": "2026年3月",
  "background": "随着人工智能技术的快速发展...",
  "literature_review": "国内外学者在该领域已有大量研究...",
  "research_goals": "本研究旨在设计并实现...",
  "methodology": "采用RAG框架结合知识图谱...",
  "expected_results": "预期完成系统开发，达到...",
  "references": "[1] 张三. 大语言模型综述. 2024.\n[2] Smith J. RAG Survey. 2023.",
  "phase1_time": "第1-2周",
  "phase1_task": "文献调研，完成文献综述",
  "phase2_time": "第3-4周",
  "phase2_task": "系统设计，确定技术方案",
  "phase3_time": "第5-10周",
  "phase3_task": "系统开发与实现",
  "phase4_time": "第11-12周",
  "phase4_task": "系统测试与优化",
  "phase5_time": "第13-14周",
  "phase5_task": "论文撰写",
  "phase6_time": "第15-16周",
  "phase6_task": "论文修改与答辩准备",
  "advisor_comment": "（待导师填写）",
  "sign_date": "2026年3月"
}
```

**第 2 步**：填充模板生成正式文档：

```bash
python .agents/skills/proposal-template/scripts/generate_proposal.py fill \
  --template proposal_template.docx \
  --data proposal_data.json \
  --out proposal_final.docx
```

---

## 典型工作流：Agent 帮我写开题报告

```
1. init    → 创建模板文件
2. show    → 查看所有变量（view_file 读取）
3. （Agent 根据学生提供的题目和方向，生成 JSON 数据）
4. fill    → 填充模板，生成 .docx 正式文档
5. （使用 read-write-docx skill 进一步精调内容）
```

## 自定义模板

如果学校有专属格式要求：
1. 用 `init` 生成默认模板
2. 用 Word 打开，调整字体/格式/页眉页脚
3. 在需要填充的位置手动输入 `{{ 变量名 }}`（保留双花括号）
4. 保存，之后用 `fill` 命令填充即可
