---
description: Agent 修改论文 docx 的自纠流程——确保每次修改都正确执行并经过验证
---

# 论文修改 + 自纠 Workflow

> **// turbo-all**

## 前置：读取 SKILL.md
操作前必须先读取以下 skill：
- `.agents/skills/read-write-docx/SKILL.md`

---

## 第 0 步：备份原文件

// turbo
```bash
copy "原文件.docx" "原文件_backup.docx"
```

---

## 第 1 步：读取全文，理解当前内容

// turbo
```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py read "文件.docx"
```
用 `view_file` 读取输出 txt，**在脑中记录需要修改的段落原文**。

---

## 第 2 步：执行修改操作

根据任务执行 replace / insert / delete / comment。

---

## 第 3 步：【强制】技术自纠 — 必须输出以下格式

每次修改后，Agent 必须立即执行读回并输出结构化报告：

// turbo
```bash
python .agents/skills/read-write-docx/scripts/edit_docx.py read "文件.docx"
```

**Agent 必须用以下固定格式输出验证结论，不得省略任何一项：**

```
【技术验证报告】
✅/❌ 修改是否生效：[是/否，并引用文档中找到的具体文字证明]
✅/❌ 修改数量是否正确：[执行了N处修改，读回找到N处，匹配/不匹配]
✅/❌ 原文是否已被替换：[原文"XXX"在读回结果中 已不存在/仍存在]
⚠️  发现的异常：[无 / 具体描述异常]
📋 下一步：[继续第4步 / 重试修改（原因：XXX）]
```

如果报告中有 ❌，执行 `reject` 撤销并重试，最多 3 次，3 次仍失败则向用户报告。

---

## 第 4 步：【强制】内容质量自纠 — 必须输出以下格式

所有修改完成后，Agent 切换为"严格的学术导师"视角，输出：

```
【内容质量自评报告】
评分：[1-10分]

逻辑连贯性：[✅通过 / ⚠️问题描述]
学术规范性：[✅通过 / ⚠️问题描述]（有无口语化、表达是否严谨）
上下文衔接：[✅通过 / ⚠️问题描述]（修改后段落与前后文是否流畅）
格式一致性：[✅通过 / ⚠️问题描述]

总结：[一句话说明本次修改的整体质量]
决定：[评分≥8 → 结束 | 评分<8 → 说明需要再改哪里，返回第2步]
```

评分 < 8 则必须继续修改，一轮最多 3 次循环。

---

## 第 5 步：查重风险初筛（添加大量新内容时执行）

// turbo
```bash
python .agents/skills/check-similarity/scripts/check_similarity.py self \
  --file "文件.txt" --threshold 0.6
```
用 `view_file` 读取报告，对 🔴 高风险段落提出改写建议。

---

## 自纠失败处理规则

| 情况 | 处理方式 |
|---|---|
| replace 后读回未找到新文本 | 用 `info` 命令确认段落原文，检查空格/标点是否完全一致，重试 |
| 修订数量少于预期 | 说明锚点未找到，重新 `read` 确认后重试 |
| 修改后逻辑断裂 | `reject` 撤销，改用 `comment` 标注，请用户决策 |
| 连续 3 次自纠失败 | 停止，向用户完整报告失败原因 |
