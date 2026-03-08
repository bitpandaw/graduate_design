---
name: check-similarity
description: 论文查重本地初筛工具。使用 jieba 中文分词 + TF-IDF 余弦相似度，检测文档内重复段落或两文档间相似内容。结果写入 .txt 文件，Agent 用 view_file 读取。
---

# 查重初筛 Skill

## 核心设计原则

> **这是本地初筛工具，不能替代知网/维普等专业查重系统。**
> 用途：在提交正式查重前，自查和发现明显重复段落，提前修改。

适用场景：
- ✅ 查找论文内部重复段落（自我复制、段落重排）
- ✅ 对比与参考文献、旧草稿的相似度
- ✅ 全文风险评估，找出高风险段落
- ❌ 不能替代知网 / 维普 / PaperPass 等正式系统

结果写入 `.txt` 文件，**Agent 执行后必须用 `view_file` 读取。**

## 依赖库

```bash
pip install jieba scikit-learn
```

## 使用步骤（Agent 必须严格按此执行）

所有命令格式：
```bash
python .agents/skills/check-similarity/scripts/check_similarity.py <command> [options]
```

支持 `.txt` 和 `.docx` 文件（docx 需要 `pip install python-docx`）。

---

### 命令一：self — 自查（同文档内重复段落）

```bash
python .agents/skills/check-similarity/scripts/check_similarity.py self \
  --file "thesis.txt" --threshold 0.6
```

**执行后用 `view_file` 读取输出的 txt 报告。**

输出包含：
- 相似度超过阈值的段落对
- 每对的具体文本和相似度百分比

可选参数：
```bash
--threshold 0.6    # 相似度阈值（0~1，默认 0.6）
--min-len 30       # 段落最小字符数，过滤太短的段落（默认 30）
--out report.txt   # 自定义输出路径
```

---

### 命令二：compare — 对比两个文档

```bash
python .agents/skills/check-similarity/scripts/check_similarity.py compare \
  --file1 "my_thesis.txt" --file2 "reference_paper.txt" --threshold 0.5
```

**执行后用 `view_file` 读取输出的 txt 报告。**

输出包含：
- 两文档间高相似段落对
- 估算整体相似率

---

### 命令三：scan — 全文扫描（风险热力报告）

```bash
python .agents/skills/check-similarity/scripts/check_similarity.py scan \
  --file "thesis.txt"
```

**执行后用 `view_file` 读取输出的 txt 报告。**

输出包含每个段落的风险等级：
- 🔴 高风险（≥60%）—— 建议大幅改写
- 🟡 中风险（35%-60%）—— 建议适当调整
- 🟢 低风险（<35%）—— 基本安全

---

## 阈值参考

| 场景 | 建议阈值 | 说明 |
|---|---|---|
| 自查内部重复 | 0.6 | 同一文档内近似段落 |
| 与参考文献对比 | 0.5 | 警惕过度摘抄 |
| 宽松初步扫描 | 0.4 | 找出所有可疑位置 |

## 典型工作流：提交前自查

```
1. scan    → 全文扫描，了解整体风险分布（view_file 读取）
2. self    → 定位具体的高相似段落对
3. （Agent 就高风险段落提出改写建议）
4. （修改后用 read-write-docx skill 更新文档）
5. 再次 scan → 验证改写效果
6. 提交至学校查重系统做最终确认
```

## 注意事项

- 中文分词由 `jieba` 完成，首次运行会加载词典（正常现象）
- 相似度基于**词语共现**，对改写后的表述不敏感（和知网算法不同）
- 建议在修改完成、提交前 1-2 天进行正式查重
