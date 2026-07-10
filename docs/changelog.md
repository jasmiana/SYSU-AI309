# Changelog

> Multi-Agent SVG/PPT System - Development Log

---

## Phase 2: 质量提升 — 2026-07-10

**目标**: 完整的 4 Agent 流水线 + 渲染验证闭环 + 迭代精炼反馈循环。

### 完成内容

| 任务 | 文件 | 说明 |
|------|------|------|
| Agent 1 key_points修复 | agent1_system.txt | 新增CoT步骤5 + Critical Rules块, 杜绝空数组 |
| Agent 2 布局规划器 | agent2_system.txt, layout_planner.py | 比例布局, 4套配色, 6级排版, Layout IR Schema |
| Agent 4 质量审核器 | agent4_system.txt, quality_reviewer.py | 6维审查, 结构化检查解读, 修改建议格式 |
| 渲染验证模块 | rendering/validator.py | XML语法, 坐标越界, 元素重叠, WCAG对比度 |
| 完整流水线集成 | orchestrator.py, svg_coder.py, main.py | 4 Agent串联 + Agent4→3反馈循环(max 2轮) |

### 端到端验证 (sample4)

Agent1 35.9s -> Agent2 56.5s -> Agent3(r1) 195.9s -> Validator 2ms -> Agent4(r1) 59.6s NOT Passed -> Agent3(r2) 134.0s -> Validator 4ms -> Agent4(r2) 39.2s PASSED (8.8/10)
Total: 521.1s, 2 refinement rounds. Feedbacks loop successfully improved the SVG.

### Agent 1 key_points验证

Phase 1: key_points = [] (sample1为空)
Phase 2: key_points = [5条详细信息] (每条为完整中文陈述句)

---




### 补充修复: cairosvg 渲染验证 + Layout IR JSON 重试 (2026-07-10)

**cairosvg 集成**:
- Windows: GTK3 Runtime 安装后, 通过 ctypes.CDLL 预加载 libcairo-2.dll
  (路径: C:/Program Files/GTK3-Runtime Win64/bin/)
- validator.py 启动时自动检测 DLL, 可用则 render_ok=true, 否则优雅降级
- 已验证 sample5 SVG 渲染: render_ok=true

**Layout IR JSON 解析修复** (sample1 根因):
- 根因: Agent 2 输出 8805 chars JSON, design_notes 中文长文本导致
  max_tokens 截断, JSON 字符串未闭合
- 修复 1: Agent 2 max_tokens 16384 -> 32768 (预防截断)
- 修复 2: BaseAgent.run() JSON 解析失败后自动重试一次,
  带 keep design_notes under 200 chars 指令
- 修复 3: 新增 _fix_truncated_json() 尝试闭合截断的字符串和括号

**对比度检查精准化**:
- 仅检查 <text> 元素的 fill 颜色 (之前错误地将 rect 填充色也纳入检查)

### Phase 2.6: Agent 4 误判修复 (2026-07-10)

**问题发现**: sample5 (数据对比柱状图) 的 SVG 实际质量良好（柱状图坐标精确、无重叠），
但 Agent 4 给出 score 4.5 的错误低分，声称存在"柱子坐标错误"和"严重重叠"。

**根因分析**:
1. SVG 截断: Agent 4 仅接收 SVG 前 3000 字符，sample5 SVG 长 5876 字符，
   实际柱状图部分被截断，Agent 4 基于不完整信息推理出虚假问题
2. 重叠误报: 图表背景 rect (150,150,600,600) 与内部柱子的包含关系被检测器
   标记为 overlap，导致 Agent 4 误判为布局错误
3. Agent 4 放大: 从 structured_check 的 3 个 overlap 条目 + 截断 SVG，
   Agent 4 推断出"严重重叠"和"坐标错误"等完全不存在的问题

**修复内容**:
- quality_reviewer.py: 移除 SVG 3000 字符截断，Agent 4 现接收完整 SVG
- quality_reviewer.py: max_tokens 8192 -> 16384（适应完整 SVG 输入）
- validator.py: overlap 检测增加包含关系过滤（_is_containment），
  图表背景包含柱子不再误报为重叠
- agent4_system.txt: 增加提示"不要在 SVG 代码中推理出不存在的问题"

**修复验证**:
- sample5 重新生成: 一次通过，score 9.0（之前: 2轮精炼后仍 4.5）
- 最终 5/5 全部通过，平均分 8.7（修复前: 4/5 通过，平均 7.8）

### Phase 2.5: 全样例生成与结果分析 (2026-07-10)

| 样例 | 评分 | 通过 | 精炼轮数 | 耗时 |
|------|------|------|----------|------|
| sample1 (LLM原理) | 8.0 | True | 1 | 240s |
| sample2 (词向量) | 8.5 | True | 1 | 308s |
| sample3 (SYSU历史) | 9.2 | True | 2 | 427s |
| sample4 (咖啡链) | 8.8 | True | 2 | 521s |
| sample5 (数据对比) | 4.5 | False | 2 | 314s |

运行中代码修复:
1. Layout IR JSON解析增强 (extract_json_from_response) — trailing comma/balanced braces
2. Agent 2 max_tokens 8192 -> 16384
3. MAX_REFINEMENT_ROUNDS 2 -> 1 (避免thinking模式下超时)
4. sample5 柱状图坐标错误确认为LLM数值推理固有问题 (Phase 3 确定性渲染器解决)

详细结果: docs/results.md

---

## 补充更新：DeepSeek 思考模式配置 — 2026-07-10

**目标**：将主模型切换至 `deepseek-v4-pro`，备选 `deepseek-v4-flash`，启用 DeepSeek 原生思考模式 + high reasoning effort。

**变更清单**：

| 文件 | 变更 |
|------|------|
| `src/utils/config.py` | 主模型 `deepseek-v4-pro`，备选 `deepseek-v4-flash`；新增 `THINKING_ENABLED`、`REASONING_EFFORT` 字段；新增 `get_thinking_config()` 方法返回 `extra_body` 参数 |
| `.env.example` | 新增 `DEEPSEEK_FALLBACK_MODEL`、`THINKING_ENABLED`、`REASONING_EFFORT` 字段 |
| `src/agents/base_agent.py` | `create()` 调用增加 `extra_body=config.get_thinking_config()` |
| `src/agents/svg_coder.py` | `max_tokens` 从 16384 → 32768（思考 tokens 消耗预算） |
| `docs/implementation_plan.md` | 更新 §7.1 技术栈选型表 |

**思考模式对性能的影响**（以 sample4 咖啡链为例）：

| 指标 | 无思考模式 | 思考模式 enabled | 变化 |
|------|-----------|-----------------|------|
| Agent 1 耗时 | ~5.6s | ~18.6s | +3.3x |
| Agent 3 耗时 | ~20.7s | ~120.1s | +5.8x |
| 总耗时 | ~26.4s | ~138.7s | +5.3x |
| 置信度 | 0.95 | 0.99 | +0.04 |
| SVG 大小 | 9.0 KB | 6.5 KB | 更精炼 |

**评估**：思考模式显著增加了延迟（Agent 3 尤其明显，从 20s → 120s），但换来更深层的推理。SVG 更精炼，设计决策更有依据。对于课程设计项目，质量优先于速度，此配置是合适的。

---

## Phase 1: 核心流水线搭建 — 2026-07-09

**目标**：从用户 prompt → 结构化分析 → SVG 代码 → 输出文件，跑通最简链路。

**范围**：Agent 1（内容分析器）+ Agent 3（SVG 生成器）的直接流水线，暂不包含 Agent 2（布局规划器）、Agent 4（质量审核器）、渲染验证、知识检索。

---

### 任务 1.1：项目环境搭建 ✅

**完成内容**：
- 创建完整项目目录结构（`src/agents/`, `src/pipeline/`, `src/prompts/`, `src/rendering/`, `src/knowledge/`, `src/utils/`, `tests/`, `outputs/`）
- 编写 `requirements.txt`（核心依赖：anthropic, python-dotenv, cairosvg, Pillow, wikipedia-api, python-pptx）
- 编写 `.env.example` 模板文件
- 搭建 conda 环境 `nlp` (Python 3.11.15)，安装核心依赖
  - anthropic SDK v0.116.0 已安装
  - python-dotenv 已安装

**文件清单**：
```
project3/
├── requirements.txt
├── .env.example
├── main.py
├── src/
│   ├── __init__.py
│   ├── agents/__init__.py
│   ├── pipeline/__init__.py
│   ├── prompts/__init__.py
│   ├── rendering/__init__.py
│   ├── knowledge/__init__.py
│   └── utils/__init__.py
└── tests/
```

**状态**：✅ 完成

---

### 任务 1.2：实现 base_agent.py ✅

**完成内容**：
- 实现 `BaseAgent` 抽象基类，提供：
  - Anthropic SDK API 调用封装 (`call_llm`)
  - JSON 结构化输出解析 (`extract_json_from_response`)
  - 重试机制（最多 3 次，指数退避：2s/4s/8s）
  - 超时处理
  - 支持 `run()` (返回 JSON) 和 `run_raw()` (返回原始文本) 两种模式
- 实现关键实用函数：
  - `extract_json_from_response()`: 从 LLM 响应中提取 JSON（支持纯 JSON、markdown 代码块、嵌入式 JSON）
  - `strip_svg_markdown()`: 从 LLM 响应中清理 SVG 代码（移除 markdown 包装）

**文件清单**：
```
src/agents/base_agent.py
```

**测试结果**：✅ 通过 3/3 项测试
- JSON extraction (纯 JSON、markdown 代码块、无语言标注代码块)
- SVG markdown stripping (markdown 包裹、裸 SVG)
- IR validation (有效 IR、无效 IR 捕获)

**状态**：✅ 完成

---

### 任务 1.3：实现 Agent 1（内容分析器）✅

**完成内容**：
- 编写 `agent1_system.txt` — 中文 system prompt，包含完整的 5 步 CoT 分析流程：
  1. 意图分类（6 种类型：concept_explanation, 科普, process_flow, data_comparison, timeline, architecture_diagram）
  2. 实体抽取（NER：person, organization, location, term, number, date）
  3. 关系识别（RE：comparison, hierarchy, sequence, causality, temporal）
  4. 信息完整性评估（知识缺口检测）
  5. 目标受众分析
- 定义 Content IR JSON Schema（完整 Schema 含 intent, entities, relations, content_summary, knowledge_gap, chart_type）
- 实现 `ContentAnalyzer` 类，继承 `BaseAgent`
  - 低温参数 (temperature=0.3) 保证分析一致性
  - `analyze()` 方法接收原始提示词，返回 Content IR

**文件清单**：
```
src/prompts/agent1_system.txt  (2841 chars)
src/agents/content_analyzer.py
```

**状态**：✅ 完成

---

### 任务 1.4：实现 Agent 3（SVG 生成器）✅

**完成内容**：
- 编写 `svg_guidelines.txt` — SVG 设计规范参考文档，涵盖：
  - XML 编码规范（根元素、标签闭合、颜色、文本处理）
  - 设计规范（画布留白、圆角矩形、箭头连接线、渐变、阴影）
  - 四套配色方案（现代科技感、自然清新感、学术稳重感、数据可视化）
  - 排版规范（6 级字号体系）
  - 文本凝练规则
  - 常见设计模式代码片段（标题栏、信息卡片、流程节点、柱状图）
- 编写 `agent3_system.txt` — SVG 代码生成器 system prompt
  - 设计策略（6 种图表类型的定制化指导）
  - 美观原则
  - 特殊场景处理（数值关系、多步骤流程、历史时间线）
- 实现 `SVGCoder` 类，继承 `BaseAgent`
  - 中温参数 (temperature=0.5) 平衡创意与一致
  - 更长的 max_tokens (16384) 适应 SVG 代码长度
  - `build_user_prompt()` 从 Content IR 构建丰富的生成指令
  - `generate()` 方法输出清洁 SVG XML

**文件清单**：
```
src/prompts/svg_guidelines.txt  (3586 chars)
src/prompts/agent3_system.txt   (1928 chars)
src/agents/svg_coder.py
```

**状态**：✅ 完成

---

### 任务 1.5：实现流水线编排器 ✅

**完成内容**：
- 实现 `Phase1Pipeline` 类：
  - 串联 Agent 1 → Agent 3
  - 全链路日志（PipelineLogger）
  - 中间结果自动保存（Content IR JSON + SVG 文件）
  - 执行元数据记录（耗时、意图、置信度等）
- 实现 `ir_schema.py`：
  - Content IR、Layout IR、Review IR 的完整 Schema 定义
  - `validate_content_ir()` 验证函数
- 实现 `main.py` 入口：
  - CLI 参数解析（--sample, --model, --list）
  - 5 个必选样例的定义
  - 单样例和批量运行模式
- 实现工具模块：
  - `config.py`: 环境变量配置管理（支持 .env 文件）
  - `logger.py`: 结构化日志（JSON trace 输出）
  - `file_manager.py`: 输出文件管理（按样例分目录）

**文件清单**：
```
src/pipeline/orchestrator.py
src/pipeline/ir_schema.py
src/utils/config.py
src/utils/logger.py
src/utils/file_manager.py
main.py
```

**测试结果**：✅ 通过 6/6 项测试
- Module imports
- JSON extraction
- SVG stripping
- IR validation
- Prompt loading (Agent 1: 2841 chars, Agent 3: 1928 chars, Guidelines: 3586 chars)
- File manager (SVG save, IR save)

**状态**：✅ 完成

---

### 任务 1.6：5 样例初版生成与评估 ⏳

**阻塞项**：需要用户配置 API Key。

**操作步骤**：
```bash
# 1. 创建 .env 文件
cp .env.example .env

# 2. 编辑 .env，填入 Anthropic API Key
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
# ANTHROPIC_MODEL=claude-sonnet-4-20250514  （可选）

# 3. 运行单样例测试
python main.py --sample sample4

# 4. 运行全部 5 样例
python main.py
```

**预期产出**：
- `outputs/sample1_llm_principles/` — 大语言模型基本原理 SVG
- `outputs/sample2_word_embedding/` — 词向量概念 SVG
- `outputs/sample3_sysu_history/` — 中山大学发展历程 SVG
- `outputs/sample4_coffee_chain/` — 咖啡生产链流程图 SVG
- `outputs/sample5_video_comparison/` — 视频数量对比柱状图 SVG

**状态**：✅ 已完成（见下方 Phase 1.6 补充记录）

---

### 补充：DeepSeek API 迁移（2026-07-09）✅

因用户持有 DeepSeek API Key，将全部 LLM 调用从 Anthropic SDK 迁移至 DeepSeek API：

**变更清单**：
- `requirements.txt`: `anthropic` → `openai` (DeepSeek 兼容 OpenAI SDK)
- `.env.example`: 字段更新为 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL`
- `src/utils/config.py`: 移除 Anthropic/OpenAI 字段，新增 DeepSeek 配置
- `src/agents/base_agent.py`: 使用 `openai.OpenAI` 客户端，`base_url` 指向 `https://api.deepseek.com`，system prompt 以 `role: "system"` 消息传递（OpenAI 格式）
- `tests/`: 更新测试引用
- `docs/implementation_plan.md`: 更新 §7.1 核心技术栈选型

**技术细节**：
- DeepSeek 模型 `deepseek-chat`（DeepSeek-V3）用于所有 Agent
- API 通过 OpenAI 兼容接口调用：`client.chat.completions.create(model="deepseek-chat", messages=[...])`
- 所有现有 prompt 和 IR Schema 保持不变，仅调用层替换

---

### 任务 1.6：5 样例初版生成与评估 ✅

**运行日期**：2026-07-10

**运行结果**：

| 样例 | 意图分类 | 图表类型 | 置信度 | 耗时 | SVG 大小 | XML 验证 |
|------|----------|----------|--------|------|----------|----------|
| sample1 (LLM原理) | concept_explanation | architecture_diagram | 0.95 | 28.6s | 10.6 KB | ✅ 有效 |
| sample2 (词向量) | concept_explanation | concept_map | — | 30.6s | 12.9 KB | ✅ 有效 |
| sample3 (SYSU历史) | timeline | timeline | — | 23.7s | 7.6 KB | ✅ 有效 |
| sample4 (咖啡链) | process_flow | flowchart | 0.95 | 26.4s | 9.0 KB | ✅ 有效 |
| sample5 (数据对比) | data_comparison | comparison_chart | 0.95 | 24.9s | 8.4 KB | ✅ 有效 |

**总计**：5/5 全部通过，总耗时 ~134s，所有 SVG 均为有效 XML。

**IR 质量评估**：
- **NER 精确率**：5/5 样例正确识别核心实体（LLM、Transformer、YouTube/TikTok/Kuaishou、咖啡生产步骤等）
- **意图分类准确率**：5/5 分类正确（concept_explanation, concept_explanation, timeline, process_flow, data_comparison）
- **关系抽取**：sample5 数值关系抽取精准（"10 times more", "2 times more"），sample1 正确识别层级关系
- **知识缺口检测**：sample3 正确触发知识检索需求，sample4/sample5 正确判断无需外部知识

**已知问题（Phase 2 改进方向）**：
- sample3（SYSU 历史）：缺乏 Web 搜索，依赖 LLM 内置知识，时间节点可能不完全准确——Phase 3 集成知识检索后将改善
- sample2（词向量）：最复杂的视觉设计，需在 Phase 2 引入 Agent 2 布局规划 + Agent 4 审核后进一步优化
- 所有 SVG 为"初版"质量，Phase 2 引入 Agent 2（布局规划器）和 Agent 4（质量审核器 + 迭代精炼）后将显著提升视觉质量

---

## Phase 1 总结

### 实现统计

| 指标 | 数值 |
|------|------|
| 源代码文件数 | 17 个 |
| Python 代码行数 | ~800 行 |
| Prompt 文本量 | ~8,300 chars（3 个 prompt 文件） |
| Agent 数量 | 2 个（ContentAnalyzer + SVGCoder） |
| 辅助模块 | 3 个（config, logger, file_manager） |
| 单元测试覆盖 | 6 项全部通过 |

### 关键设计决策记录

1. **Phase 1 跳过 Agent 2（布局规划器）**：按照实施计划 §8.2 的策略，Phase 1 优先跑通端到端链路（Agent 1 → Agent 3），布局规划将在 Phase 2 引入。

2. **Agent 3 拥有布局最终决定权**：SVG 生成器在 prompt 中被明确告知可以基于实际文本需求微调坐标和尺寸，这从架构上规避了"尺寸不匹配"问题，不需要在 Phase 2 引入 Agent 2↔3 反馈循环。

3. **使用 OpenAI Python SDK 调用 DeepSeek API**：DeepSeek API 完全兼容 OpenAI 接口格式，通过 `openai.OpenAI(base_url="https://api.deepseek.com")` 接入。System prompt 以 `role: "system"` 消息传递。JSON Schema 约束通过 prompt 指令实现（而非 function calling）。

4. **Prompt 文件外置**：每个 Agent 的 system prompt 存储在独立 `.txt` 文件中，支持不修改代码即可迭代优化 prompt。

### 下一步计划（Phase 2）

1. 实现 Agent 2（布局规划器）+ `agent2_system.txt`
2. 实现渲染验证模块（cairosvg + XML 验证 + 坐标/重叠/对比度检查）
3. 实现 Agent 4（质量审核器）+ `agent4_system.txt`
4. 完整 4 Agent 流水线联调 + Agent 4→3 反馈循环
5. 基于 Phase 1 生成结果进行 Prompt Engineering 优化

---

> **下次更新**：Phase 2 完成后
