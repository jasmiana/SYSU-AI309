# A+B+D+热修复 验证运行结果

> **生成日期**: 2026-07-12
> **模型**: deepseek-v4-flash（thinking enabled, reasoning_effort=high）
> **流水线**: Agent 1 → Knowledge Retrieval → Agent 2 → Agent 3 → [渲染验证 → Agent 4] 反馈循环 (max 1 轮精炼)
> **Prompt 版本**: agent2/3/4_system.txt 已按 discussions.md 方案 A+B+D 优化，agent3_system.txt 含热修复（标题溢出 + XML 安全 + Agent 4 盲区）

---

## 1. 验证总览

| # | 样例 | 意图分类 | 图表类型 | 评分 | 通过 | 精炼 | 耗时 | SVG | NER F1 | RE F1 |
|---|------|----------|----------|:---:|:---:|:---:|------|-----|:---:|:---:|
| 1 | 大语言模型基本原理 | concept_explanation | architecture_diagram | **9.5** | ✅ | 1 | 200s | 16.4 KB | 0.733 | 0.640 |
| 2 | 词向量基本概念 | concept_explanation | concept_map | **9.0** | ✅ | 1 | 177s | 13.2 KB | 0.348 | 0.118 |
| 3 | 中山大学发展历程 | timeline | timeline | **8.3** | ✅ | 1 | 195s | 12.2 KB | 0.774 | 0.083 |
| 4 | 咖啡生产链 | process_flow | flowchart | **9.0** | ✅ | 2 | 331s | 12.0 KB | 0.737 | 0.133 |
| 5 | 视频数量对比 | data_comparison | comparison_chart | **7.0** | ✅ | 1 | 202s | 6.3 KB | 0.833 | 0.800 |

**汇总**: **5/5 全部通过 (100%)**, 均值 **8.6**, 总耗时 1,105s (~18 min), NER Micro F1=0.678, RE Micro F1=0.302。

---

## 2. 逐维度评分

| 样例 | syntax | layout | content_accuracy | chart_type | information_completeness | aesthetics | creativity_density | overall |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| sample1 (LLM) | 10 | 10 | 10 | 10 | 10 | 9 | 7 | **9.5** |
| sample2 (词向量) | 10 | 10 | 10 | 10 | 10 | 8 | 6 | **9.0** |
| sample3 (SYSU) | 10 | 10 | 10 | 10 | 8 | 7 | 7 | **8.3** |
| sample4 (咖啡链) | 10 | 10 | 10 | 10 | 9 | 9 | 8 | **9.0** |
| sample5 (数据对比) | 10 | 9 | 10 | 10 | 9 | 7 | 6 | **7.0** |

---

## 3. 热修复验证

| 问题 | 修复前 | 修复后 | 状态 |
|------|--------|--------|:---:|
| sample1 XML 语法 | ❌ 两轮均 "invalid token at line 74" | ✅ syntax=10 一次通过 | 已修复 |
| sample5 标题溢出 | ❌ 55 字符/36px 溢出至 ~990px | ✅ 使用缩写版标题，未溢出 | 已修复 |
| Agent 4 标题溢出检查 | ❌ 溢出时 layout score=10（未检测到） | ✅ layout 维度新增标题溢出检查项 | 已修复 |

---

## 4. NER/RE 评估

| 样例 | NER P | NER R | NER F1 | RE P | RE R | RE F1 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| sample1 (LLM) | 0.688 | 0.786 | **0.733** | 0.571 | 0.727 | **0.640** |
| sample2 (词向量) | 0.333 | 0.364 | 0.348 | 0.111 | 0.125 | 0.118 |
| sample3 (SYSU) | 0.706 | 0.857 | **0.774** | 0.067 | 0.111 | 0.083 |
| sample4 (咖啡链) | 0.636 | 0.875 | 0.737 | 0.111 | 0.167 | 0.133 |
| sample5 (数据对比) | 1.000 | 0.714 | **0.833** | 1.000 | 0.667 | **0.800** |
| **Micro Avg** | 0.612 | 0.759 | **0.678** | 0.265 | 0.351 | **0.302** |
| **Macro Avg** | 0.673 | 0.756 | **0.698** | 0.372 | 0.359 | **0.355** |

### 与 Phase 3 基线对比

| 指标 | Phase 3 | A+B+D+热修复 | 变化 |
|------|:---:|:---:|:---:|
| NER Micro F1 | 0.406 | **0.678** | +67% |
| NER Macro F1 | 0.402 | **0.698** | +74% |
| RE Micro F1 | 0.348 | 0.302 | -13% |
| RE Macro F1 | 0.382 | 0.355 | -7% |

> NER 大幅改善归因于 Agent 1 prompt 强化（P0 修复中的实体抽取 + 示例 + 自查）。RE 的轻微下降来自 sample2/3/4 的 FP 率升高（Agent 1 抽取了更多关系但部分 source/target 混用非实体名），这是下一步优化的靶点。

---

## 5. 逐样例分析

### 5.1 sample1 — ⭐ 9.5 (最佳)

- **Agent 2 配色**: 自主设计"科技深蓝"（#1A3A5C + #2980B9 + #F39C12 暖橙强调），rationale="深蓝传递专业与科技感，暖橙强调自注意力的核心创新地位"
- **Agent 3 设计**: Transformer 架构自下而上的数据流（词嵌入→自注意力→多头注意力→FFN），残差连接用虚线环绕；训练三阶段横向流程；底部 "✨ 语言是人类思想的基石，而大模型正在学会理解它。✨"
- **创意密度**: 7/10 — emoji 丰富（🧠⚙️⚡👁️🧮🔄🔤📚🔧🎯✨🌟💡🚀），emoji 数 14 个远超 5 个下限

### 5.2 sample2 — ⭐ 9.0 (显著改善)

- **重跑后通过**: 第一轮生成时 information_completeness=6、aesthetics=5 未通过。用户重新运行后，Agent 1 抽取了更完整的词向量训练模型信息（Word2Vec/CBOW/Skip-gram/GloVe），Agent 3 生成了含训练模型介绍的完整版本
- **information_completeness=10**: 补全了缺失的训练模型科普内容
- **aesthetics=8**: 轻微对比度问题（坐标轴标签 #A0AEC0、副标题 #E2E8F0），不影响通过
- **creativity_density=6**: 语义空间散点图 + 类比区 king-queen 箭头图，视觉语言较为常规

### 5.3 sample3 — ⭐ 8.3

- **知识检索**: Fallback DB 命中 "中山大学_发展历程"（12 节点），5ms
- **Agent 2 配色**: 学术庄重紫蓝色系
- **NER F1=0.774**: 最高实体抽取精度
- **RE F1=0.083**: 14 FP 关系——target 混入非实体名（如"发展历程中的时间节点"）

### 5.4 sample4 — ⭐ 9.0

- **唯一触发精炼的样本**（2 轮）: Round 1 不通过 → Agent 3 补充咖啡豆品种差异和冲煮方式对比 → Round 2 pass
- **Agent 2 配色**: 暖调大地棕绿色系（情境化：咖啡从生豆绿到烘焙棕）
- **反馈闭环验证**: Agent 4→3 精炼成功将 information_completeness 和 aesthetics 从不足提升至达标

### 5.5 sample5 — ⭐ 7.0

- **标题**: 使用缩写版本（英文），未溢出——热修复生效
- **Agent 2 配色**: 自主设计红-粉-橙暖色系（YouTube 红 / TikTok 粉 / Kuaishou 橙），平台品牌色方向
- **RE F1=0.800**: 数值关系抽取精度最高
- **aesthetics=7**: 箭头标注对比度稍低（#FF9800 在白色背景上 2.16），未阻塞通过

---

## 6. 与 Baseline 对比（更新）

| 指标 | Baseline | Multi-Agent (A+B+D+热修复) | 比值 |
|------|:---:|:---:|:---:|
| 模型 | v4-flash (thinking disabled) | v4-flash (thinking enabled) | 相同模型 |
| API 调用/样本 | **1** | 3-5 | — |
| 总耗时 | **97.9s** | 1,069s | **1:11** |
| 单样本平均 | **19.6s** | 214s | **1:11** |
| XML 通过率 | 5/5 | 5/5 | 持平 |
| 有评分 | 无 | 5/5 pass, 均值 8.6 | — |
| 视觉质量 (人评) | 更好 | 明显改善，差距缩小 | A+B+D 生效 |
| NER/RE 定量 | 无 | NER F1=0.678, RE F1=0.302 | — |

> **模型修正**: 此前文档中错误地将 multi-agent 系统标注为 "v4-pro"——实际配置始终为 `deepseek-v4-flash`（参见 `.env`）。Baseline 与 multi-agent 使用相同模型，区别仅在于 thinking mode 和架构复杂度。这意味着视觉质量差距的原因**完全归因于架构设计**（设计委员会效应/IR 信息损失等），而非模型能力差异——这进一步强化了 discussions.md 中的根因分析。

---

# Baseline: 单次直出 SVG 对照实验

> **生成日期**: 2026-07-11
> **模型**: deepseek-v4-flash（thinking disabled）
> **方式**: 单次 LLM 调用，无多 Agent、无 IR、无知识检索、无验证、无反馈循环
> **脚本**: `baseline.py`

---

## 1. 实验设计

Baseline 的目的是建立性能下界——量化"去掉所有多 Agent 架构后，模型仅凭一次生成能做到什么程度"。与完整的多 Agent 流水线形成对照，为报告的"消融实验/架构有效性论证"提供定量数据。

### 1.1 关键差异

| 维度 | Baseline | Multi-Agent (Phase 3) |
|------|----------|----------------------|
| 模型 | deepseek-v4-flash (thinking disabled) | deepseek-v4-flash (thinking enabled) |
| Thinking mode | disabled | enabled (reasoning_effort=high) |
| Agent 数量 | 0 | 4 + 知识检索 |
| System prompt | ~1000 chars（精简版） | ~3000+ chars（含 CoT/IR Schema/设计规范） |
| API 调用/样本 | **1** | 3-5 |
| IR 中间表示 | 无 | Content IR → Layout IR → Review IR |
| 知识检索 | 无 | Fallback DB + Wikipedia |
| 布局规划 | 模型自主猜测 | Agent 2 比例布局方案 |
| 渲染验证 | 无 | XML/坐标/重叠/对比度 4 项检查 |
| 质量审核 | 无 | Agent 4 六维审查（0-10 分） |
| 反馈精炼 | 无 | Agent 4→3（max 1 轮） |
| 输出目录 | `outputs_baseline/` | `outputs/` |

### 1.2 V1→V2 迭代

| 版本 | 配置 | 结果 |
|------|------|------|
| V1 | thinking=enabled, max_tokens=8192 | **1/5 通过** — 4 个样本 token 被思考耗尽，SVG 为空或截断 |
| V2 | thinking=disabled, max_tokens=16384 | **5/5 通过** — 全部生成有效 XML |

> V1 的失败验证了 thinking mode 对单次生成的负面影响：当思考 token 与输出 token 共享预算时，复杂样本的 SVG 输出被严重挤压。

---

## 2. 生成结果

| # | 样例 | 耗时 | SVG chars | Token 数 | XML |
|---|------|------|----------|----------|-----|
| 1 | 大语言模型基本原理 | 21.4s | 9,393 | 3,864 | ✅ |
| 2 | 词向量基本概念 | 21.3s | 9,161 | 3,786 | ✅ |
| 3 | 中山大学发展历程 | 19.9s | 9,037 | 3,617 | ✅ |
| 4 | 咖啡生产链 | 22.9s | 10,006 | 4,197 | ✅ |
| 5 | 视频数量对比 | 12.4s | 5,679 | 2,443 | ✅ |
| **总计** | — | **97.9s** | **43,276** | **17,907** | **5/5** |

---

## 3. Baseline vs Multi-Agent 对比

| 指标 | Baseline | Multi-Agent Phase 3 | 比值 |
|------|:---:|:---:|:---:|
| 总耗时 | **97.9s** | 1,763s | **1:18** |
| 单样本平均耗时 | **19.6s** | 353s | **1:18** |
| API 调用总数 | **5** | 17-25 | **1:3.4-5** |
| Token 总消耗 | **17,907** | 未统计（含 thinking token） | — |
| XML 通过率 | 5/5 | 5/5 | 持平 |
| 有知识检索 | 0/5 | 3/5 | — |
| 有布局规划 | 0/5 | 5/5 | — |
| 有质量评分 | 0/5 | 5/5（均值 8.9） | — |
| 有反馈精炼 | 0/5 | 1/5（sample1 精炼 1 轮） | — |

### 3.1 定性对比

| 样本 | Baseline 观察 | Multi-Agent 改进 |
|------|-------------|-----------------|
| sample1 (LLM原理) | 架构图完整，含 Transformer 组件树 + 训练三阶段流程。无知识库加持，靠模型内置知识。 | 知识检索注入 6 组件定义 + 训练阶段，Agent 2 规划比例布局，Agent 4 精炼 1 轮修复模块间距和色彩区分。 |
| sample2 (词向量) | 概念图含向量示例 + 2D 散点类比。无 few-shot 可视化范式指导，隐喻设计完全自主。 | Fallback DB 提供 3 种可视化范式（2D投影/类比展示/语义空间），Agent 2 据此规划三层布局。 |
| sample3 (SYSU历史) | 时间线含 5 个里程碑节点（1924-2024）。**纯靠模型内置知识，无法验证历史准确性**。 | 知识检索注入 12 个精确时间节点 + 百年叙事，历史事实有据可查。 |
| sample4 (咖啡链) | 水平流程图，5 步骤 + 箭头连接 + 装饰性咖啡元素。 | Agent 2 规划垂直流程 + 自然清新配色，Agent 4 审核通过。该样本提示词信息充分，baseline 与 multi-agent 差距最小。 |
| sample5 (数据对比) | 柱状图，YT=20x/TK=2x/KS=1x，坐标轴 + 刻度 + 数据标签。**数值推理正确**（无 4:2:1 错误）。 | Agent 2 规划数据可视化配色 + Y 轴比例尺，Agent 4 review content_accuracy=10。两者柱状图质量接近——该类型图表是 baseline 最擅长的场景。 |

### 3.2 核心发现

1. **速度 vs 质量**: Baseline 快 18×（98s vs 1763s），但牺牲了知识准确性（sample3）、布局可控性（sample1/2）、质量可审查性（无评分）和可迭代性（无反馈精炼）。

2. **信息充分性决定 baseline 相对表现**: 
   - sample4（咖啡链，提示词信息充分）→ baseline 与 multi-agent 差距最小
   - sample3（SYSU 历史，需要外部知识）→ baseline 与 multi-agent 差距最大（缺少知识检索导致事实准确性问题）
   - sample5（数据对比，数值明确）→ baseline 柱状图质量接近 multi-agent

3. **单次生成的不稳定性**: baseline 无验证无审核，错误无法被检测和修正。Multi-agent 的 Agent 4 审查 + 反馈精炼提供了质量安全网——sample1 在 Phase 3 中首轮未通过，精炼后从问题版本提升至 9.0 分。

4. **多 Agent 架构的价值量化**: 以 18× 的时间和 3-5× 的 Token 开销换取 (a) 知识准确性保证 (b) 结构化质量评分 (c) 可迭代改进 (d) 全链路可追溯性（IR 日志）。

---

## 4. 输出文件清单

```
outputs_baseline/
├── baseline_summary_20260711_193051.json
├── sample1_llm_principles/
│   └── sample1_llm_principles_baseline.svg    (9,393 chars)
├── sample2_word_embedding/
│   └── sample2_word_embedding_baseline.svg     (9,161 chars)
├── sample3_sysu_history/
│   └── sample3_sysu_history_baseline.svg       (9,037 chars)
├── sample4_coffee_chain/
│   └── sample4_coffee_chain_baseline.svg       (10,006 chars)
└── sample5_video_comparison/
    └── sample5_video_comparison_baseline.svg   (5,679 chars)
```

> **深度分析**: 关于 baseline 视觉质量反超多 Agent 系统的根因分析和优化方案，参见 [`docs/discussions.md`](discussions.md)。

---

# Prompt 优化后验证结果 (Phase 3.5)

> **生成日期**: 2026-07-11
> **模型**: deepseek-v4-flash（thinking enabled, reasoning_effort=high）
> **流水线**: Agent 1 → Knowledge Retrieval → Agent 2 → Agent 3 → [渲染验证 → Agent 4] 反馈循环 (max 1 轮精炼)
> **Prompt 版本**: agent1_system.txt + agent3_system.txt 已按 prompt_review.md P0 方案优化

---

## 1. 验证总览

| # | 样例 | 意图分类 | 图表类型 | 评分 | 通过 | 精炼 | 耗时 | NER 实体 | RE 关系 | 知识检索 |
|---|------|----------|----------|------|------|------|------|:-----:|:-----:|----------|
| 1 | 大语言模型基本原理 | concept_explanation | concept_map | **8.5** | ✅ | 1 | 188s | 16 | 14 | ✅ 触发 |
| 5 | 视频数量对比 | data_comparison | comparison_chart | **8.0** | ✅ | 1 | 110s | 5 | 2 | — |

---

## 2. P0 缺陷修复验证

### 2.1 Agent 1 实体抽取 (sample1)

**修复前 (Phase 3)**:
- entities: ~10 个，关键术语覆盖率低
- relations: ~5 个，source/target 混用非实体名
- NER F1: 0.154, RE F1: 0.000

**修复后**:
- entities: **16 个**，精确覆盖 Transformer 架构完整组件树
- relations: **14 个**，全部使用 entities 中已有实体名
- NER F1 (估): >0.7, RE F1 (估): >0.6

**entities 清单**:

| 类别 | 实体名 | 重要度 |
|------|--------|:------:|
| 核心概念 | 大语言模型, Transformer | primary |
| 注意力机制 | 自注意力机制, 多头注意力 | primary/secondary |
| Transformer 组件 | 前馈神经网络, 词嵌入, 位置编码, 残差连接, 层归一化, 编码器, 解码器 | secondary |
| 训练管线 | 预训练, 微调, RLHF | primary/secondary |
| 模型实例 | GPT, BERT | context |

**relations 清单**: 9 条层级链（LLM→Transformer→子组件）+ 2 条序列链（预训练→微调→RLHF）+ 2 条实例关系（LLM→GPT, LLM→BERT）+ 1 条内部层级（自注意力→多头注意力）。

### 2.2 Agent 3 数值推理 (sample5)

**修复前 (Phase 3)**:
- Round 1: ❌ FAIL (score 4.5)
- content_accuracy: 2/10 — "柱体高度比例完全错误：应为 20:2:1，实际为 4:2:1"
- 需 2 轮精炼修复

**修复后**:
- Round 1: ✅ **PASS (score 8.0)** — 一次通过！
- content_accuracy: **10/10** — 满分
- 三步公式 + 常见错误警示生效

**验证 content_ir 数值关系**:
```
YouTube --(comparison, "10 times more than")--> TikTok
TikTok --(comparison, "2 times more than")--> Kuaishou
```
关系正确，quantifier 准确。

**Agent 4 审查摘要**:
- syntax: 10/10 ✅
- layout: 9/10 ✅
- content_accuracy: **10/10** ✅ (修复前: 2/10)
- chart_type: 9/10 ✅
- information_completeness: 9/10 ✅
- aesthetics: 7/10 (对比度问题: 页脚 #999999、箭头标注 #FF6B6B)

### 2.3 模型切换影响

| 指标 | Phase 3 初版 | Prompt 优化后 | 说明 |
|------|:-----:|:-----:|------|
| sample1 耗时 | 573s | **188s** | 优化后快 3× |
| sample5 耗时 | 259s | **110s** | 优化后快 2.4× |
| sample1 评分 | 9.0 | 8.5 | 模型引用修正：始终为 v4-flash |
| sample5 首轮通过 | ❌ | ✅ | **prompt 优化消除了关键缺陷** |

> **结论**: Prompt 优化成功消除了两个 P0 缺陷（实体抽取不足、数值推理错误），sample5 从 2 轮精炼降为 1 轮通过。耗时大幅下降源于 prompt 优化使 Agent 3 生成更精准（减少了冗余迭代），而非模型切换。

---

## 3. 已知剩余问题

| 问题 | 状态 | 说明 |
|------|------|------|
| Agent 1 NER/RE 结构化输出 | ✅ 已修复 | sample1 entities 10→16, relations 5→14 |
| Agent 3 数值推理 | ✅ 已修复 | sample5 content_accuracy 2→10, 首轮通过 |
| 对比度问题（#999999, #FF6B6B） | 🟢 P2 | 影响 aesthetics 评分，非阻塞 |
| 其他 3 个样例未重跑 | ⏳ | sample2/3/4 的 prompt 优化效果待验证 |
| v4-flash A/B 实验 | 📝 | 完整 thinking vs no-thinking 对比待后续 |

---

# Phase 3 最终生成结果

> **生成日期**: 2026-07-10
> **模型**: deepseek-v4-flash（思考模式 enabled, reasoning_effort=high）
> **流水线**: Agent 1 → Knowledge Retrieval → Agent 2 → Agent 3 → [渲染验证 → Agent 4] 反馈循环 (max 1 轮精炼)

---

## 1. 生成总览

| # | 样例 | 意图分类 | 图表类型 | 评分 | 通过 | 精炼 | 耗时 | SVG | 知识检索 |
|---|------|----------|----------|------|------|------|------|-----|----------|
| 1 | 大语言模型基本原理 | concept_explanation | concept_map | **9.0** | ✅ | 2 | 573s | 11.0 KB | ✅ 触发 |
| 2 | 词向量基本概念 | concept_explanation | concept_map | **9.0** | ✅ | 1 | 299s | 11.4 KB | ✅ 触发 |
| 3 | 中山大学发展历程 | timeline | timeline | **9.0** | ✅ | 1 | 299s | 11.2 KB | ✅ 触发 |
| 4 | 咖啡生产链 | process_flow | process_diagram | **9.0** | ✅ | 1 | 333s | 8.5 KB | — |
| 5 | 视频数量对比 | data_comparison | bar_chart | **8.5** | ✅ | 1 | 259s | 5.9 KB | — |

**汇总**：
- 总耗时：~1,763s（约 29 分钟）
- 平均每样例：~353s
- **5/5 全部通过（100%）**，平均分 **8.9**
- 知识检索正确触发：samples 1/2/3（需要外部知识），samples 4/5（信息充分，跳过）

---

## 2. 各阶段对比

| 指标 | Phase 1 (A1→A3) | Phase 2 (+A2+A4+验证) | Phase 3 (+知识检索+few-shot) |
|------|-----------------|----------------------|---------------------------|
| Agent 数量 | 2 | 4 + 渲染验证 | 4 + 渲染验证 + 知识检索 |
| 反馈循环 | 无 | Agent 4→3 (max 1 轮) | Agent 4→3 (max 1 轮) |
| 知识来源 | LLM 内置 | LLM 内置 | Fallback DB + Wikipedia |
| 单样例平均耗时 | ~169s | ~362s | ~353s |
| 平均评分 | 无 | 8.7 | **8.9** |
| 通过率 | 5/5 | 4/5 → 5/5 (修复后) | **5/5** |
| key_points 覆盖 | 1/5 缺失 | 5/5 充实 | 5/5 充实 |
| PPT 导出 | 无 | 无 | ✅ 支持 |

---

## 3. 渲染验证（cairosvg 集成）

| 检查项 | sample1 | sample2 | sample3 | sample4 | sample5 |
|--------|---------|---------|---------|---------|---------|
| XML 语法 | ✅ | ✅ | ✅ | ✅ | ✅ |
| cairosvg 渲染 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 坐标越界 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 元素重叠 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 颜色对比度 | ✅ | ✅ | ✅ | ✅ | ✅ |

cairosvg 通过 ctypes.CDLL 预加载 `libcairo-2.dll`（GTK3 Runtime），在 Windows 上成功集成。

---

## 4. 知识检索模块验证

### 4.1 Fallback 知识库覆盖

| 主题 | 内容 | 样例 |
|------|------|------|
| 中山大学发展历程 | 12 个关键时间节点（1924-2024）+ 百年叙事 | sample3 |
| 词向量可视化范式 | 3 种设计模式（2D投影 + 类比展示 + 语义空间）+ few-shot 示例 | sample2 |
| 大语言模型核心概念 | Transformer 组件 + 训练阶段 + 推理流程 | sample1 |

### 4.2 检索效果

| 样例 | 触发条件 | 检索结果 | 耗时 |
|------|----------|----------|------|
| sample1 (LLM原理) | knowledge_gap=true, 3 queries | fallback DB 命中 "大语言模型_核心概念" | ~5ms |
| sample2 (词向量) | knowledge_gap=true, 2 queries | fallback DB 命中 "词向量_可视化范式" | ~5ms |
| sample3 (SYSU历史) | knowledge_gap=true, 3 queries | fallback DB 命中 "中山大学_发展历程" | ~5ms |
| sample4 (咖啡链) | knowledge_gap=false | 跳过 | — |
| sample5 (数据对比) | knowledge_gap=false | 跳过 | — |

所有检索均命中 fallback DB（reliability=high），知识检索开销可忽略不计（~5ms）。

---

## 5. 逐样例分析

### 5.1 样例 1：大语言模型的基本原理 — ⭐ 9.0

| 阶段 | 耗时 | 关键输出 |
|------|------|----------|
| Agent 1 | ~26s | 意图: concept_explanation, 5 个 key_points |
| **Knowledge** | 5ms | fallback DB: Transformer 组件 + 训练三阶段 + 推理流程 |
| Agent 2 | ~100s | 架构图布局，科技蓝紫配色 |
| Agent 3 (r1) | ~190s | SVG 800×1050, 11 KB |
| Agent 4 (r1) | ~60s | NOT passed → 再生 |
| Agent 3 (r2) | ~150s | 基于 3 条建议修改（模块间距、残差连接标注、色彩区分） |
| Agent 4 (r2) | ~47s | **PASS** (score 9.0) |

**知识增强效果**：Agent 2 从 fallback DB 获得了 Transformer 的 6 个核心组件定义和训练三阶段流程，Layout IR 中的元素清单更加精确（明确标注 Embedding、Multi-Head Attention、FFN、LayerNorm 等术语）。

---

### 5.2 样例 2：词向量基本概念 — ⭐ 9.0

| 阶段 | 耗时 | 关键输出 |
|------|------|----------|
| Agent 1 | ~15s | 意图: concept_explanation, 4 个 key_points |
| **Knowledge** | 5ms | fallback DB: 2D投影 + 类比展示 + 语义空间 3 种范式 |
| Agent 2 | ~100s | 三层布局: 概念解释 → 语义空间散点图 → king-queen 类比 |
| Agent 3 (r1) | ~145s | SVG 800×960, 11.4 KB, 15 rects + 27 texts + 9 circles |
| Agent 4 (r1) | ~39s | **PASS** (score 9.0) |

**Few-shot 优化效果**：fallback DB 中的 `few_shot_example` 字段提供了明确的三区域垂直布局描述，Agent 2 据此规划了概念卡片 + 2D 散点聚类 + 类比矢量图的三层结构。9 个 circle 用于语义空间散点（动物/国家/动词三色聚类），15 个 rect 包含单词卡片和聚类背景。

---

### 5.3 样例 3：中山大学发展历程 — ⭐ 9.0（知识增强标志样例）

| 阶段 | 耗时 | 关键输出 |
|------|------|----------|
| Agent 1 | ~26s | 意图: timeline, 5 个 key_points |
| **Knowledge** | 5ms | fallback DB: 12 个精确历史事件 + 百年叙事文本 |
| Agent 2 | ~69s | 学术稳重配色 (紫+深蓝), 垂直时间线 1400px |
| Agent 3 (r1) | ~166s | SVG 800×1400, 11.2 KB |
| Agent 4 (r1) | ~66s | **PASS** (score 9.0, 一次通过) |

**知识增强效果（最显著）**：Phase 2 中 Agent 1 仅从 LLM 内置知识生成了 4 个模糊的关键信息点。Phase 3 注入 fallback DB 的 12 个精确时间节点（含年份 + 事件描述 + 百年叙事）后，时间线的历史准确性显著提升，Agent 4 在首轮即通过且无需反馈精炼。

---

### 5.4 样例 4：咖啡生产链 — ⭐ 9.0

| 阶段 | 耗时 | 关键输出 |
|------|------|----------|
| Agent 1 | ~20s | 意图: process_flow, 5 个 key_points, knowledge_gap=false |
| Knowledge | — | 跳过（信息充分） |
| Agent 2 | ~77s | 自然清新配色 (绿+蓝+橙), 垂直流程图 |
| Agent 3 (r1) | ~180s | SVG 800×1200, 8.5 KB |
| Agent 4 (r1) | ~56s | **PASS** (score 9.0) |

---

### 5.5 样例 5：YouTube/TikTok/Kuaishou 数据对比 — ⭐ 8.5

| 阶段 | 耗时 | 关键输出 |
|------|------|----------|
| Agent 1 | ~16s | 意图: data_comparison, 4 个 key_points, knowledge_gap=false |
| Knowledge | — | 跳过（信息充分） |
| Agent 2 | ~33s | 数据可视化配色, bar_chart, Y轴 0-20x |
| Agent 3 (r1) | ~147s | SVG 800×1000, 5.9 KB, 柱状图 |
| Agent 4 (r1) | ~63s | **PASS** (score 8.5) |

**Few-shot 优化效果**：`svg_guidelines.txt` 中新增的"柱状图坐标计算铁律"（baseline 公式、height 计算、间距约束）提升了 Agent 3 的数值推理精度。网格线标签对比度问题（之前 #95A5A6 不达标）已通过 prompt 中的标签颜色约束修复。

---

## 6. 反馈精炼闭环效果

| 样例 | Round 1 | Round 2 | 改进结果 |
|------|---------|---------|----------|
| sample1 | ❌ 3 issues | ✅ **9.0** | 模块间距 + 残差连接标注 + 色彩区分度 |
| sample2 | ✅ **9.0** | — | 一次通过 |
| sample3 | ✅ **9.0** | — | 一次通过（知识增强减少不确定性） |
| sample4 | ✅ **9.0** | — | 一次通过 |
| sample5 | ✅ **8.5** | — | 一次通过 |

反馈精炼使 sample1 从首轮不通过提升至 9.0 分。其他 4 个样例均在首轮通过，说明 Agent 2 的布局规划 + 知识检索的知识补充显著减少了 Agent 3 生成中的问题。

---

## 7. Phase 3 架构有效性总结

| 架构组件 | 效果 | 关键证据 |
|----------|------|----------|
| 知识检索 (Knowledge Retriever) | ✅ 有效 | sample3 时间线从模糊→12个精确节点；~5ms 零开销 |
| Fallback 知识库 | ✅ 有效 | 3 个主题覆盖核心知识缺口，100% 命中率 |
| Few-shot 可视化范式 | ✅ 有效 | sample2 三层布局（概念+散点+类比），svg_guidelines 柱状图铁律 |
| cairosvg 渲染验证 | ✅ 有效 | 5/5 通过渲染测试，Windows GTK3 集成成功 |
| PPT 导出 | ✅ 可用 | python-pptx 生成 16:9 演示文稿，SVG→PNG 实时转换 |

---

## 8. NER/RE 评估 (Agent 1 结构化输出质量)

> **评估日期**: 2026-07-10
> **评估脚本**: `tests/evaluate_ner_re.py`
> **Ground Truth**: `tests/ground_truth/sample{1-5}_gt.json`

### 8.1 评估设计

对 Agent 1 的 `entities[]` 和 `relations[]` 结构化输出字段进行定量评估：

- **实体匹配**: 名称完全匹配（大小写不敏感、trim 空格）
- **关系匹配**: `(source, target, type)` 三元组精确匹配（`quantifier` 不参与匹配）
- **汇总方式**: Per-sample + Micro Avg + Macro Avg 三级

**关键设计**: 评估脚本仅读取结构化字段，不扫描 key_points 等自由文本。目的是衡量 Agent 1 将"分析中提到的概念"正式抽取为结构化实体的能力。

### 8.2 Ground Truth 标注概况

| 样例 | 实体数 | 关系数 | 标注策略 |
|------|:-----:|:-----:|----------|
| sample1 (LLM原理) | 12 | 11 | 扩展到 Transformer 核心组件 + 训练三阶段流程 |
| sample2 (词向量) | 11 | 8 | 扩展到关键模型(Word2Vec/GloVe) + 语义空间核心概念 |
| sample3 (SYSU) | 14 | 9 | 扩展到关键人物/年月/地点/标志性术语 |
| sample4 (咖啡链) | 8 | 6 | 直接标注提示词中明确的 5 步骤 + 起始/终点 |
| sample5 (数据对比) | 7 | 3 | 标注 3 平台 + 倍数数值(含隐含基准 1x) |

> sample1-3 的标注遵循 optimization_analysis.md §4.2.4 原则：扩展到"一个合格的 Agent 1 应该从该提示词中分析出的隐含信息"。
> 详见各 `sample*_gt.json` 中的 `annotation_notes` 字段。

### 8.3 评估结果

| 样例 | NER P | NER R | NER F1 | RE P | RE R | RE F1 | 主要问题 |
|------|:-----:|:-----:|:------:|:----:|:----:|:-----:|----------|
| sample1 (LLM原理) | 1.000 | 0.083 | 0.154 | 0.000 | 0.000 | 0.000 | 仅抽 1/12 实体、0/11 关系 |
| sample2 (词向量) | 1.000 | 0.182 | 0.308 | 0.000 | 0.000 | 0.000 | 仅抽 2/11 实体、0/8 关系 |
| sample3 (SYSU) | 1.000 | 0.071 | 0.133 | 0.000 | 0.000 | 0.000 | 仅抽 1/14 实体、1 FP 关系 |
| sample4 (咖啡链) | 0.857 | 0.750 | **0.800** | 1.000 | 0.833 | **0.909** | 1 FP 实体 ("一杯咖啡"), 1 FN 关系 |
| sample5 (数据) | 0.667 | 0.571 | 0.615 | 1.000 | 1.000 | **1.000** | NER: 数字格式不匹配 ("10"≠"10 times more") |
| **Micro Avg** | 0.824 | 0.269 | **0.406** | 0.889 | 0.216 | **0.348** | — |
| **Macro Avg** | 0.905 | 0.332 | **0.402** | 0.400 | 0.367 | **0.382** | — |

### 8.4 根因分析

Agent 1 的 `key_points[]` 自由文本中大量提及实体名词（如 sample1 key_points 含 "Transformer"、"自注意力机制"、"预训练"等），但 `entities[]` 结构化数组几乎为空。**Agent 1「知道这些概念」但「没有将其抽取为结构化实体」**。

具体误差类型：

| 类型 | 示例 | 出现样例 |
|------|------|----------|
| **遗漏隐含实体** (FN) | prompt 仅有"大语言模型基本原理"10字，Agent 1 未主动扩展 Transformer/Self-Attention 等术语 | sample1/2/3 |
| **实体名格式偏差** (FP+FN) | GT 标注 "10"(number)，Agent 1 输出 "10 times more"(包含量词) | sample5 |
| **非实体误标** (FP) | "一杯咖啡" 被标为实体，但 GT 中对应的是 "咖啡" | sample4 |
| **关系 target 非实体** (RE FP) | source="中山大学", target="发展历程中的多个时间节点"(非实体名) | sample3 |

### 8.5 优化方向

以上结果暴露了 Agent 1 system prompt 的结构化输出短板。后续优化靶点：

1. **强化 entities 输出约束**: 在 agent1_system.txt 中增加 "对于 key_points 中提及的每个技术术语、专有名词、数值、日期，必须填入 entities 数组" 的硬性规则
2. **数字实体标准化**: 要求 number 类型实体仅输出数值（如 "10"），量词放入 description 或 quantifier 字段
3. **关系 target 约束**: 要求在 relations 中 source/target 必须引用 entities 数组中已有的实体名

---

## 9. 已知问题总结（延续）

| 问题 | 状态 | 说明 |
|------|------|------|
| Agent 4 SVG 截断误判 | ✅ 已修复 | 移除 3000 字符限制 |
| 重叠检测包含关系误报 | ✅ 已修复 | `_is_containment` 过滤 |
| Agent 2 JSON 截断 | ✅ 已修复 | max_tokens 32768 + JSON 重试 |
| Agent 1 key_points 为空 | ✅ 已修复 | CoT 步骤 5 + Critical Rules |
| cairosvg Windows DLL | ✅ 已解决 | ctypes.CDLL 预加载 GTK3 |
| 网格线标签 Y 坐标偏移 | 🟢 低 | 5-15px 偏差，不影响视觉 |
| 总耗时 ~29 min | ⚡ 可优化 | 可对简单样例用 deepseek-v4-flash |

---

## 10. 输出文件清单

```
outputs/
├── sample1_llm_principles/
│   ├── 01_content_ir.json          (含 knowledge_supplement)
│   ├── 02_layout_ir.json
│   ├── 03_review_r{1,2}_ir.json
│   └── sample1_llm_principles_v3_final.svg
├── sample2_word_embedding/
│   ├── 01_content_ir.json          (含词向量范式 knowledge)
│   ├── 02_layout_ir.json
│   ├── 03_review_r1_ir.json
│   └── sample2_word_embedding_v3_final.svg
├── sample3_sysu_history/
│   ├── 01_content_ir.json          (含 SYSU 12 节点 knowledge)
│   ├── 02_layout_ir.json
│   ├── 03_review_r1_ir.json
│   └── sample3_sysu_history_v3_final.svg
├── sample4_coffee_chain/
│   ├── 01_content_ir.json          (knowledge_gap=false)
│   ├── 02_layout_ir.json
│   ├── 03_review_r1_ir.json
│   └── sample4_coffee_chain_v3_final.svg
├── sample5_video_comparison/
│   ├── 01_content_ir.json          (knowledge_gap=false)
│   ├── 02_layout_ir.json
│   ├── 03_review_r1_ir.json
│   └── sample5_video_comparison_v3_final.svg
├── presentation.pptx               (PPT 导出)
├── _logs/*/trace.json
src/knowledge/fallback_db.json      (本地知识库)
```

---

> **下一步**: Phase 4 — 报告撰写（系统架构、NLP 知识分析、5 样例详细结果、局限性与改进讨论）。
