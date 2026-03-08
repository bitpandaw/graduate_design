---
description: Agent 搜索并整理文献综述的自纠流程——确保文献来源可靠、内容准确、引用正确
---

# 文献搜索 + 自纠 Workflow

> **// turbo-all**

## 前置：读取 SKILL.md
操作前必须先读取：
- `.agents/skills/search-paper/SKILL.md`
- `.agents/skills/read-pdf/SKILL.md`

---

## 第 1 步：明确搜索策略（必须先声明）

Agent 在搜索前必须输出：

```
【搜索策略声明】
研究主题：[用一句话概括]
核心关键词：[英文，2-3个]
扩展关键词：[近义词/缩写，2-3个]
时间范围：[全部 / 近N年]
预期论文类型：[综述/实验/方法/应用]
```

---

## 第 2 步：搜索并读取结果

// turbo
```bash
python .agents/skills/search-paper/scripts/search_paper.py search \
  --query "关键词" --max 15 --sort relevance
```
用 `view_file` 读取输出 txt。

---

## 第 3 步：【强制】搜索结果自纠 — 必须输出以下格式

```
【搜索结果评估报告】
总数：找到 N 篇，其中直接相关 N 篇

相关性：[✅≥8篇相关 / ❌仅N篇相关，需换词重搜]
多样性：[✅涵盖综述/方法/应用 / ⚠️缺少某类，说明]
时效性：[✅有近3年论文 / ⚠️最新论文是XXXX年，偏老]
权威性：[✅有高引用论文 / ⚠️暂未发现]

决定：[✅进入第4步 | ❌换关键词"XXX"重搜（原因：XXX）]
```

如有 ❌，换关键词重搜，最多 3 轮，每轮记录不同关键词。

---

## 第 4 步：精读关键论文

对评分最高的 3-5 篇执行：

// turbo
```bash
python .agents/skills/search-paper/scripts/search_paper.py abstract --id "arxiv_id"
```

// turbo
```bash
python .agents/skills/search-paper/scripts/search_paper.py download \
  --id "arxiv_id" --dir "./papers"
python .agents/skills/read-pdf/scripts/read_pdf.py "papers/xxx.pdf"
```

每读完一篇，输出简报：
```
【论文简报 #N】
标题：XXX
核心贡献：[1-2句]
与本研究的关系：[直接相关/间接参考/对比基线]
可引用的论点：[具体内容]
```

---

## 第 5 步：【强制】综述草稿自纠 — 必须输出以下格式

写完综述段落后：

```
【综述质量自评报告】
评分：[1-10分]

事实准确性：[✅每个论点都有文献来源 / ❌第N句来源不明]
引用完整性：[✅N个观点均有引用 / ❌缺少引用：具体内容]
批判性分析：[✅指出了现有方法的局限 / ⚠️目前只是描述，未评价]
逻辑结构：[✅从宏观到微观有序展开 / ⚠️某处跳跃]
引出本研究：[✅最后指出了研究缺口 / ❌未说明本研究的必要性]

决定：[评分≥8 → 完成 | 评分<8 → 需改进：XXX，返回修改]
```

---

## 自纠失败处理

| 情况 | 处理方式 |
|---|---|
| 3轮搜索仍不足8篇相关 | 报告给用户，建议换研究角度或拓宽主题 |
| 摘要看不懂 | 下载全文 PDF，精读 Introduction 和 Conclusion |
| 引用内容与原文不符 | 用 `abstract` 重新核实，修正表述 |
| 综述评分连续<8，3轮仍未改善 | 停止，向用户展示当前版本请求指导 |
