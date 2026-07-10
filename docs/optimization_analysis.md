# 后续优化方向分析

> **日期**: 2026-07-10
> **基于**: 当前 Phase 3 实施状态 + implementation_plan.md + changelog.md

---

## 目录

1. [方向一：主模型切换为 deepseek-v4-flash](#1-方向一主模型切换为-deepseek-v4-flash)
2. [方向二：MAX_REFINEMENT_ROUNDS 消融实验](#2-方向二max_refinement_rounds-消融实验)
3. [方向三：PPT 导出（已确认跳过）](#3-方向三ppt-导出已确认跳过)
4. [方向四：NER/RE 指标的人工标注与计算方法](#4-方向四nerre-指标的人工标注与计算方法)
5. [方向五：Prompt 针对性优化指南](#5-方向五prompt-针对性优化指南)
6. [方向六：引入图标库（iconfont.cn）的可行性分析](#6-方向六引入图标库iconfontcn-的可行性分析)

---

## 1. 方向一：主模型切换为 deepseek-v4-flash

### 1.1 现状

| 指标 | deepseek-v4-pro（当前） | 说明 |
|------|--------------------------|------|
| 单样例平均耗时 | ~350s（~6 分钟） | 主要瓶颈在 Agent 3（80-200s） |
| 5 样例总耗时 | ~1,750s（~29 分钟） | 思考模式贡献了大量延迟 |
| 平均评分 | 8.7/10 | 5/5 全部通过 |
| 思考模式 | enabled + reasoning_effort=high | 质量提升但 Agent 3 延迟增至 5.8x |

### 1.2 deepseek-v4-flash 的预期表现

| 维度 | v4-pro（当前） | v4-flash（切换后） | 预期变化 |
|------|:---:|:---:|------|
| **API 延迟** | 慢（深度推理） | 快（轻量推理） | Agent 3 预计从 120s → 30-40s |
| **代码生成质量** | 高 | 中高 | SVG XML 可能更易出现语法瑕疵 |
| **复杂推理** | 强（CoT 充分） | 中（CoT 受限） | 布局规划、图表类型判断可能变弱 |
| **中文理解** | 强 | 中强 | NER/RE 质量可能轻微下降 |
| **思考模式效果** | 显著提升 | 提升有限 | flash 模型的思考 token 预算通常更少 |
| **成本** | 高 | 低 | 大幅降低 Token 费用 |

### 1.3 合理性评估：✅ 合理，但建议做 A/B 对比

**论据支持切换**：

1. **时间约束是真实瓶颈**。29 分钟跑 5 个样例在开发迭代中确实偏慢。如果需要进行多轮 prompt 调试，这个延迟会严重拖慢迭代速度。
2. **当前 5 样例已全部通过（8.7 分）**，说明 v4-pro 的深度推理在当前任务上可能"过剩"——问题复杂度尚未触及 flash 的能力上限。
3. **Agent 4 + 渲染验证提供了安全网**。即使 flash 生成的 SVG 质量略降，语法错误会被 validator 捕获，内容问题会被 Agent 4 识别，反馈循环可以修复大部分问题。

**论据反对完全切换**：

1. **sample 2（词向量）和 sample 1（LLM 原理）是高风险样例**。这两个需要深层的概念理解和复杂的空间布局设计，flash 模型可能力不从心。
2. **思考模式在 flash 上的效果未知**。v4-pro + thinking 的 5.8x 延迟增加换来了显著的质量提升；但 flash 的 thinking token 预算通常更少，边际收益可能更低。
3. **MER/RE 质量下降会影响报告中的 NLP 指标**。如果切换到 flash 导致意图分类错误或实体遗漏，NLP 评估数据会变差。

### 1.4 推荐方案：混合策略 + A/B 对比实验

```
┌─────────────────────────────────────────────────────────┐
│  推荐方案：v4-flash 为主 + v4-pro 兜底                    │
│                                                         │
│  Agent 1 (分析): v4-flash（分析任务推理深度需求适中）      │
│  Agent 2 (布局): v4-flash（布局规划结构化程度高）          │
│  Agent 3 (编码): v4-flash → 如果失败则切 v4-pro 重试      │
│  Agent 4 (审查): v4-flash（审查有结构化报告辅助）          │
│                                                         │
│  兜底逻辑：                                              │
│  if Agent 3 生成的 SVG XML 验证失败:                      │
│      自动切换到 v4-pro 重新生成                            │
│  if Agent 4 评分为 fail 且 needs_regeneration:            │
│      精炼轮使用 v4-pro（关键修复用更强的模型）              │
└─────────────────────────────────────────────────────────┘
```

**建议的 A/B 实验设计**：

| 实验组 | 模型 | 样例 | 测量指标 |
|--------|------|------|----------|
| A（对照组） | v4-pro + thinking | 全部 5 个 | 评分、耗时、XML 通过率、NER 准确数 |
| B（实验组） | v4-flash + thinking | 全部 5 个 | 同上 |
| C（混合组） | flash + pro 兜底 | 全部 5 个 | 同上 + 兜底触发率 |

**实验执行方式**：

```bash
# 通过环境变量切换模型，保持其他条件不变
DEEPSEEK_MODEL=deepseek-v4-flash python main.py --sample sample1
DEEPSEEK_MODEL=deepseek-v4-pro python main.py --sample sample1
```

预计耗时：v4-pro 组 ~30 分钟，v4-flash 组 ~8-10 分钟，混合组 ~10-15 分钟。一小时内可完成。

### 1.5 结论

**建议采纳，但不要一刀切**。将默认模型改为 v4-flash，在 `.env` 中配置，并增加 v4-pro 作为失败时的 fallback。同时运行一次完整的 A/B 对比实验，将结果写入报告——这本身就是很好的"工程决策分析"素材。

---

## 2. 方向二：MAX_REFINEMENT_ROUNDS 消融实验

### 2.1 消融实验设计

**自变量**：`MAX_REFINEMENT_ROUNDS` ∈ {0, 1, 2}

- **0 轮**：Agent 3 生成 → 渲染验证 → Agent 4 审查（仅评分，不反馈修改）→ 直接输出
- **1 轮**（当前）：Agent 3 → 验证 → Agent 4 → 如不通过则 Agent 3 修改 1 次 → 输出
- **2 轮**：Agent 3 → 验证 → Agent 4 → 不通过改 1 次 → Agent 4 再审 → 不通过再改 1 次 → 输出

**因变量**：

| 指标 | 测量方法 |
|------|----------|
| 最终评分 | Agent 4 `overall_score` |
| 通过率 | Agent 4 `pass` |
| 各维度评分 | `dimensions.*.score`（重点关注 layout, content_accuracy, aesthetics） |
| 总耗时 | `total_duration_s` |
| Token 消耗 | 需在 base_agent.py 中添加 token 计数 |
| 语法正确性 | validator `xml_valid` |

**控制变量**：固定模型（v4-flash 或 v4-pro）、固定 prompt、固定 5 个样例。

### 2.2 实验矩阵

| 实验 ID | MAX_REFINEMENT_ROUNDS | 样例 | 预期 |
|---------|----------------------|------|------|
| R0 | 0 | 全部 5 个 | 最快，评分最低。作为 baseline |
| R1 | 1 | 全部 5 个 | 当前配置，已有数据可复用 |
| R2 | 2 | 全部 5 个 | 最慢，评分可能最高，但需验证边际收益 |

### 2.3 预期结果与假设

基于当前运行数据推断：

| 样例 | R0 预期评分 | R1 实际评分 | R2 预期评分 | 精炼边际收益 |
|------|:---------:|:---------:|:---------:|:----------:|
| sample1 (LLM原理) | ~7.0 | 8.0 | ~8.5 | R0→R1: +1.0, R1→R2: +0.5 |
| sample2 (词向量) | ~7.0 | 8.5 | ~9.0 | R0→R1: +1.5, R1→R2: +0.5 |
| sample3 (SYSU历史) | ~7.5 | 9.2 | ~9.2 | R0→R1: +1.7, R1→R2: ~0 |
| sample4 (咖啡链) | ~7.5 | 8.8 | ~9.0 | R0→R1: +1.3, R1→R2: +0.2 |
| sample5 (数据对比) | ~7.5 | 9.0 | ~9.0 | R0→R1: +1.5, R1→R2: ~0 |

**核心假设**：第 1 轮精炼的边际收益最大（修复明显问题），第 2 轮收益递减（仅能微调细节）。但对于本身就在 R1 通过的样例（sample1/2/5），R2 可能完全无额外收益。

### 2.4 实施方式

在 `orchestrator.py` 中将 `MAX_REFINEMENT_ROUNDS` 改为可通过参数控制：

```python
# orchestrator.py 修改方案
class Pipeline:
    def __init__(self, model: str | None = None, max_refinement_rounds: int = 1):
        self.max_refinement_rounds = max_refinement_rounds
        ...

# main.py 增加 CLI 参数
parser.add_argument("--max-rounds", type=int, default=1,
                    help="Max refinement rounds (0-2)")
```

```bash
# 执行消融实验
python main.py --sample sample4 --max-rounds 0
python main.py --sample sample4 --max-rounds 1
python main.py --sample sample4 --max-rounds 2
```

### 2.5 结论

**强烈建议做**。消融实验是报告中非常有说服力的内容：
- 展示了对系统行为的深入理解
- 量化了反馈循环的边际收益
- 为"为什么选择 1 轮"提供了数据支撑（而非仅凭工程直觉）
- 符合 NLP 研究的实验方法论

建议在报告中以图表形式呈现（折线图：x=精炼轮数, y=评分，每条线一个样例）。

---

## 3. 方向三：PPT 导出（已确认跳过）

已确认。PPT 导出功能（`src/knowledge/ppt_exporter.py`、`main.py --ppt`）在后续优化中不再维护或改进。当前实现可作为可选功能保留，但报告中的结果展示应优先使用 SVG 截图/嵌入。

---

## 4. 方向四：NER/RE 指标的人工标注与计算方法

### 4.1 为什么要做

报告的 NLP 知识运用分析（implementation_plan §10）需要有**定量数据**支撑，而非仅定性描述。NER 和 RE 是 Agent 1 的核心 NLP 能力，其准确率直接体现系统的语义理解水平。

### 4.2 标注方案

#### 4.2.1 标注范围

对 5 个必选样例的提示词，分别标注 ground truth：

```
样例提示词 → 人工标注的实体列表 (ground truth) → Agent 1 输出的实体列表 (prediction) → 对比
```

#### 4.2.2 实体标注规范

**实体类型定义**（与 Agent 1 prompt 保持一致）：

| 类型 | 说明 | 示例 |
|------|------|------|
| `person` | 人物名称 | 孙中山 |
| `organization` | 组织/机构 | 中山大学、YouTube |
| `location` | 地点 | 珠海、深圳 |
| `term` | 专业术语/概念 | Transformer、词向量、Self-Attention |
| `number` | 数值 | 10、2（含倍数关系中隐含的数值） |
| `date` | 日期/时间 | 1924年、2017年 |

**标注原则**：

1. **最小实体原则**：标注最小的有意义单元。例如"大语言模型"标注为一个 `term`，而非拆分为"大"+"语言"+"模型"。
2. **上下文敏感**：同一个词在不同提示词中可能属于不同类型。例如"中山大学"在 sample3 中是 `organization`（历史叙述的主体），如果在其他上下文中可能只是 `location` 修饰语。
3. **隐含实体也要标注**：sample5 提示词中的倍数关系隐含了"Kuaishou = 1x"这个基准值，应将这个隐含的 `number` 实体也标注。
4. **不标注停用词**：如"的"、"是"、"了"、"绘制"等功能词不作为实体。

#### 4.2.3 关系标注规范

**关系类型定义**（与 Agent 1 prompt 保持一致）：

| 类型 | 说明 | 示例 |
|------|------|------|
| `comparison` | 对比关系 | YouTube 比 TikTok 多 10 倍 |
| `hierarchy` | 层级/包含关系 | Transformer 包含 Self-Attention |
| `sequence` | 序列/流程关系 | 种植→采摘→烘焙→研磨→冲煮 |
| `causality` | 因果关系 | （当前 5 样例中较少出现） |
| `temporal` | 时序关系 | 1924年建校 先于 2001年合并 |

**标注原则**：

1. 关系标注的是**实体对之间的关系**，每个关系需要有明确的 `(source, target, type)` 三元组。
2. 如果提示词中明确表达了关系，则标注。如果仅是暗示，可标注但标注 `confidence: implicit`。
3. 数值关系必须标注 `quantifier`。

#### 4.2.4 标注模板

为每个样例创建一个标注文件（JSON 格式），例如 `tests/ground_truth/sample1_gt.json`：

```json
{
  "sample_id": "sample1",
  "prompt": "绘制白色背景的SVG信息图解释大语言模型的基本原理",
  "ground_truth_entities": [
    {"name": "大语言模型", "type": "term", "role": "subject", "importance": "primary"},
    {"name": "Transformer", "type": "term", "role": "subject", "importance": "primary"},
    {"name": "Self-Attention", "type": "term", "role": "subject", "importance": "secondary"},
    {"name": "前馈神经网络", "type": "term", "role": "subject", "importance": "secondary"},
    {"name": "词嵌入", "type": "term", "role": "subject", "importance": "secondary"},
    {"name": "残差连接", "type": "term", "role": "subject", "importance": "secondary"},
    {"name": "层归一化", "type": "term", "role": "subject", "importance": "secondary"},
    {"name": "预训练", "type": "term", "role": "attribute", "importance": "secondary"},
    {"name": "微调", "type": "term", "role": "attribute", "importance": "secondary"},
    {"name": "RLHF", "type": "term", "role": "attribute", "importance": "secondary"}
  ],
  "ground_truth_relations": [
    {"type": "hierarchy", "source": "大语言模型", "target": "Transformer", "quantifier": null},
    {"type": "hierarchy", "source": "Transformer", "target": "Self-Attention", "quantifier": null},
    {"type": "hierarchy", "source": "Transformer", "target": "前馈神经网络", "quantifier": null},
    {"type": "hierarchy", "source": "Transformer", "target": "词嵌入", "quantifier": null},
    {"type": "hierarchy", "source": "Transformer", "target": "残差连接", "quantifier": null},
    {"type": "hierarchy", "source": "Transformer", "target": "层归一化", "quantifier": null},
    {"type": "sequence", "source": "预训练", "target": "微调", "quantifier": null},
    {"type": "sequence", "source": "微调", "target": "RLHF", "quantifier": null}
  ]
}
```

> **注意**：sample1 的提示词只有"大语言模型的基本原理"10 个字。Agent 1 实际抽取的实体会远超提示词字面内容（因为它会基于 LLM 的知识补充相关术语）。因此 ground truth 的标注也应该**扩展到提示词隐含的信息范围**——即"一个合格的 Agent 1 应该从这条提示词中分析出什么"。这个范围的界定需要标注者自行判断，可以遵循"如果我是 Agent 1，基于 NLP 常识我应该抽取哪些实体"的标准。

#### 4.2.5 标注注意事项

1. **标注前先不要让 Agent 1 跑结果**——避免预测结果影响标注判断（锚定偏差）。
2. **一人标注、一人审核**——如果条件允许，两人独立标注后计算 IAA（标注者间一致率）。
3. **标注完成后 freeze**——不要在看过预测结果后修改 ground truth（这会使评估失去意义）。
4. **承认模糊性**——对于有歧义的实体，在标注中备注 `"note": "此实体可能存在歧义，因..."`。

### 4.3 评估计算方法

#### 4.3.1 实体级评估（Entity-level）

```python
def evaluate_ner(predicted: list[dict], ground_truth: list[dict]) -> dict:
    """
    计算 NER 的精确率、召回率、F1。
    
    匹配规则：实体 name 完全匹配（忽略大小写和首尾空格）
    """
    pred_names = set(e["name"].strip().lower() for e in predicted)
    gt_names = set(e["name"].strip().lower() for e in ground_truth)
    
    tp = len(pred_names & gt_names)  # 正确抽取的实体
    fp = len(pred_names - gt_names)  # 多抽的实体（幻觉）
    fn = len(gt_names - pred_names)  # 漏抽的实体
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "tp": list(pred_names & gt_names),
        "fp": list(pred_names - gt_names),
        "fn": list(gt_names - pred_names),
    }
```

#### 4.3.2 关系级评估（Relation-level）

关系评估比实体评估更复杂，因为同一个三元组可能有不同表述。匹配规则：

```python
def evaluate_re(predicted: list[dict], ground_truth: list[dict]) -> dict:
    """
    计算 RE 的精确率、召回率、F1。
    
    匹配规则：三元组 (source, target, type) 完全匹配
    source/target 使用实体名匹配（允许小范围别名，如 "LLM" ↔ "大语言模型"）
    """
    # 先将三元组标准化
    def normalize(rel: dict) -> tuple:
        return (
            rel["source"].strip().lower(),
            rel["target"].strip().lower(),
            rel["type"].strip().lower()
        )
    
    pred_triples = set(normalize(r) for r in predicted)
    gt_triples = set(normalize(r) for r in ground_truth)
    
    tp = len(pred_triples & gt_triples)
    fp = len(pred_triples - gt_triples)
    fn = len(gt_triples - pred_triples)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "tp": list(pred_triples & gt_triples),
        "fp": list(pred_triples - gt_triples),
        "fn": list(gt_triples - pred_triples),
    }
```

#### 4.3.3 汇总方法

| 汇总方式 | 计算方法 | 适用场景 |
|----------|----------|----------|
| **Micro-average** | 将所有样例的 TP/FP/FN 累加后统一计算 | 关注整体表现 |
| **Macro-average** | 每个样例单独计算指标后取平均 | 关注每个样例同等重要 |
| **Per-sample** | 逐样例报告指标 | 分析哪个样例是短板 |

对于 5 个样例的课程设计，建议**三种都报告**——Per-sample 用于逐样例分析，Micro 和 Macro 用于系统整体评估。

### 4.4 实施步骤

```
Step 1: 创建 tests/ground_truth/ 目录
Step 2: 对 5 个样例分别创建 sample{1-5}_gt.json 标注文件
Step 3: 实现评估脚本 tests/evaluate_ner_re.py
Step 4: 遍历 outputs/*/01_content_ir.json，读取 Agent 1 的实际输出
Step 5: 与 ground truth 对比，计算每个样例的指标
Step 6: 汇总为一张结果表（见下方模板）
Step 7: 对误检/漏检案例做错误分析（FP 和 FN 各选 2-3 个典型案例）
```

### 4.5 结果展示模板

| 样例 | NER P | NER R | NER F1 | RE P | RE R | RE F1 | 主要 FP 类型 | 主要 FN 类型 |
|------|:-----:|:-----:|:------:|:----:|:----:|:-----:|-------------|-------------|
| sample1 (LLM原理) | 0.xx | 0.xx | 0.xx | 0.xx | 0.xx | 0.xx | 术语泛化 | 遗漏隐含概念 |
| sample2 (词向量) | ... | ... | ... | ... | ... | ... | ... | ... |
| sample3 (SYSU) | ... | ... | ... | ... | ... | ... | ... | ... |
| sample4 (咖啡链) | ... | ... | ... | ... | ... | ... | ... | ... |
| sample5 (数据对比) | ... | ... | ... | ... | ... | ... | ... | ... |
| **Micro Avg** | 0.xx | 0.xx | 0.xx | 0.xx | 0.xx | 0.xx | — | — |
| **Macro Avg** | 0.xx | 0.xx | 0.xx | 0.xx | 0.xx | 0.xx | — | — |

### 4.6 结论

**强烈建议执行**。这是课程设计中"NLP 知识深度"最直接的量化证据。标注工作量可控——5 个样例，每个 10-20 个实体 + 5-10 个关系，总标注时间约 2-3 小时。相比其在报告中产生的说服力，投入产出比很高。

---

## 5. 方向五：Prompt 针对性优化指南

### 5.1 Prompt 文件清单与作用

| 文件 | 作用于 | 控制内容 | 优化空间 |
|------|--------|----------|----------|
| `src/prompts/agent1_system.txt` | Agent 1（内容分析器） | NER/RE/意图分类/知识缺口检测/图表推荐 | 🔴 高 |
| `src/prompts/agent2_system.txt` | Agent 2（布局规划器） | 空间分区/配色方案/排版/元素定义/连接关系 | 🟡 中 |
| `src/prompts/agent3_system.txt` | Agent 3（SVG 生成器） | SVG 编码规范/图表类型策略/美观原则/文本凝练 | 🔴 高 |
| `src/prompts/agent4_system.txt` | Agent 4（质量审核器） | 6 维审查标准/判定规则/修改建议格式 | 🟡 中 |
| `src/prompts/svg_guidelines.txt` | Agent 3（设计规范） | 配色方案/排版规范/设计模式代码片段/柱状图坐标规则 | 🔴 高 |

### 5.2 各 Agent 的优化切入点

#### Agent 1（agent1_system.txt）—— 提升分析质量

**当前问题**：
- sample1 中 Agent 1 将分类输出为 `concept_explanation` 而非更具体的 `architecture_diagram`（implementation_plan 预期的是后者）。虽然不是错误，但可能影响下游的布局策略选择。

**优化方向**：

```diff
  ### 步骤 1：意图分类（Intent Classification）
+ 
+ 特别规则：
+ - 如果提示词涉及"技术原理""架构""结构"且主题为技术系统（如LLM、Transformer、
+   神经网络），应优先考虑 architecture_diagram 而非 concept_explanation
+ - 如果提示词同时符合多个类型，在 primary_type 中选择最具体的（architecture >
+   concept > process > timeline > comparison）
+ - secondary_type 填写次优类型，帮助下游 Agent 做灵活判断
```

**优化方向**（知识缺口检测）：

```diff
  ### 步骤 4：信息完整性评估
+ 
+ 判断标准细化：
+ - 提示词仅给出主题但未提供具体内容 → needs_external_knowledge = true
+   （如"中山大学发展历程"——主题明确但历史事实需检索）
+ - 提示词既给出主题又给出结构化内容 → needs_external_knowledge = false
+   （如"种植→采摘→烘焙→研磨→冲煮"——所有步骤已明确列出）
+ - 提示词要求解释某个概念 → 如果该概念在你的训练数据中有充分覆盖，
+   needs_external_knowledge = false，在 fallback_knowledge 中预填你确认的知识
```

#### Agent 3（agent3_system.txt）—— 提升 SVG 生成质量

**当前问题**：
- sample4（咖啡链）评分 8.8，美学维度仅 8/10——存在"设计平庸"风险
- 缺少对"装饰性元素"的具体指导和分寸感

**优化方向**：

```diff
  ## 特殊场景处理
  
+ ### 流程图/过程链的增强设计
+ - 为每个步骤节点添加简约图标（使用基本几何图形组合）
+   种植 → 叶子/幼苗图标（椭圆+弧线）
+   采摘 → 手/篮子图标（圆+梯形）
+   烘焙 → 火焰/热浪图标（三角形堆叠）
+   研磨 → 齿轮/研磨器图标（多边形+圆）
+   冲煮 → 咖啡杯图标（梯形杯身+椭圆杯口+弧线蒸汽）
+ - 节点间连接线可以使用渐变色过渡（绿色→棕色），隐喻从原料到成品的变化
+ - 在画布底部或侧边添加小的装饰性咖啡豆散落（小椭圆+曲线）
```

```diff
  ## 美观原则：
+ 
+ 6. 装饰性元素的"三要三不要"：
+    要：与主题相关的隐喻性装饰（咖啡豆、齿轮、书本、芯片）
+    要：弱化处理（低透明度 10-20%、小尺寸、放在边角）
+    要：风格统一（全部线框风格或全部填充风格）
+    不要：与主题无关的纯装饰（随机波浪线、无意义几何图形）
+    不要：喧宾夺主（装饰面积不超过画布的 10%）
+    不要：使用复杂路径（超过 3 个贝塞尔曲线控制点的 path）
```

#### svg_guidelines.txt —— 增强设计规范

**当前问题**：
- sample1 中的残差连接（虚线弧线）在 Agent 3 的 prompt 中有提及但缺乏具体实现指导
- 缺少对"信息密度过高"场景的降级策略

**优化方向**——新增以下章节：

```markdown
## 复杂架构图的布局策略

### 残差连接/跳跃连接的实现
当架构图中有从底层绕到顶层的跳跃连接时：
1. 使用 `<path>` 的贝塞尔曲线命令 `C` 而非直线，创建优雅的弧形绕行
2. 线条使用虚线样式 `stroke-dasharray="6,3"` 与主数据流区分
3. 颜色使用低饱和度的灰色（如 #95A5A6）而非主色，降低视觉权重
4. 弧线从模块侧面出发，沿画布边缘绕行，不穿越其他模块

示例：
<path d="M 100,500 C 50,500 50,100 100,100" 
      fill="none" stroke="#95A5A6" stroke-width="1.5" 
      stroke-dasharray="6,3" marker-end="url(#arrow-gray)"/>

### 信息密度过高的降级策略
如果画布中元素超过 20 个：
1. 优先保障 primary 元素的完整展示
2. secondary 元素可以缩小字号 2-4px
3. tertiary 元素可以合并或省略
4. 使用背景色块区分功能区域，减少视觉混乱
```

### 5.3 优化迭代流程

```
┌──────────────────────────────────────────────────┐
│           Prompt 优化迭代流程                      │
│                                                  │
│  1. 识别问题                                      │
│     └→ 查看 Agent 4 审查报告中的低分维度           │
│     └→ 查看 SVG 渲染截图，人工发现视觉问题         │
│                                                  │
│  2. 定位根因                                      │
│     └→ 是 Agent 1 分析不准确？（改 agent1_system） │
│     └→ 是 Agent 2 布局不合理？（改 agent2_system） │
│     └→ 是 Agent 3 编码质量差？（改 agent3_system   │
│        或 svg_guidelines）                       │
│     └→ 是 Agent 4 审查标准有问题？（改 agent4）    │
│                                                  │
│  3. 单样例验证                                    │
│     └→ python main.py --sample sampleX            │
│     └→ 对比修改前后评分                            │
│                                                  │
│  4. 全样例回归                                    │
│     └→ 确保一个 prompt 修改不破坏其他样例           │
│     └→ python main.py（全量运行）                  │
└──────────────────────────────────────────────────┘
```

**核心原则**：
- **一次只改一个文件的一个部分**——否则无法归因效果
- **每次修改后单样例验证**——不要改完全部再跑，迭代周期太长
- **记录每次修改的效果**——形成 prompt 优化日志，作为报告的"Prompt Engineering"章节素材

### 5.4 结论

Prompt 优化是当前投入产出比最高的改进方向。修改 `agent1_system.txt`、`agent3_system.txt` 和 `svg_guidelines.txt` 这三个文件即可覆盖大部分质量提升空间。建议在模型切换（方向一）之前先做 prompt 优化，作为 baseline；切换模型后再对比，可以分离"模型能力"和"prompt 质量"的贡献。

---

## 6. 方向六：引入图标库（iconfont.cn）的可行性分析

### 6.1 问题拆解

用户的核心需求可以拆解为三个子问题：

| 子问题 | 难度 | 说明 |
|--------|:----:|------|
| Q1: LLM 能否搜索图标库？ | 🔴 不可行 | LLM 无法访问外部网站，需要人工预选 |
| Q2: LLM 能否选择合适的图标？ | 🟡 可行 | 如果提供图标目录，LLM 可以匹配 |
| Q3: LLM 能否准确放置图标？ | 🟡 可行但易出错 | SVG 坐标计算是 LLM 的弱项 |

### 6.2 技术方案分析

#### 方案 A：LLM 直接调用 iconfont API（❌ 不可行）

```
Agent 3: "我需要一个咖啡图标" → iconfont API → 返回图标 → 嵌入 SVG
```

**不可行原因**：
1. LLM 没有网络访问能力（除非配置 MCP tool，但当前架构不支持 Agent 3 调用外部工具）
2. iconfont 没有面向机器的检索 API（只有面向人类的搜索界面）
3. 即使有 API，图标的选择需要视觉判断——LLM 无法"看到"图标长什么样

#### 方案 B：人工预选图标 + LLM 按需选择（⚠️ 可行但局限性大）

```
人 → 预选 20 个图标 → 存储为 SVG symbols → 提供图标目录给 Agent 3 →
Agent 3 在生成 SVG 时通过 <use href="#icon-coffee" x="..." y="..."/> 引用
```

**实施步骤**：

```
Step 1: 在 iconfont.cn 上搜索并下载 15-20 个图标（SVG 格式）
        覆盖主题：咖啡/食物、科技/芯片、教育/书本、时间/日历、
                 人物、自然/植物、数据/图表
Step 2: 将图标整合为一个 SVG sprite 文件（resources/icons.svg）
Step 3: 编写图标目录文件（resources/icon_catalog.json）
Step 4: 在 svg_guidelines.txt 中添加图标使用说明
Step 5: Agent 3 在生成 SVG 时嵌入图标引用
```

**图标目录示例**（`resources/icon_catalog.json`）：

```json
{
  "icons": [
    {
      "id": "icon-coffee-bean",
      "description": "咖啡豆",
      "category": "food",
      "viewBox": "0 0 24 24",
      "width": 24,
      "height": 24,
      "keywords": ["咖啡", "豆", "种植", "原料"]
    },
    {
      "id": "icon-fire",
      "description": "火焰",
      "category": "nature",
      "viewBox": "0 0 24 24",
      "width": 24,
      "height": 24,
      "keywords": ["烘焙", "热", "加热", "火"]
    },
    {
      "id": "icon-chip",
      "description": "芯片/处理器",
      "category": "tech",
      "viewBox": "0 0 24 24",
      "width": 24,
      "height": 24,
      "keywords": ["芯片", "CPU", "GPU", "处理器", "硬件"]
    }
  ]
}
```

**在 svg_guidelines.txt 中添加**：

```markdown
## 图标库使用说明

本项目提供了预选 SVG 图标库，位于 `resources/icons.svg`。
在生成 SVG 时，你可以通过以下方式引用图标：

1. 在 SVG 的 `<defs>` 中引入图标 sprite：
   将 resources/icons.svg 的内容复制到你的 SVG `<defs>` 中

2. 在需要图标的位置使用 `<use>` 标签：
   <use href="#icon-coffee-bean" x="100" y="200" width="32" height="32"/>

3. 可用图标列表（详见 resources/icon_catalog.json）：
   - icon-coffee-bean: 咖啡豆 → 用于咖啡/种植相关场景
   - icon-fire: 火焰 → 用于烘焙/加热相关场景
   - icon-chip: 芯片 → 用于技术/架构图场景
   - icon-book: 书本 → 用于教育/历史场景
   - icon-chart: 图表 → 用于数据对比场景
   ...

4. 图标使用原则：
   - 图标尺寸统一（24-36px），不要过大
   - 图标颜色应与配色方案一致（使用 fill="currentColor" 或显式指定）
   - 图标放在流程节点左侧或上方，作为视觉辅助
   - 不要在所有节点上都放图标——仅关键节点使用
```

**此方案的核心局限**：

1. **图标需要与配色方案兼容**。iconfont 下载的图标通常是单色（黑色），需要 Agent 3 在引用时修改 `fill` 颜色。但 `<use>` 标签的颜色继承有坑——如果原始图标内部元素有 `fill` 属性，外部 `fill` 不会覆盖。

2. **坐标放置仍是 LLM 的弱项**。为图标计算合适的 x/y 坐标，使其与相邻文本/节点对齐——这对 LLM 来说是不小的挑战。容易出现图标与文本重叠或偏移的问题。

3. **图标库维护成本**。每新增一个样例类型就需要扩充图标库。

#### 方案 C：LLM 使用基本 SVG 几何图形拼出"图标"（✅ 当前方案，推荐继续）

Agent 3 的 system prompt 中已经包含：

```
可以使用简单的几何图形组合来创造示意性图标：
- 文档：矩形 + 折角线
- 齿轮/设置：六边形 + 内圆
- 人物：圆 + 梯形身体
```

这是目前最务实的方案。**不需要外部资源依赖，风格自动统一（因为都是 Agent 3 从零绘制的几何图形），颜色自动匹配配色方案**。

**增强建议**：

在 `svg_guidelines.txt` 中扩展几何图标的"组件库"：

```markdown
## 几何图标组件库

以下几何图标组合可以直接在你的 SVG 中使用（替换示例坐标）：

### 咖啡豆
<ellipse cx="16" cy="14" rx="6" ry="8" fill="#8B4513" transform="rotate(-15 16 14)"/>
<path d="M 16,6 Q 20,14 16,22" fill="none" stroke="#5D2E0C" stroke-width="0.8"/>

### 火焰
<polygon points="16,2 12,8 14,8 10,16 16,10 14,10 20,4" fill="#FF6B35"/>

### 芯片
<rect x="4" y="4" width="24" height="24" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/>
<rect x="10" y="10" width="12" height="12" rx="1" fill="currentColor" opacity="0.3"/>

### 齿轮
<circle cx="16" cy="16" r="6" fill="none" stroke="currentColor" stroke-width="2"/>
<rect x="14" y="2" width="4" height="8" rx="1" fill="currentColor"/>
...（8个齿均匀分布）
```

这样 Agent 3 拥有了一个"代码级图标库"——不需要外部文件，直接复制粘贴坐标即可。比 iconfont 方案更健壮。

### 6.3 三方案对比

| 维度 | A: API 搜索 | B: 预选 + 引用 | C: 几何图形（当前） |
|------|:---:|:---:|:---:|
| **技术可行性** | ❌ | ⚠️ | ✅ |
| **图标精美度** | 高 | 高 | 中 |
| **颜色适配** | 差（需手动处理） | 差（fill 继承有坑） | 优（自动匹配） |
| **坐标定位精度** | N/A | 差（LLM 弱项） | 中（几何图形也是 LLM 算坐标） |
| **维护成本** | 低（假设 API 可用） | 高（每次扩充需人工选图标） | 低（LLM 自行创作） |
| **风格一致性** | 不可控 | 可控（人工预选） | 天然一致（同一 LLM 生成） |
| **引入新问题** | 无 API、无视觉判断 | 颜色不匹配、坐标偏移 | 图标可能简陋 |

### 6.4 结论与推荐

**iconfont 方案（方案 B）不建议作为主要方向**，原因如下：

1. **核心技术障碍**：LLM 无法"看到"图标，无法判断图标风格是否匹配、颜色是否协调。这导致图标选择本质上仍是随机匹配（基于关键词），没有利用图标库的核心优势（视觉精美度）。

2. **引入新问题多于解决的问题**：颜色继承的 SVG 技术坑、坐标偏移的对齐问题——这些是硬骨头，解决成本高于收益。

3. **与课程定位不匹配**：课程评分的核心是 NLP 知识深度，不是前端设计精美度。花大量时间处理图标库集成和颜色兼容性，对得分帮助有限。

**推荐替代方案**：

1. **增强方案 C**（几何图标组件库）：在 `svg_guidelines.txt` 中扩展 15-20 个几何图标的代码片段。这是零外部依赖、最高效的提升视觉丰富度的方式。

2. **如果确实需要外部图标**：不接入 iconfont，而是**手工挑选 10 个最关键的图标**，在 Illustrator/Figma 中手动调整为与项目配色方案兼容的版本（移除硬编码 fill），然后一次性嵌入 `resources/icons.svg`。Agent 3 只需要知道图标 ID 和用途，无需做颜色匹配。这种"精选 + 预处理"的方式比"接入图标库让 LLM 自己搜"可控得多。

3. **Unicode 符号作为轻量装饰**：在标题或关键节点旁使用 Unicode 符号（如 ☕ 🔥 ⚙️ 📚 📊 🌱 ⏳），这些符号在所有系统中都能正常渲染，不需要额外文件，零坐标计算。缺点是视觉效果较简单。

```svg
<!-- 示例：在流程节点标签中使用 Unicode 符号 -->
<text x="400" y="200" text-anchor="middle" font-size="16">
  🌱 种植
</text>
```

---

## 七、优化优先级总结

综合 6 个方向的分析，建议的执行优先级如下：

| 优先级 | 方向 | 行动 | 预计耗时 | 报告价值 |
|:------:|------|------|:--------:|:--------:|
| 🔴 P0 | 方向四：NER/RE 标注 | 创建 5 个 ground truth 文件 + 评估脚本 + 运行 | 3-4h | 极高（量化 NLP 能力） |
| 🔴 P0 | 方向五：Prompt 优化 | 针对 agent1/agent3/svg_guidelines 三个文件做定向修改 | 3-5h | 高（展示 prompt engineering） |
| 🟡 P1 | 方向二：消融实验 | 实现 MAX_ROUNDS 参数化 + 跑 3×5=15 次实验 | 2-3h（含等待） | 极高（实验方法论） |
| 🟡 P1 | 方向一：模型切换 | 配置 v4-flash + v4-pro fallback + A/B 实验 | 2-3h（含等待） | 高（工程决策分析） |
| 🟢 P2 | 方向六：图标库 | 扩展几何图标组件库（方案 C）+ 可选预选 10 图标 | 2-4h | 中（锦上添花） |
| ⚪ 跳过 | 方向三：PPT | 已确认跳过 | — | — |

**建议的执行顺序**：方向四（标注）→ 方向五（prompt 优化）→ 方向二（消融）→ 方向一（模型切换）→ 方向六（图标增强）

这个顺序确保了：
- 先建立 NLP 评估基线（标注 + 当前指标）
- 再做 prompt 优化并评估提升幅度
- 然后通过消融实验量化反馈循环的价值
- 接着探索模型切换的性能-质量 trade-off
- 最后用图标增强做视觉润色

所有实验结果都应该归档到报告中——它们共同构成了一个完整的"系统优化与评估"叙事。

---

> **文档维护**：每完成一个方向的优化，请在本节末尾追加结果摘要（日期 + 关键发现 + 指标变化）。
