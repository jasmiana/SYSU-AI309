# 实施计划：基于多智能体的静态 SVG/动态 SVG/PPT 生成系统

> **版本**: v1.0  
> **日期**: 2026-07-09  
> **基于**: PRD v1.0 + insights.md（含 review.md 元评估）

---

## 目录

1. [项目概述与目标](#1-项目概述与目标)
2. [总体架构设计](#2-总体架构设计)
3. [多智能体详细设计](#3-多智能体详细设计)
4. [中间表示（IR）Schema 定义](#4-中间表示ir-schema-定义)
5. [知识检索模块设计](#5-知识检索模块设计)
6. [渲染与验证闭环设计](#6-渲染与验证闭环设计)
7. [技术栈选型](#7-技术栈选型)
8. [分阶段开发计划](#8-分阶段开发计划)
9. [五个必选样例策略](#9-五个必选样例策略)
10. [NLP 知识深度展示计划](#10-nlp-知识深度展示计划)
11. [风险管理矩阵](#11-风险管理矩阵)
12. [报告撰写大纲](#12-报告撰写大纲)

---

## 1. 项目概述与目标

### 1.1 项目定位

构建一个**基于多智能体（Multi-Agent）协作架构**的自然语言到可视化内容生成系统。用户输入自然语言提示词（中文/英文/中英混合），系统通过多个专业化 Agent 的协作，自动生成高质量的静态 SVG 信息图、动态 SVG 动画或 PPT 演示文稿。

### 1.2 核心目标

| 维度 | 目标 | 度量标准 |
|------|------|----------|
| **功能完整性** | 支持 5 种可视化类型（概念解释、科普教学、历史叙述、流程展示、数据对比） | 5 个必选样例全部通过 |
| **多智能体架构** | 至少 4 个专业化 Agent 协作完成生成任务 | Agent 数量 ≥ 4，职责明确分离 |
| **NLP 知识深度** | 体现 ≥ 8 项 NLP 课程核心概念 | 报告中逐项分析映射 |
| **输出质量** | SVG 语法有效、视觉合理、内容准确 | XML 验证通过 + 人工评估 ≥ 4/5 |
| **鲁棒性** | 对输入变化、知识缺失具有容错能力 | 所有样例优雅降级，无崩溃 |

### 1.3 设计哲学

本方案遵循以下工程原则（经 insights.md 第十章元评估校准）：

1. **NLP 深度优先**：架构设计以最大化 NLP 知识展示深度为元标准，工程复杂度服务于这一目标。
2. **渐进式实施**：Phase 1 先跑通最小可行流水线 (Agent 1 → Agent 3 → 输出)，后续迭代加固各层。
3. **务实的复杂度控制**：区分"必须做"（渲染验证、置信度分数、样例分析）和"可以后做"（多模态评估、并行备选生成）。
4. **IR 作为通信协议**：Agent 间传递结构化 JSON 中间表示，但最终 SVG 生成保留 LLM 的灵活性（选择性采纳方向 B，非完整渲染引擎路线）。

---

## 2. 总体架构设计

### 2.1 架构概览

采用 **方向 A（多 Agent 流水线）+ 方向 B（选择性 IR）+ 方向 E（知识增强）** 的混合架构：

```
                          ┌─────────────────────┐
                          │   外部知识源         │
                          │   · Web Search API   │
                          │   · 预置知识库        │
                          │   · SVG 设计规范      │
                          └──────────┬──────────┘
                                     │ (按需触发)
                                     ▼
┌──────────────────────────────────────────────────────────────┐
│                    多智能体核心流水线                          │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐ │
│  │ Agent 1  │───▶│ Agent 2  │───▶│ Agent 3  │───▶│ Agent 4 │ │
│  │ 内容分析器│    │ 布局规划器│    │ SVG 生成器│    │ 质量审核器│ │
│  │          │    │          │    │          │    │         │ │
│  │ 意图分类 │    │ 图表选型  │    │ SVG 编码  │    │ 语法检查 │ │
│  │ 实体抽取 │    │ 空间布局  │    │ 文本凝练  │    │ 内容验证 │ │
│  │ 关系识别 │    │ 配色方案  │    │ 动画实现  │    │ 布局校验 │ │
│  │ 知识检索 │    │ 视觉层次  │    │ 标注添加  │    │ 美学评估 │ │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬────┘ │
│       │               │               │               │      │
│       ▼               ▼               ▼               │      │
│  内容 IR         布局 IR           SVG 代码     ┌──────┘      │
│  (JSON)         (JSON)           (XML)        │             │
│                                               ▼             │
│                                    ┌─────────────────────┐  │
│                                    │  渲染验证闭环        │  │
│                                    │  · cairosvg 渲染     │  │
│                                    │  · XML 语法验证      │  │
│                                    │  · 结构化规则检查    │  │
│                                    │  · 自动修复建议      │  │
│                                    └──────────┬──────────┘  │
│                                               │             │
│                                    反馈修改 or 通过         │
└──────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                              最终输出
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              静态 SVG     动态 SVG     PPT (可选)
```

### 2.2 架构决策记录（ADR）

| 决策 | 选择 | 替代方案 | 理由 |
|------|------|----------|------|
| Agent 数量 | 4 核心 + 2 辅助 | 3 或 6+ | 4 核心 Agent 覆盖分析→规划→生成→审查的完整链路，职责分离清晰但不过度碎片化 |
| Agent 间通信格式 | JSON（结构化输出） | 自然语言、伪代码 | JSON 可程序化验证、无歧义、便于调试和日志记录 |
| SVG 生成方式 | LLM 直接生成 | 完整 IR→渲染引擎 | 保留 LLM 的创意灵活性；结构化图表（流程图、柱状图）可选走渲染器 |
| 知识检索触发 | 按需触发（Agent 1 判断） | 始终检索、始终不检索 | 节省 Token，仅在提示词信息不足时检索 |
| 迭代上限 | Agent 4→3 最多 2 轮 | 无限循环、单次 | 防止无限修改循环，2 轮足以修复大多数问题 |
| 渲染验证 | cairosvg 渲染 + 结构化规则检查 | 多模态模型评估 | 成本可控、无 self-evaluation bias、可自动执行 |

### 2.3 数据流与信息传递

```
用户提示词 (自然语言)
    │
    ▼
Agent 1: 内容分析器
    │ 输出: ContentIR { intent, entities, relations, chart_type, knowledge_supplement }
    ▼
Agent 2: 布局规划器
    │ 输入: ContentIR + 设计规范 (system prompt)
    │ 输出: LayoutIR { chart_type, canvas, color_scheme, sections[], elements[], arrows[] }
    ▼
Agent 3: SVG 生成器
    │ 输入: LayoutIR + ContentIR.content_texts + SVG 编写规范 (system prompt)
    │ 输出: SVG 字符串 (XML)
    ▼
Agent 4: 质量审核器
    │ 输入: SVG + 原始提示词 + ContentIR + LayoutIR + 结构化检查报告
    │ 输出: ReviewResult { pass, issues[], suggestions[], needs_regeneration }
    ▼
[渲染验证闭环]
    │ cairosvg 渲染 → 坐标验证 → 元素重叠检测 → 对比度检查
    │ 输出: StructuredCheckReport { xml_valid, bounds_ok, overlaps[], contrast_issues[] }
    ▼
最终输出: SVG/PPT
```

---

## 3. 多智能体详细设计

### 3.1 Agent 1：内容分析器（Content Analyzer）

**职责**：对用户提示词进行深层语义分析，提取结构化信息，判断可视化需求，必要时检索外部知识。

**NLP 知识体现**：
- 意图识别（Intent Classification）
- 命名实体识别（NER）
- 关系抽取（Relation Extraction）
- 指代消解（Coreference Resolution）
- 信息检索（IR）

**输入**：
```json
{
  "user_prompt": "string (原始提示词)",
  "context": "string | null (可选的上下文信息)"
}
```

**System Prompt 设计要点**：
```
你是一个专业的自然语言内容分析器。你的任务是深度分析用户的提示词，
提取用于生成 SVG 信息图所需的所有结构化信息。

分析步骤（Chain-of-Thought）：
1. 意图分类：用户想要什么类型的可视化？
   - concept_explanation (概念解释)
   - process_flow (流程展示)
   - data_comparison (数据对比)
   - timeline (时间线/历史叙述)
   -科普 (科普教学)
   - architecture_diagram (架构图)

2. 实体抽取：提示词中包含哪些关键实体？
   - 人物、组织、地点、术语、数值

3. 关系识别：实体之间存在什么关系？
   - 对比关系、层级关系、流程关系、时序关系、因果关系

4. 信息完整性评估：提示词是否包含足够的信息来生成可视化？
   - 如果信息不足，标记需要检索的主题

5. 目标受众分析：内容的难度和风格应该是什么？
```

**输出 Schema**：
```json
{
  "intent": {
    "primary_type": "concept_explanation | process_flow | data_comparison | timeline |科普 | architecture_diagram",
    "secondary_type": "string | null",
    "confidence": 0.0-1.0,
    "reasoning": "string"
  },
  "entities": [
    {
      "name": "string",
      "type": "person | organization | location | term | number | date",
      "role": "subject | object | attribute | relation",
      "importance": "primary | secondary | context"
    }
  ],
  "relations": [
    {
      "type": "comparison | hierarchy | sequence | causality | spatial | temporal",
      "source": "string (entity name)",
      "target": "string (entity name)",
      "description": "string",
      "quantifier": "string | null (e.g., '10 times more than')"
    }
  ],
  "content_summary": {
    "title": "string",
    "key_points": ["string"],
    "target_audience": "general | technical | academic",
    "language": "zh | en | mixed"
  },
  "knowledge_gap": {
    "needs_external_knowledge": true/false,
    "search_queries": ["string"],
    "fallback_knowledge": "string | null"
  },
  "chart_type": {
    "recommended": "flowchart | bar_chart | timeline | architecture_diagram | concept_map | comparison_chart | process_diagram",
    "alternatives": ["string"],
    "type_confidence": 0.0-1.0
  }
}
```

**关键实现细节**：
- 对于 `type_confidence < 0.8` 的情况，在输出中标记 `alternatives`，由 Agent 4 在审查阶段做二次确认
- `knowledge_gap.needs_external_knowledge == true` 时，触发 Web Search API 检索
- 所有 NER 和 RE 结果记录在日志中，用于报告中的 NLP 知识运用分析

---

### 3.2 Agent 2：布局规划器（Layout Planner）

**职责**：将结构化内容转换为空间布局方案，包括图表选型、元素位置规划、配色方案设计、视觉层次定义。

**NLP 知识体现**：
- 结构化知识表示（Structured Knowledge Representation）
- 文本到空间的语义映射（Semantic-to-Spatial Mapping）
- 多模态信息组织（Multimodal Information Organization）

**输入**：
```json
{
  "content_ir": "{Agent 1 的完整输出}",
  "design_constraints": {
    "canvas_width": 800,
    "canvas_height": 1200,
    "style": "modern_clean | colorful | minimalist | academic"
  }
}
```

**System Prompt 设计要点**：
```
你是一个专业的可视化布局规划器。你的任务是将结构化内容映射为空间布局方案。

设计原则：
1. 信息层次：使用视觉层次（大小、颜色、位置）来表达语义重要性
2. 阅读顺序：自上而下、从左到右，引导观众的视线流动
3. 留白原则：使用充分留白防止信息过载，最小元素间距 20px
4. 分组原则：相关元素在空间上靠近，不相关元素在空间上分离
5. 对齐原则：元素应当沿网格对齐，保持视觉整洁

布局约束：
- 使用比例布局 (percentages) 而非绝对像素坐标
- 每个元素的尺寸使用 {x_pct, y_pct, width_pct, height_pct} 表示
- 标题区域占画布 8-12% 高度
- 主要内容区域占画布 75-80% 高度
- 页脚/注释区域占画布 5-8% 高度
```

**输出 Schema**：
```json
{
  "chart_type": "string (与 Agent 1 推荐一致或微调)",
  "canvas": {
    "width": 800,
    "height": "number (根据内容自动计算)",
    "background": "#FFFFFF | 渐变色定义"
  },
  "color_scheme": {
    "name": "string",
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "text_primary": "#hex",
    "text_secondary": "#hex",
    "palette": ["#hex"],
    "rationale": "string (配色选择理由)"
  },
  "typography": {
    "title_size": "number (px)",
    "heading_size": "number (px)",
    "body_size": "number (px)",
    "label_size": "number (px)",
    "font_family": "sans-serif | serif | monospace"
  },
  "layout_grid": {
    "columns": "number",
    "rows": "number",
    "gutter": "number (px)"
  },
  "sections": [
    {
      "id": "string",
      "type": "title | content_block | diagram | chart | timeline | footer",
      "position": {"x_pct": 0-100, "y_pct": 0-100, "width_pct": 0-100, "height_pct": 0-100},
      "z_index": "number",
      "visual_weight": "primary | secondary | tertiary"
    }
  ],
  "elements": [
    {
      "id": "string",
      "type": "rect | rounded_rect | circle | ellipse | diamond | hexagon | text_block | image_placeholder | arrow | line | icon",
      "label": "string",
      "parent_section": "string (section id)",
      "color": "string (color key from color_scheme)",
      "importance": "primary | secondary | tertiary",
      "relative_position": {"x_offset_pct": 0-100, "y_offset_pct": 0-100},
      "size_hint": {"min_width": "number", "min_height": "number", "aspect_ratio": "number | null"}
    }
  ],
  "connections": [
    {
      "id": "string",
      "type": "arrow | line | curve | dashed",
      "from_element": "string (element id)",
      "to_element": "string (element id)",
      "direction": "top-to-bottom | left-to-right | bottom-to-top | right-to-left",
      "label": "string | null",
      "line_style": "solid | dashed | dotted"
    }
  ],
  "design_notes": "string (给 Agent 3 的视觉设计指导)"
}
```

**关键实现细节**：
- **使用比例布局而非绝对坐标**：Agent 2 输出百分比位置（如 `x_pct: 50, y_pct: 30`），Agent 3 根据实际文本长度在合理范围内自适应调整。这从根本上规避了"尺寸不匹配"问题（insights.md §10.3 替代方案 a）。
- `size_hint` 字段提供最小尺寸和宽高比建议，Agent 3 在编码时可基于实际文本内容微调。
- `design_notes` 为 Agent 3 提供自然语言级别的视觉指导，弥补 JSON 结构对美学意图的表达局限。

---

### 3.3 Agent 3：SVG 生成器（SVG Coder）

**职责**：根据布局 IR 和内容 IR，编写完整、有效的 SVG XML 代码。需要同时具备代码生成能力和视觉设计感。

**NLP 知识体现**：
- 受控文本生成（Controlled Text Generation）
- 文本摘要/凝练（Text Summarization for Labels）
- 代码生成（Code Generation，跨模态映射）

**输入**：
```json
{
  "layout_ir": "{Agent 2 的完整输出}",
  "content_ir": "{Agent 1 的完整输出}",
  "svg_spec": {
    "version": "1.1",
    "use_css_animations": false,
    "use_smil_animations": false,
    "embed_fonts": false,
    "accessibility": true
  }
}
```

**System Prompt 设计要点**：
```
你是一个专业的 SVG 代码生成器。你需要根据布局规划生成高质量的 SVG XML 代码。

SVG 编码规范：
1. 使用 <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H"> 根元素
2. 坐标必须在 viewBox 范围内，不能越界
3. 所有标签必须正确闭合，属性值必须用引号包围
4. 使用 <defs> 定义可复用的渐变、滤镜、标记（箭头、阴影）
5. 颜色使用十六进制值或 CSS 变量，不使用命名颜色
6. 文本使用 <text> 元素，设置 text-anchor 和 dominant-baseline 确保对齐
7. 为所有元素添加 class 属性以便样式控制
8. 使用 <g> 分组相关元素

设计规范：
1. 圆角矩形的 rx/ry 与尺寸成比例（小元素 rx=4-6，大元素 rx=8-12）
2. 箭头使用 <marker> 定义在 <defs> 中
3. 阴影使用 <filter> 定义，适度使用（主要元素才加阴影）
4. 渐变方向与阅读方向一致（标题用水平渐变，流程用垂直渐变）
5. 文本与容器之间保留适当内边距（最小 10px）
6. 图标/装饰元素保持简洁，不要过度复杂

文本凝练规则：
- 标题：不超过 20 字（中文）或 15 词（英文）
- 节点标签：不超过 8 字或 5 词
- 说明文本：每行不超过 30 字，总行数不超过 4 行
- 数据标签：数值 + 单位，无需完整句子

⚠️ 关键约束：
- 你可以在合理范围内微调布局 IR 中的元素位置以适配实际文本尺寸
- 如果某个文本标签超出容器，你有权调整字号或拆分文本
- 如果布局 IR 中的某个位置导致元素重叠，你需要自行调整间距
```

**输出**：完整的 SVG XML 字符串。

**关键实现细节**：
- Agent 3 拥有布局的**最终调整权**：可以在 Agent 2 的布局框架内，基于实际文本渲染需求微调位置和尺寸。这使得 Agent 3 能够自然地处理内容-布局匹配问题，无需引入 Agent 2↔3 反馈循环（insights.md §10.3 替代方案 c）。
- 在 system prompt 中嵌入常用 SVG 设计模式片段（圆角矩形卡片、箭头连接线、渐变标题栏、阴影定义），作为隐式的 few-shot 参考。
- 对于静态 SVG，将 CSS 样式内嵌在 `<style>` 标签中；对于动态 SVG，在 system prompt 中额外加入 CSS animation / SMIL 动画规范。

---

### 3.4 Agent 4：质量审核器（Quality Reviewer）

**职责**：对生成的 SVG 进行多维度审查，识别并报告问题，决定是否需要修改。**审查的输入不仅是 SVG 文本，还包括结构化检查报告**。

**NLP 知识体现**：
- 自动评估（Automatic Evaluation）
- 文本蕴含/一致性检测（Textual Entailment / Consistency Checking）
- 错误分析与诊断（Error Analysis）

**输入**：
```json
{
  "svg_code": "string (Agent 3 的输出)",
  "original_prompt": "string",
  "content_ir": "{Agent 1 输出}",
  "layout_ir": "{Agent 2 输出}",
  "structured_check": {
    "xml_valid": true/false,
    "xml_errors": ["string"],
    "bounds_check": {"ok": true/false, "out_of_bounds": ["element_id"]},
    "overlap_check": {"ok": true/false, "overlaps": [{"elem1": "id", "elem2": "id"}]},
    "contrast_check": {"ok": true/false, "low_contrast": [{"text": "string", "ratio": "number"}]},
    "text_truncation_check": {"ok": true/false, "issues": ["string"]}
  }
}
```

**System Prompt 设计要点**：
```
你是一个专业的 SVG 质量审核器。你需要从多个维度审查生成的 SVG。

审查维度：
1. 语法正确性（参考 structured_check）：XML 是否有效？标签是否闭合？
2. 视觉布局（参考 structured_check）：元素是否越界？是否重叠？对比度是否足够？
3. 内容准确性：SVG 中的文本是否准确表达了原始提示词的意图？
4. 图表类型合理性：当前使用的图表类型是否最适合表达这个内容？
   如果不是，应该建议什么类型？
5. 信息完整性：关键实体和关系是否都在 SVG 中有所体现？
6. 美学质量：配色是否协调？字体层次是否合理？留白是否充分？

判定规则：
- 语法错误：必须修改
- 内容错误（关键实体缺失或错误）：必须修改
- 布局问题（重叠、越界）：必须修改
- 图表类型错误：建议修改
- 美学问题：建议修改（但不阻塞通过）
- 轻微文本凝练问题：记录但不阻塞
```

**输出 Schema**：
```json
{
  "pass": true/false,
  "overall_score": 0-10,
  "dimensions": {
    "syntax": {"score": 0-10, "pass": true/false, "issues": ["string"]},
    "layout": {"score": 0-10, "pass": true/false, "issues": ["string"]},
    "content_accuracy": {"score": 0-10, "pass": true/false, "issues": ["string"]},
    "chart_type_appropriateness": {"score": 0-10, "pass": true/false, "issues": ["string"]},
    "information_completeness": {"score": 0-10, "pass": true/false, "issues": ["string"]},
    "aesthetics": {"score": 0-10, "pass": true/false, "issues": ["string"]}
  },
  "needs_regeneration": true/false,
  "regeneration_focus": ["dimension_name"],
  "specific_suggestions": [
    {
      "target": "element_id | section_id | global",
      "issue": "string",
      "suggestion": "string",
      "priority": "critical | high | medium | low"
    }
  ],
  "summary": "string (给 Agent 3 修改用的简明指导)"
}
```

**反馈流程**：
```
Agent 4 审查
    │
    ├── pass == true → 输出最终 SVG
    │
    └── pass == false
          │
          ├── 第 1 轮修改 → Agent 3（附带 suggestions）→ Agent 4 再审
          │     │
          │     ├── pass == true → 输出
          │     └── pass == false → 第 2 轮修改（最后一次）
          │           │
          │           └── 无论结果如何，输出当前最优版本 + 问题清单
```

---

### 3.5 辅助 Agent：知识检索器（Knowledge Retriever）

**职责**：当 Agent 1 判断需要外部知识时，执行 Web 搜索并整理结果。

**触发条件**：`Agent1.output.knowledge_gap.needs_external_knowledge == true`

**实现方式**：
- 优先使用 Web Search API（如 Bing Search API、SerpAPI）
- 备选：预置 JSON 知识库（针对高频主题如 Transformer 架构、SYSU 历史）
- 对样例 3（中山大学发展历程）：**手工整理关键时间节点作为 fallback**，确保即使搜索失败也有可靠数据

**输出**：
```json
{
  "search_results": [
    {
      "query": "string",
      "sources": [{"title": "string", "url": "string", "snippet": "string"}],
      "extracted_facts": ["string"],
      "reliability": "high | medium | low"
    }
  ],
  "compiled_knowledge": "string (整理后的知识摘要，供下游 Agent 使用)"
}
```

---

## 4. 中间表示（IR）Schema 定义

### 4.1 IR 设计原则

1. **人类可读**：IR 应该是可读的 JSON，便于调试和报告展示
2. **渐进细化**：Content IR（语义层）→ Layout IR（空间层）→ SVG（渲染层），信息沿流水线逐步具象化
3. **约束宽松**：IR 定义的是"结构骨架"而非"像素级规范"，给下游 Agent 留有自适应空间
4. **可扩展**：新增图表类型通过扩展 `chart_type` 枚举和对应的渲染策略实现

### 4.2 Content IR（Agent 1 → Agent 2）

详见 §3.1 的输出 Schema。核心字段：
- `intent`: 意图分类 + 置信度
- `entities[]`: NER 结果
- `relations[]`: RE 结果
- `knowledge_gap`: 知识检索触发
- `chart_type`: 推荐图表类型 + 备选 + 置信度

### 4.3 Layout IR（Agent 2 → Agent 3）

详见 §3.2 的输出 Schema。核心字段：
- `sections[]`: 区域划分（比例布局）
- `elements[]`: 元素定义 + 尺寸提示
- `connections[]`: 连接线/箭头定义
- `color_scheme`: 完整配色方案
- `design_notes`: 设计意图的自然语言说明

### 4.4 IR 在报告中的展示价值

IR 是展示 NLP 知识的核心载体：
- Content IR → 展示了 **NER、RE、意图分类** 的实际输出
- Layout IR → 展示了 **结构化知识表示** 和 **语义到空间的映射**
- 两份 IR 的对比 → 展示了 **信息如何在多 Agent 间无损传递**

报告应在每个样例的展示中附上简化版 IR，并分析 NLP 技术的运用。

---

## 5. 知识检索模块设计

### 5.1 检索策略

| 场景 | 检索策略 | Fallback |
|------|----------|----------|
| 样例 1（LLM 原理） | Agent 内置知识（LLM 训练数据已充分覆盖 Transformer） | 课程教材/课件摘要 |
| 样例 2（词向量） | Agent 内置知识 + few-shot 可视化范例 | 经典词向量可视化设计模式描述 |
| 样例 3（SYSU 历史） | **Web Search API + 手工整理的 fallback 时间线** | 手工整理的 10+ 关键时间节点 |
| 样例 4（咖啡链） | 不需要检索（提示词信息充分） | — |
| 样例 5（数据对比） | 不需要检索（提示词信息充分） | — |

### 5.2 样例 3 Fallback 知识库设计

```json
{
  "topic": "中山大学发展历程",
  "key_events": [
    {"year": 1924, "event": "国立广东大学创立，孙中山先生创办"},
    {"year": 1926, "event": "更名为国立中山大学，纪念孙中山先生"},
    {"year": 1930s, "event": "发展为文理工医农法多学科综合大学"},
    {"year": 1952, "event": "全国院系调整，成为文理科综合大学"},
    {"year": 1980s, "event": "改革开放后迅速发展，扩大办学规模"},
    {"year": 2000, "event": "珠海校区启用"},
    {"year": 2001, "event": "与原中山医科大学合并，组建新的中山大学"},
    {"year": 2004, "event": "广州东校区（大学城校区）启用"},
    {"year": 2015, "event": "深圳校区启动建设"},
    {"year": 2017, "event": "入选国家'双一流'建设高校（A类）"},
    {"year": 2020s, "event": "形成三校区五校园办学格局、11个学科入选双一流"}
  ],
  "source": "手工整理 + 中山大学官网验证",
  "reliability": "high"
}
```

---

## 6. 渲染与验证闭环设计

### 6.1 设计理念

渲染验证闭环是本方案的核心质量保障机制。参考 insights.md §10.2 的评估，采用**分阶段引入**策略：
- **Phase 2 引入**：cairosvg 渲染 + XML 语法验证 + 结构化规则检查
- **暂不引入**：多模态模型视觉评估（受限于 self-evaluation bias 和成本）

### 6.2 结构化检查规则

#### 6.2.1 XML 语法验证（cairosvg）

```python
import cairosvg
import xml.etree.ElementTree as ET

def validate_svg_syntax(svg_string: str) -> dict:
    """验证 SVG XML 语法"""
    try:
        ET.fromstring(svg_string)
        # cairosvg 渲染测试（检查更多语义正确性）
        cairosvg.svg2png(bytestring=svg_string.encode('utf-8'))
        return {"valid": True, "errors": []}
    except ET.ParseError as e:
        return {"valid": False, "errors": [str(e)]}
    except Exception as e:
        return {"valid": False, "errors": [f"cairosvg render error: {str(e)}"]}
```

#### 6.2.2 坐标越界检查

```python
def check_bounds(svg_string: str, viewBox: tuple) -> dict:
    """检查所有带坐标的元素是否在 viewBox 范围内"""
    # 解析所有 x, y, cx, cy 等坐标属性
    # 检查是否超出 viewBox (0, 0, W, H)
    ...
```

#### 6.2.3 元素重叠检测

```python
def check_overlaps(svg_string: str) -> dict:
    """检测文本/形状元素之间的重叠"""
    # 构建每个元素的包围盒 (bounding box)
    # 检测重要元素（非装饰性）之间的重叠
    ...
```

#### 6.2.4 颜色对比度检查

```python
def check_contrast(svg_string: str) -> dict:
    """检查文本-背景颜色对比度（WCAG AA 标准）"""
    # 提取文本颜色和其背景颜色
    # 计算对比度比值
    # WCAG AA: 正常文本 ≥ 4.5:1，大文本 ≥ 3:1
    ...
```

### 6.3 验证结果如何嵌入 Agent 4

`structured_check` 作为 Agent 4 的输入字段之一，Agent 4 在审查时同时参考：
1. **结构化报告**（确定性规则的输出）→ 处理可程序化检测的问题
2. **自身的纯文本推理**（语义理解）→ 处理需要理解力的内容一致性问题

这种分工避免了纯文本 LLM 对视觉判断的盲目性，也避免了纯规则引擎对语义理解的局限性。

---

## 7. 技术栈选型

### 7.1 核心技术栈

| 组件 | 选择 | 版本/型号 | 理由 |
|------|------|-----------|------|
| **主 LLM API** | DeepSeek API | deepseek-v4-pro | 深度推理能力强，开启思考模式 + high reasoning effort，适合复杂 SVG 生成 |
| **备选 LLM API** | DeepSeek API | deepseek-v4-flash | 轻量快速，用于简单场景或需要低延迟时 |
| **思考模式** | DeepSeek thinking | `{"type": "enabled"}` | 启用 CoT 推理链，生成质量显著提升；通过 `extra_body` 参数传入 |
| **推理强度** | reasoning_effort=high | — | 最大化推理深度，确保 Agent 1 分析准确 + Agent 3 SVG 质量 |
| **API 调用方式** | OpenAI Python SDK | — | DeepSeek API 完全兼容 OpenAI SDK 格式，通过自定义 base_url 接入 |
| **结构化输出** | Prompt 指令约束 | — | 通过 system prompt 要求输出纯 JSON，配合客户端解析 |
| **SVG 渲染** | cairosvg | Python | 轻量、纯 Python、支持基本 SVG 特性 |
| **SVG XML 解析** | xml.etree (标准库) | — | 轻量，满足基本验证需求 |
| **Web 搜索** | Wikipedia API + Web Search API | — | 优先 Wikipedia（结构化数据），备选通用搜索 |
| **开发语言** | Python | ≥ 3.10 | 生态丰富、开发效率高、教学环境友好 |
| **PPT 生成（可选）** | python-pptx | latest | 如实现 PPT 输出 |
| **配置管理** | python-dotenv | — | API Key 管理 |
| **日志系统** | Python logging + JSON | — | 全链路日志用于报告 |
| **输出管理** | 本地文件系统 | — | SVG/PPT 文件按样例分类保存 |

### 7.2 项目目录结构

```
project3/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py          # Agent 基类（API 调用、JSON 解析、重试逻辑）
│   │   ├── content_analyzer.py    # Agent 1: 内容分析器
│   │   ├── layout_planner.py      # Agent 2: 布局规划器
│   │   ├── svg_coder.py           # Agent 3: SVG 生成器
│   │   ├── quality_reviewer.py    # Agent 4: 质量审核器
│   │   └── knowledge_retriever.py # 辅助 Agent: 知识检索器
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # 流水线编排（多 Agent 调度、迭代控制）
│   │   └── ir_schema.py           # IR Schema 定义与验证
│   ├── rendering/
│   │   ├── __init__.py
│   │   ├── renderer.py            # cairosvg 渲染封装
│   │   └── validator.py           # 结构化规则检查（语法、坐标、重叠、对比度）
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── search.py              # Web Search / Wikipedia API 封装
│   │   └── fallback_db.json       # 预置知识库（SYSU 历史等）
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── agent1_system.txt      # Agent 1 system prompt
│   │   ├── agent2_system.txt      # Agent 2 system prompt
│   │   ├── agent3_system.txt      # Agent 3 system prompt
│   │   ├── agent4_system.txt      # Agent 4 system prompt
│   │   └── svg_guidelines.txt     # SVG 设计规范（供 Agent 3 和 4 共享）
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # 配置管理（API Key、参数）
│       ├── logger.py              # 日志系统
│       └── file_manager.py        # 输出文件管理
├── tests/
│   ├── test_agent1.py
│   ├── test_pipeline.py
│   └── test_validator.py
├── outputs/                       # 生成结果
│   ├── sample1_llm_principles/
│   ├── sample2_word_embedding/
│   ├── sample3_sysu_history/
│   ├── sample4_coffee_chain/
│   └── sample5_video_comparison/
├── docs/
│   ├── prd.md
│   ├── insights.md
│   ├── implementation_plan.md
│   └── report.md                  # 最终报告
├── .env                           # 环境变量（API Key）
├── .env.example
├── requirements.txt
├── main.py                        # 主入口
└── README.md
```

---

## 8. 分阶段开发计划

### 8.1 总体时间线

| 阶段 | 时间 | 目标 | 交付物 |
|------|------|------|--------|
| Phase 1 | Day 1-2 | 最小可行流水线 | 从 prompt 到 SVG 的端到端链路 |
| Phase 2 | Day 3-4 | 质量提升 | 完整的 4 Agent 流水线 + 渲染验证 |
| Phase 3 | Day 5 | 知识增强与高级特性 | Web 搜索集成 + 样例调优 |
| Phase 4 | Day 6-7 | 报告撰写与收尾 | 完整报告 + 5 样例最终结果 |

### 8.2 Phase 1：核心流水线搭建（Day 1-2）

**目标**：从用户 prompt → 结构化分析 → SVG 代码 → 输出文件，跑通最简链路。

**不包含**：Agent 2（布局规划器）、Agent 4（质量审核器）、渲染验证、知识检索。

**任务清单**：

| # | 任务 | 预计耗时 | 详细说明 |
|---|------|----------|----------|
| 1.1 | 项目环境搭建 | 1h | 初始化 Python 项目、安装依赖、配置 API Key、确定目录结构 |
| 1.2 | 实现 `base_agent.py` | 2h | LLM API 调用封装、JSON 结构化输出解析、重试机制（max 3 次）、超时处理 |
| 1.3 | 实现 Agent 1（内容分析器） | 3h | 编写 system prompt、实现 Content IR 输出、单元测试（5 个样例各跑一次） |
| 1.4 | 实现 Agent 3（SVG 生成器）基础版 | 4h | 编写 system prompt + SVG 规范、端到端测试（跳过 Agent 2，Agent 1 输出直接给 Agent 3）、生成 5 样例初版 |
| 1.5 | 实现流水线编排器 | 2h | 串联 Agent 1 → Agent 3、中间结果日志记录、输出文件保存 |
| 1.6 | 5 样例初版生成与评估 | 4h | 生成 5 样例的第一版 SVG、记录问题清单、评估生成质量基线 |

**Phase 1 产出**：
- 5 个样例的初始 SVG（质量可能一般，但链路跑通）
- Agent 1 和 Agent 3 的 system prompt 初版
- 问题清单（哪些样例效果差、哪些步骤需要优化）

**Phase 1 风险与应对**：
- **Agent 3 生成的 SVG 语法错误严重** → 在 system prompt 中加入更严格的 XML 规范约束，必要时在 Phase 1 末尾就加入 lightweight 的 XML 格式验证
- **某个样例效果明显不如预期** → 详细记录，Phase 2 优先处理

### 8.3 Phase 2：质量提升（Day 3-4）

**目标**：加入完整的 4 Agent 流水线、渲染验证闭环、迭代优化。

**任务清单**：

| # | 任务 | 预计耗时 | 详细说明 |
|---|------|----------|----------|
| 2.1 | 实现 Agent 2（布局规划器） | 4h | 编写 system prompt（比例布局 + 设计原则）、实现 Layout IR 输出、与 Agent 1 和 Agent 3 联调 |
| 2.2 | 实现渲染验证模块 | 3h | cairosvg 渲染、XML 语法验证、坐标越界检查、元素重叠检测、颜色对比度检查 |
| 2.3 | 实现 Agent 4（质量审核器） | 4h | 编写 system prompt（6 维审查 + 结构化检查报告解读）、实现 Review IR 输出、Agent 4 → Agent 3 反馈循环（max 2 轮） |
| 2.4 | 完整流水线联调 | 3h | 4 Agent 串联 + 渲染验证嵌入、全链路日志验证、迭代流程测试 |
| 2.5 | Prompt Engineering 优化 | 4h | 基于 Phase 1 问题清单，逐 Agent 优化 prompt、重点优化 Agent 3 的 SVG 编码质量 |
| 2.6 | 5 样例第二轮生成 | 2h | 全流程生成 5 样例、与 Phase 1 初版对比、记录质量提升幅度 |

**Phase 2 产出**：
- 完整的 4 Agent + 渲染验证流水线
- Phase 2 版本 5 样例 SVG
- Prompt 优化记录

### 8.4 Phase 3：知识增强与高级特性（Day 5）

**目标**：集成知识检索、加入 few-shot 可视化范式、可选 PPT 输出。

**任务清单**：

| # | 任务 | 预计耗时 | 详细说明 |
|---|------|----------|----------|
| 3.1 | 实现知识检索模块 | 3h | Web Search API 封装、Wikipedia API 封装、Agent 1 知识检索触发逻辑 |
| 3.2 | 建立 fallback 知识库 | 1h | SYSU 历史时间线数据整理、词向量经典可视化范式整理、LLM/Transformer 核心概念验证集 |
| 3.3 | 样例针对性优化 | 4h | **样例 2**：few-shot 词向量可视化设计模式嵌入、**样例 5**：数值推理强化 + 图表比例尺约束、**样例 3**：知识检索集成测试 |
| 3.4 | 设计规范完善 | 2h | 整理 SVG 设计规范文档（配色理论、排版原则、常见组件片段）、完善 Agent 3 的 system prompt |
| 3.5 | （可选）PPT 输出 | 2h | 使用 python-pptx 将 SVG 嵌入 PPT、多页幻灯片结构、如时间不足则舍弃 |

**Phase 3 产出**：
- 知识检索模块
- 样例针对性优化后的 SVG
- （可选）PPT 版本

### 8.5 Phase 4：报告撰写与收尾（Day 6-7）

**目标**：撰写完整课程设计报告，整理最终成果。

**任务清单**：

| # | 任务 | 预计耗时 | 详细说明 |
|---|------|----------|----------|
| 4.1 | 系统架构章节撰写 | 3h | 架构图绘制、多智能体协作机制详细描述、IR Schema 说明 |
| 4.2 | NLP 知识运用分析 | 3h | 逐概念映射到系统实现、展示 NER/RE/COT 等在实际运行中的输出 |
| 4.3 | 5 组问答结果整理 | 4h | 每样例：输入→IR 摘要→SVG 截图→分析讨论、不少于 5 组（可额外增加 1-2 组自主样例）、附上最终 SVG 代码（或截图 + 链接） |
| 4.4 | 局限性与改进讨论 | 2h | 当前方案局限性（基于 insights.md 元评估）、可能的改进方向（微调路线、多模态评估等） |
| 4.5 | 参考文献 + 附录 | 1h | OmniSVG、SVGen 等参考文献格式、附录：完整 prompt 设计、关键代码片段 |
| 4.6 | 最终审校与提交 | 1h | 全文通读、格式统一、文件打包 |

**Phase 4 产出**：
- 完整课程设计报告（`docs/report.md` 或 PDF）
- 最终版 5+ 样例 SVG 文件
- 项目源代码（含注释）

---

## 9. 五个必选样例策略

基于 insights.md §1.3 的样例分析和 §10.5 的审查补充，为每个样例制定详细的生成策略。

### 9.1 样例 1：大语言模型的基本原理

| 维度 | 策略 |
|------|------|
| **内容类型** | 概念解释 → 架构图 + 流程说明 |
| **推荐图表类型** | `architecture_diagram` (主) + `concept_explanation` (辅) |
| **NLP 知识重点** | 意图分类（识别为概念解释）、NER（抽取 Transformer、Self-Attention 等术语）、CoT（LLM 推理工作流展示） |
| **挑战识别** | Transformer 架构需要在单画面表达多层概念（嵌入→注意力→FFN→输出），且包含残差连接、LayerNorm 等复杂拓扑 |
| **应对策略** | 1) 采用分层架构图布局（自底向上或自左向右）；2) 使用色彩编码区分不同功能模块（嵌入=蓝、注意力=紫、FFN=绿）；3) 残差连接用虚线弧线表示；4) 每个模块配简短标注（2-3 词） |
| **Agent 1 注意事项** | `type_confidence` 可能 < 0.8（架构图 vs 概念图模糊），需要通过 Agent 4 的类型合理性检查做二次确认 |
| **Agent 2 注意事项** | 元素数量多（15+ 个模块 + 连接线），需要精心设计空间布局，确保阅读路径清晰 |
| **Agent 3 注意事项** | 残差连接（从底层绕到顶层）的路径绘制是技术难点，需要在 prompt 中提供路径绘制的示例 |

### 9.2 样例 2：通俗易懂地解释词向量（Word Embedding）的基本概念

| 维度 | 策略 |
|------|------|
| **内容类型** | 科普教学 → 空间映射图 + 语义关系示意 |
| **推荐图表类型** | `concept_map` (主) + `comparison_chart` (辅) |
| **NLP 知识重点** | 语义理解（将抽象概念"词向量"转化为可视化隐喻）、文本凝练（通俗化表述）、RE（词间语义关系的空间表达：相似词近、类比关系平行） |
| **挑战识别** | **这是 5 个样例中最大的挑战**（insights.md §10.5）：需要将高维语义空间降维表达为 2D 图示，且要兼顾通俗性（目标受众是"不懂 NLP 的人"） |
| **应对策略** | 1) **Few-shot 嵌入**：在 Agent 2 和 Agent 3 的 prompt 中嵌入词向量可视化的经典范式描述——"将语义相似的词在 2D 空间中放置得更近，用相同颜色标记同类词"；2) **降维隐喻**：用 2D 散点图隐喻高维空间的降维投影；3) **类比展示**：用 `king - man + woman ≈ queen` 的经典类比作为图示核心；4) **颜色编码**：同类词（动物、国家、动词）使用不同颜色区分 |
| **Agent 1 注意事项** | 这是一个科普任务，`target_audience` 应为 `general`，内容难度需适配 |
| **Agent 2 注意事项** | 布局应逻辑清晰：上部分=概念解释（什么是词向量），中部分=可视化展示（词的 2D 空间映射），下部分=类比示例（king-queen 关系） |
| **Agent 3 注意事项** | 坐标轴标签和散点标签需要特别仔细的布局计算，防止文本重叠；散点图 + 标注的组合是 SVG 生成中较复杂的场景 |

### 9.3 样例 3：中山大学的发展历程

| 维度 | 策略 |
|------|------|
| **内容类型** | 历史叙述 → 时间线/里程碑图 |
| **推荐图表类型** | `timeline` |
| **NLP 知识重点** | 信息检索/RAG（外部知识检索）、NER（抽取时间-事件对）、时序关系抽取、文本凝练（将历史描述浓缩为时间节点标注） |
| **挑战识别** | 需要 SYSU 历史事实（外部知识依赖），时间线布局需要合理安排 10+ 个时间节点 |
| **应对策略** | 1) **知识检索 + fallback**：Agent 1 触发 Web Search → Wikipedia/官网检索 SYSU 历史；如果搜索失败，使用 §5.2 中手工整理的 10 个关键时间节点作为 fallback；2) **时间线布局**：采用水平或垂直时间线设计，关键节点（1924 建校、2001 合并、2017 双一流、2020s 五校园）做视觉强调（更大的节点圆 + 不同颜色）；3) **时间轴规范**：非等距时间轴（早期事件稀疏、近期事件密集），需标注具体年份 |
| **Agent 1 注意事项** | `knowledge_gap.needs_external_knowledge` 必须为 `true`，`search_queries` 包含 "中山大学 历史 发展" "Sun Yat-sen University history" |
| **Agent 2 注意事项** | 时间线节点的垂直间距需均匀分布，年份标注的方式（节点一侧还是节点上方）需统一 |

### 9.4 样例 4：咖啡豆到一杯咖啡的完整生产链

| 维度 | 策略 |
|------|------|
| **内容类型** | 流程描述 → 垂直/水平流程图 |
| **推荐图表类型** | `process_diagram` / `flowchart` |
| **NLP 知识重点** | 流程关系抽取（序列关系识别：种植→采摘→烘焙→研磨→冲煮）、文本凝练（将每个步骤浓缩为图标+标签的形式） |
| **挑战识别** | **最安全的样例**（提示词信息充分，流程步骤明确），主要风险是设计质量平庸 |
| **应对策略** | 1) **垂直流程 + 图标**：采用自顶向下的垂直流程图，每个步骤用一个圆角矩形 + 简笔图标（咖啡豆→手→火焰→研磨器→咖啡杯）+ 步骤标签表示；2) **对抗平庸**：引入色彩渐变（从绿色种植到棕色咖啡的渐变过渡）、添加装饰性元素（蒸汽线条、咖啡豆散落）、使用精致的箭头连接和阴影效果；3) **可选变体**：如果时间允许，生成 2 个设计变体（垂直 vs 水平、扁平 vs 写实），选择较优者 |
| **Agent 3 注意事项** | 这是唯一明确要求"流程图"的样例，SVG 中应包含标准的流程节点和箭头连接；装饰性元素不能喧宾夺主 |

### 9.5 样例 5：YouTube vs TikTok vs Kuaishou 视频数量对比

| 维度 | 策略 |
|------|------|
| **内容类型** | 数据对比 → 柱状图/比例图 |
| **推荐图表类型** | `bar_chart` / `comparison_chart` |
| **NLP 知识重点** | 数值关系抽取（RE：YouTube = 10× TikTok, TikTok = 2× Kuaishou）、数值推理（自动计算相对值和比例尺）、结构化输出（将模糊的"X times more"转为精确的图表数据） |
| **挑战识别** | LLM 的数值推理可能不精确（比例尺选择不当），需要显式约束 |
| **应对策略** | 1) **数值预处理**：Agent 1 先将"10 倍"和"2 倍"转化为精确数值（设 Kuaishou = N → TikTok = 2N → YouTube = 20N → 自动选择 N 使图表美观）；2) **比例尺约束**：在 Agent 2 和 Agent 3 的 prompt 中显式要求"Y 轴必须从 0 开始，比例尺标注必须是整数"；3) **图例 + 数据标注**：每个柱子顶部标注具体倍数关系（文字 + 数值）；4) **备选方案**：如果柱状图效果不佳，生成比例图（三个圆面积比例 1:2:20 代表相对视频量）作为备选 |
| **Agent 1 注意事项** | `relations` 字段需准确提取数值关系：`{"quantifier": "10 times more than", "source": "YouTube", "target": "TikTok"}` |
| **Agent 3 注意事项** | SVG 柱状图需要精确的坐标计算（间距、柱宽、Y 轴刻度），如果发现 LLM 数值推理错误率高，考虑将柱状图的坐标计算逻辑外置为渲染器 |

---

## 10. NLP 知识深度展示计划

基于 insights.md §10.7.2 盲点二的洞察：**评审的首要标准是 NLP 知识运用深度，而非工程架构完美程度**。为此，有意识地设计以下"NLP 深度展示点"。

### 10.1 架构层面的 NLP 展示

| NLP 知识 | 架构体现 | 报告展示方式 |
|----------|----------|-------------|
| **多智能体协作** | 4 Agent 流水线 + 2 辅助 Agent | 架构图 + Agent 间通信协议分析 |
| **结构化知识表示** | Content IR + Layout IR 的 JSON Schema | 完整 Schema 展示 + 设计原理分析 |
| **Chain-of-Thought** | 每个 Agent 的 system prompt 包含 CoT 推理步骤 | 截取一个 Agent 的完整 CoT 输出示例 |
| **受控文本生成** | JSON Mode / Structured Output 约束 Agent 输出 | Schema 定义 + 约束效果对比 |
| **信息检索 + 生成** | 知识检索模块 + Agent 1 的知识缺口检测 | RAG 流程完整展示（以样例 3 为例） |

### 10.2 样例层面的 NLP 展示

在每个样例的报告中展示：

```
┌──────────────────────────────────────────────┐
│ 样例 X 的 NLP 分析                            │
│                                              │
│ 1. Agent 1 输出摘要                           │
│    · 意图分类: ___ (置信度: ___)               │
│    · 实体抽取: [entity1, entity2, ...]        │
│    · 关系识别: [rel1, rel2, ...]              │
│    · 知识检索: (如触发) 检索结果摘要            │
│                                              │
│ 2. NER 质量评估                               │
│    精确率: ___, 召回率: ___ (人工标注对比)       │
│                                              │
│ 3. RE 质量评估                                │
│    正确关系数 / 总关系数 = ___/___             │
│                                              │
│ 4. 关键 NLP 挑战                              │
│    · (此样例特有的 NLP 难点及解决方式)          │
│                                              │
│ 5. CoT 推理过程（关键步骤截取）                 │
│    Agent 2: "考虑到这是概念解释任务，我选择      │
│    分层架构图布局，自底向上展示..."              │
└──────────────────────────────────────────────┘
```

### 10.3 系统层面的定量评估

| 指标 | 计算方法 | 目标值 |
|------|----------|--------|
| NER 精确率 | 正确实体数 / Agent 1 输出实体总数 | ≥ 0.85 |
| NER 召回率 | 正确实体数 / 人工标注实体总数 | ≥ 0.80 |
| 意图分类准确率 | 正确分类数 / 总样例数 | ≥ 0.80 (4/5) |
| RE 准确率 | 正确关系数 / Agent 1 输出关系总数 | ≥ 0.80 |
| SVG 语法通过率 | XML 验证通过数 / 总生成次数 | ≥ 0.90 |
| 内容一致性评分 | Agent 4 的 `content_accuracy.score` 均值 | ≥ 7/10 |
| 平均修改轮数 | Agent 4→3 反馈次数的平均值 | ≤ 1.0 |

### 10.4 额外自主样例（可选加分项）

在 5 个必选样例之外，增加 1-2 个自主设计的测试样例以展示系统泛化能力：

| 自主样例建议 | 测试维度 | NLP 挑战 |
|-------------|----------|----------|
| "比较 CNN 和 Transformer 在图像处理中的优缺点" | 对比分析 | 多实体比较 + 结构化对比表 |
| "2024 年诺贝尔物理学奖颁给了谁？为什么？" | 时事知识 | 知识时效性 + 因果推理 |
| "解释 TCP 三次握手的过程" | 技术流程 | 时序关系 + 状态转换 |

---

## 11. 风险管理矩阵

基于 insights.md 第九章的风险分析和第十章元评估的优先级重排：

| # | 风险 | 概率 | 影响 | 优先级 | 应对策略 | 触发条件 | 负责人/阶段 |
|---|------|------|------|--------|----------|----------|------------|
| R1 | LLM 生成 SVG 语法错误 | 中 | 高 | 🔴 P0 | ① Agent 4 XML 解析验证 ② cairosvg 渲染测试 ③ Phase 2 引入自动修复建议 | 首次生成 XML 验证失败 | Phase 2 |
| R2 | 级联错误（Agent 1 类型误判 → 下游全错） | 中 | 高 | 🔴 P0 | ① Agent 1 增加 `type_confidence` 字段 ② Agent 4 增加图表类型合理性检查维度 ③ 置信度 < 0.8 时输出备选类型 | Agent 1 `type_confidence < 0.8` | Phase 1-2 |
| R3 | 样例 2（词向量）可视化效果差 | 中高 | 中 | 🔴 P0 | ① Few-shot 嵌入经典可视化范式描述 ② 多版本生成 + Agent 4 选择最优 ③ 设计 2-3 种可视化隐喻备选 | Phase 1 样例 2 评分 < 5/10 | Phase 3 |
| R4 | 样例 3 外部知识检索不准确 | 中 | 中 | 🟡 P1 | ① 手工整理 SYSU 关键时间节点 fallback ② 多源交叉验证 ③ 检索结果置信度标注 | Web 搜索返回结果与预期严重不符 | Phase 3 |
| R5 | 样例 5 数值推理错误 | 中 | 中 | 🟡 P1 | ① Agent 1 显式数值预处理 ② Agent 3 prompt 中的比例尺约束 ③ 生成后数值验证 | 柱状图比例明显不合理 | Phase 1-3 |
| R6 | Agent 间信息传递丢失 | 低 | 高 | 🟡 P1 | ① 严格的 JSON Schema 约束 ② 每个 Agent 输出前做 Schema 验证 ③ 全链路日志 | Schema 验证失败 | Phase 1-2 |
| R7 | Token 消耗超预算 | 中 | 中 | 🟢 P2 | ① 精简 prompt（去除冗余说明） ② 缓存中间结果（IR 可复用） ③ 设置 max_tokens 上限 | 单样例 Token > 预估值 2x | Phase 1 |
| R8 | 开发时间不足 | 低 | 高 | 🟢 P2 | ① PPT 输出为可选特性 ② 动态 SVG 动画为可选特性 ③ 自主样例为可选 ④ 优先保证 5 个必选样例质量 | Day 5 结束时进度 < 80% | Phase 3-4 |
| R9 | 多轮迭代陷入无限循环 | 低 | 中 | ⚪ P3 | ① Agent 4→3 反馈上限 2 轮 ② 2 轮后强制输出最优版本 | 某样例修改 > 2 轮且未改善 | Phase 2 |

---

## 12. 报告撰写大纲

### 12.1 报告结构（建议）

```
一、引言
    1.1 项目背景与目标
    1.2 相关工作（OmniSVG、SVGen 论文简述）
    1.3 报告结构概述

二、系统架构设计
    2.1 总体架构
    2.2 多智能体协作机制
        2.2.1 Agent 1: 内容分析器
        2.2.2 Agent 2: 布局规划器
        2.2.3 Agent 3: SVG 生成器
        2.2.4 Agent 4: 质量审核器
        2.2.5 辅助 Agent: 知识检索器
    2.3 中间表示（IR）设计
        2.3.1 Content IR Schema
        2.3.2 Layout IR Schema
    2.4 渲染验证闭环
    2.5 知识检索模块

三、关键技术实现
    3.1 LLM API 调用与结构化输出
    3.2 Prompt Engineering 策略
    3.3 渲染验证实现
    3.4 流水线编排与迭代控制

四、NLP 知识运用分析
    4.1 NLP 概念与系统组件映射
    4.2 命名实体识别（NER）在 Agent 1 中的运用
    4.3 关系抽取（RE）在内容分析中的应用
    4.4 Chain-of-Thought（CoT）在 Agent 推理中的体现
    4.5 信息检索增强生成（RAG）的实现
    4.6 结构化知识表示与受控生成
    4.7 自动评估与错误分析

五、实验结果与分析
    5.1 测试样例概览
    5.2 样例 1: 大语言模型的基本原理
        [输入 → Agent 1 IR 摘要 → Agent 2 布局 → 最终 SVG + 分析]
    5.3 样例 2: 词向量的基本概念
        [...]
    5.4 样例 3: 中山大学的发展历程
        [...]
    5.5 样例 4: 咖啡生产链流程图
        [...]
    5.6 样例 5: YouTube/TikTok/Kuaishou 数据对比
        [...]
    5.7 [可选] 额外自主样例
    5.8 系统整体评估
        5.8.1 定量评估（NER/RE 准确率、SVG 语法通过率等）
        5.8.2 定性分析（各维度评分分布）
        5.8.3 消融实验（去掉某个 Agent 对质量的影响）

六、讨论
    6.1 系统局限性
    6.2 与参考方法的比较
    6.3 改进方向
        6.3.1 微调路线（SVGen-like）
        6.3.2 多模态视觉评估
        6.3.3 渲染引擎集成
        6.3.4 动态 SVG 动画与交互

七、结论

八、参考文献

附录
    A. 完整 System Prompt 设计
    B. 关键代码片段
    C. 全部生成 SVG 代码/截图
```

---

## 附录 A：关键设计决策备忘录

本实施计划在以下关键点上做出了有意识的决策取舍，供开发过程中参考：

| 决策点 | 我们的选择 | 被否决的方案 | 否决理由 |
|--------|-----------|-------------|----------|
| 渲染引擎 | LLM 直接生成 + 结构化验证 | 完整 IR→渲染器 | IR Schema 维护成本高、灵活性受限（insights.md §10.1） |
| 视觉验证 | 结构化规则检查（cairosvg + XML + 坐标） | 多模态模型评估 | Self-evaluation bias、渲染环境差异、成本高（§10.2） |
| 布局匹配 | 比例布局 + Agent 3 最终调整权 | Agent 2↔3 尺寸协商反馈循环 | 架构过重、存在更轻量替代（§10.3） |
| Phase 1 Agent 2 | Phase 1 跳过 Agent 2 | Phase 1 引入简化 Agent 2 | Phase 1 目标是快速验证，3 Agent 调试效率 > 4 Agent（§10.4） |
| 级联容错 | Agent 1 置信度 + Agent 4 类型检查 | 低置信度并行备选生成 | 5 样例中仅 2 个有类型模糊风险，并行成本过高（§10.6） |
| NLP 深度 | 主动设计"NLP 展示点" | 依赖架构自然体现 | 课程评分标准为 NLP 深度而非架构完美（§10.7.2） |

---

> **文档维护**：本实施计划应在每个 Phase 结束时根据实际进度和发现进行回顾性更新。Phase 完成后在对应任务上标记 `[x]`，并将实际耗时与预估值对比，以便后续 Phase 调优。
