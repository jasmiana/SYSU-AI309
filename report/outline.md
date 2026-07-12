# 综合报告大纲：基于多智能体的静态 SVG 信息图自动生成系统

> **课程**: 自然语言处理课程设计
> **学校**: 中山大学
> **日期**: 2026 年 7 月
> **最终版本**: A+B+D 创意解放 + 热修复优化

---

## 摘要

- 项目目标：构建多智能体协作系统，从自然语言提示词自动生成高质量静态 SVG 信息图
- 技术路线：4 Agent 流水线 + 知识检索 + 渲染验证 + 反馈闭环
- 核心成果：5/5 必选样例全部通过，均分 8.6/10，NER Micro F1 = 0.678，RE Micro F1 = 0.302
- 关键发现：多智能体架构以创意换可控性——baseline（单次直出）视觉更优但缺知识准确性与可审查性；通过 A+B+D 创意解放方案弥合差距

**关键词**: 多智能体系统；SVG 生成；命名实体识别；关系抽取；思维链推理；知识增强生成

---

## 第一章 引言

### 1.1 项目背景
- NLP 课程设计任务概述（引用 `docs/prd.md`）
- 从自然语言到可视化内容的跨模态映射挑战
- 多智能体架构在复杂生成任务中的潜力

### 1.2 问题定义
- 输入：自然语言提示词（中文/英文/中英混合）
- 输出：静态 SVG 信息图
- 核心难点：布局规划、视觉编码、文本凝练、SVG 语法正确性、美学质量、内容保真度

### 1.3 相关工作
- OmniSVG（NeurIPS 2026）：SVG 参数化 Token + VLM 端到端生成
- SVGen（ACM MM 2025）：渐进式课程学习 + CoT 标注 + 轻量 LLM 微调
- 本项目的定位：API 调用路线的多 Agent 协作方案，不依赖大规模训练

### 1.4 五个必选测试样例
| # | 样例 | 内容类型 | 图表类型 | 语言 |
|---|------|----------|----------|------|
| 1 | 大语言模型的基本原理 | 概念解释 | 架构图 | 中文 |
| 2 | 通俗易懂地解释词向量 | 科普教学 | 概念图 | 中文 |
| 3 | 中山大学的发展历程 | 历史叙述 | 时间线 | 中文 |
| 4 | 咖啡豆到一杯咖啡的完整生产链 | 流程展示 | 流程图 | 中文 |
| 5 | YouTube vs TikTok vs Kuaishou 视频数量对比 | 数据对比 | 柱状图 | 英文 |

### 1.5 报告结构概述
- 简述各章内容与逻辑关系

---

## 第二章 系统架构设计

### 2.1 设计哲学与架构决策
- NLP 深度优先、渐进式实施、务实的复杂度控制、IR 作为通信协议（引用 `docs/implementation_plan.md` §1.3）
- 架构决策记录（ADR）：Agent 数量、通信格式、SVG 生成方式、知识检索触发、迭代上限、渲染验证策略（引用 §2.2）

### 2.2 总体架构概览
- A（多 Agent 流水线）+ B（选择性 IR）+ E（知识增强）混合架构
- 完整架构图：用户 Prompt → Agent 1 → 知识检索 → Agent 2 → Agent 3 → 渲染验证 → Agent 4 → 反馈闭环 → 最终 SVG
- 数据流与信息传递：Content IR → Layout IR → SVG → Review IR

### 2.3 Agent 1：内容分析器（Content Analyzer）
- 职责：意图分类（6 类型）、NER（6 实体类型）、RE（5 关系类型）、知识缺口检测、图表类型推荐
- NLP 知识体现：意图识别、命名实体识别、关系抽取、指代消解、信息检索
- System Prompt 设计：5 步 CoT 分析流程 + 实体抽取强化（P0 修复）
- 输出 Schema：Content IR 完整结构
- 关键设计：`type_confidence` 字段（级联错误防护）、`knowledge_gap` 触发机制

### 2.4 Agent 2：布局规划器（Layout Planner）
- 职责：图表选型、比例布局规划、自主配色设计、视觉层次定义
- NLP 知识体现：结构化知识表示、语义到空间的映射、多模态信息组织
- 设计方案演进：
  - Phase 2 原始版：4 套固定配色模板 → 机械选择
  - A+B+D 优化版：去模板化，自主设计 + 论证（方案 A），每个颜色选择有内容理由
- 输出 Schema：Layout IR（比例布局 `x_pct`/`y_pct`，非绝对像素）
- 关键设计：比例布局规避尺寸不匹配问题；标题长度硬约束（热修复）

### 2.5 Agent 3：信息图设计师（SVG Coder）
- 职责：将 Content IR + Layout IR 转化为完整 SVG XML 代码
- NLP 知识体现：受控文本生成、文本摘要/凝练、代码生成（跨模态映射）
- 角色演进：
  - Phase 2 原始版：「SVG Coder」— Layout IR 的忠实执行者
  - A+B+D 优化版：「信息图设计师」— Layout IR 降级为"设计建议"，Agent 3 拥有创作自主权（方案 B）
- System Prompt 设计：SVG 编码规范 + 设计规范 + 文本凝练规则 + 创意充实清单（5 项）+ 自检清单（11 项）+ 数值推理三步公式
- 热修复：标题长度硬约束、XML 特殊字符与 emoji 安全

### 2.6 Agent 4：质量审核器（Quality Reviewer）
- 职责：多维度审查生成的 SVG，决定通过或触发精炼
- NLP 知识体现：自动评估、文本蕴含/一致性检测、错误分析与诊断
- 审查维度演进：
  - Phase 2 原始版：6 维度（syntax, layout, content_accuracy, chart_type, information_completeness, aesthetics）
  - A+B+D 优化版：新增第 7 维度 `creativity_density`（方案 D），推动"进攻性"创意质量评估
- 输入增强：不仅审查 SVG 文本，还接收结构化检查报告（rendering validator 输出）
- 反馈流程：pass → 输出；fail → Agent 3 修改（max 1 轮）
- 热修复：layout 维度新增标题溢出检查项（填补 Agent 4 盲区）

### 2.7 辅助模块：知识检索器（Knowledge Retriever）
- 两-tier 检索策略：Wikipedia API + 本地 Fallback 知识库
- Fallback DB：3 个预设主题（SYSU 历史 12 节点、词向量可视化 3 范式、LLM 核心概念）
- 触发条件：Agent 1 判断 `knowledge_gap.needs_external_knowledge == true`
- 检索效果：3/5 样例触发，100% Fallback DB 命中，~5ms 零开销

### 2.8 渲染验证闭环（Rendering Validator）
- 设计理念：分阶段引入——结构化规则检查（Phase 2），暂不引入多模态评估
- 4 项确定性检查：
  1. XML 语法验证（`xml.etree.ElementTree` + `cairosvg` 渲染测试）
  2. 坐标越界检查（viewBox 边界验证）
  3. 元素重叠检测（含包含关系过滤 `_is_containment`）
  4. WCAG 颜色对比度检查（文本 vs 背景）
- Windows 集成：ctypes.CDLL 预加载 GTK3 `libcairo-2.dll`
- 结构化检查报告嵌入 Agent 4 输入

---

## 第三章 关键技术实现

### 3.1 LLM API 调用与结构化输出
- DeepSeek API 集成（OpenAI 兼容 SDK）
- 思考模式（Thinking Mode）配置：`extra_body={"thinking": {"type": "enabled"}}`, `reasoning_effort=high`
- 模型选择：`deepseek-v4-flash` 为主（thinking enabled），`deepseek-v4-pro` 备选
- 重试机制：3 次指数退避（2s/4s/8s）
- JSON 提取与解析：支持纯 JSON、markdown 代码块、平衡括号提取、截断 JSON 修复

### 3.2 Prompt Engineering 策略
- 5 个 Prompt 文件的分工与协作（`agent1-4_system.txt` + `svg_guidelines.txt`）
- Prompt 优化历程：
  - P0 修复：Agent 1 实体抽取强化（entities 10→16, relations 5→14）+ Agent 3 数值推理公式
  - A+B+D 创意解放：Agent 2 去模板化 + Agent 3 角色重定义 + Agent 4 创意密度维度
  - 热修复：标题溢出三层防御链（Agent 2→3→4）+ XML 特殊字符安全
- 优化方法论：识别问题 → 定位根因 → 单样例验证 → 全样例回归

### 3.3 中间表示（IR）设计
- Content IR Schema：intent / entities / relations / content_summary / knowledge_gap / chart_type
- Layout IR Schema：canvas / color_scheme / typography / sections / elements / connections / design_notes
- Review IR Schema：pass / overall_score / dimensions / needs_regeneration / specific_suggestions
- IR 设计原则：人类可读、渐进细化、约束宽松、可扩展
- IR 在 Agent 间通信中的角色：结构化知识的载体与协议

### 3.4 流水线编排与迭代控制（Orchestrator）
- 完整流水线：Agent 1 → Knowledge Retrieval → Agent 2 → Agent 3 → Rendering Validator → Agent 4 → [反馈闭环]
- 迭代策略：MAX_REFINEMENT_ROUNDS = 1（基于消融实验结果）
- 防御链设计：标题溢出（Agent 2 规划 → Agent 3 自检 → Agent 4 兜底）
- 全链路日志：JSON trace 输出，支持调试与报告分析

### 3.5 PPT 导出（可选功能）
- python-pptx 生成 16:9 宽屏演示文稿
- SVG → PNG 通过 cairosvg 实时转换
- 每样例一页幻灯片 + 汇总页

### 3.6 Baseline 对照实验
- 设计目的：量化多 Agent 架构的质量提升幅度
- 实现：单次 LLM 调用（thinking disabled），无 IR、无知识检索、无验证、无反馈
- 与 Multi-Agent 对比：快 11×（214s vs 19.6s per sample），但缺知识准确性与可审查性

---

## 第四章 NLP 知识运用分析

### 4.1 NLP 概念与系统组件映射总览
| NLP 概念 | 系统组件 | 实现方式 |
|----------|----------|----------|
| 命名实体识别（NER） | Agent 1 | 6 类型实体抽取 + 结构化输出 |
| 关系抽取（RE） | Agent 1 | 5 类型关系识别 + 三元组输出 |
| 意图分类 | Agent 1 | 6 类型意图分类 + 置信度分数 |
| Chain-of-Thought（CoT） | Agent 1/2/3/4 | 各 Agent 的 System Prompt 含显式推理步骤 |
| 信息检索增强生成（RAG） | Knowledge Retriever | Wikipedia + Fallback DB → Content IR |
| 结构化知识表示 | IR Schema | Content IR + Layout IR 的 JSON Schema |
| 受控文本生成 | Agent 3 | JSON Schema 约束 + Prompt 指令约束 |
| 文本摘要/凝练 | Agent 3 | 文本凝练规则（标题 ≤20 字、标签 ≤8 字） |
| 自动评估 | Agent 4 | 7 维度量化评分 + 结构化检查报告 |
| 多智能体协作 | Pipeline Orchestrator | 任务分解、消息传递、反馈闭环 |

### 4.2 命名实体识别（NER）在 Agent 1 中的运用
- 实体类型体系：person / organization / location / term / number / date
- Ground Truth 标注方案：5 样例 × 人工标注（共 52 实体）
- 评估方法：名称完全匹配（大小写不敏感），Micro/Macro/Per-sample 三级汇总
- 实验结果：NER Micro F1 = 0.678（A+B+D+热修复后），较 Phase 3 基线提升 +67%
- 错误分析：遗漏隐含实体（FN）、实体名格式偏差（FP+FN）、非实体误标（FP）
- 优化历程：P0 实体抽取强化（主动补充原则 + 强制自查 + 输出质量参考示例）

### 4.3 关系抽取（RE）在内容分析中的应用
- 关系类型体系：comparison / hierarchy / sequence / causality / temporal
- Ground Truth 标注方案：5 样例 × 人工标注（共 37 关系）
- 评估方法：(source, target, type) 三元组精确匹配
- 实验结果：RE Micro F1 = 0.302（A+B+D+热修复后）
- 错误分析：target 混入非实体名（主要 FP 来源）、遗漏隐式关系（FN）
- 评估脚本关键设计：仅评估结构化字段 `relations[]`，不扫描自由文本

### 4.4 Chain-of-Thought（CoT）在 Agent 推理中的体现
- Agent 1 CoT：5 步分析流程（意图分类 → 实体抽取 → 关系识别 → 知识缺口 → 受众分析）
- Agent 2 CoT：色彩情感基调 → 信息层次映射 → 阅读路径设计 → 渐变策略论证
- Agent 3 CoT：自检清单 11 项（数值比例 ×4 + 对比度 ×3 + 定位 ×3 + 完整性 ×2）
- Agent 4 CoT：7 维度逐项评估 → 综合判定 → 修改建议优先级排序
- Thinking Mode 的贡献与代价：质量提升 vs 延迟增加（Agent 3 延迟 +5.8×）

### 4.5 信息检索增强生成（RAG）的实现
- 检索触发机制：Agent 1 输出 `knowledge_gap.needs_external_knowledge == true`
- 检索架构：本地 Fallback DB（低延迟、高可靠）→ Wikipedia API（广覆盖）
- 三个样例的知识增强效果：
  - Sample 1（LLM 原理）：Transformer 6 核心组件定义 + 训练三阶段
  - Sample 2（词向量）：3 种可视化范式（2D 投影 + 类比展示 + 语义空间）
  - Sample 3（SYSU 历史）：12 个精确历史节点 + 百年叙事（知识增强效果最显著）
- 检索效率：100% Fallback DB 命中率，~5ms 检索延迟

### 4.6 结构化知识表示与受控生成
- Content IR 和 Layout IR 作为结构化知识表示的载体
- JSON Schema 约束 vs 自然语言自由度的权衡
- IR 信息传递的有损性分析（"用户 Prompt → Content IR → Layout IR → SVG"的信息密度变化）
- 发现：IR 对创造性表达的隐性压制（`docs/discussions.md` §3.2）

### 4.7 自动评估与错误分析
- Agent 4 的 7 维度量化评估体系
- 渲染验证器（Rendering Validator）的 4 项确定性规则检查
- 评估有效性验证：Agent 4 误判修复历程（SVG 截断误判、重叠包含关系误报、标题溢出盲区）
- 定量评估指标：NER F1 / RE F1 / SVG 通过率 / 意图分类准确率 / 7 维度评分分布

---

## 第五章 实验结果与分析

### 5.1 测试样例概览
- 5 个必选样例的生成策略与预期挑战
- 最终运行配置：deepseek-v4-flash, thinking enabled, reasoning_effort=high
- 总体结果表：评分、通过状态、精炼轮数、耗时、SVG 大小、NER F1、RE F1

### 5.2 样例 1：大语言模型的基本原理 — ⭐ 9.5（最佳）
- 输入 prompt 与 Agent 1 Content IR 摘要（意图、16 实体、14 关系）
- Agent 2 配色方案（自主设计"科技深蓝"：#1A3A5C + #2980B9 + #F39C12 暖橙强调）
- 最终 SVG 设计分析：自底向上的 Transformer 数据流图 + 训练三阶段 + 情感底部
- NER F1=0.733, RE F1=0.640 — 结构化抽取质量最高
- XML 语法热修复验证：从两轮均 fail → syntax=10 一次通过
- 最终效果截图与说明

### 5.3 样例 2：词向量基本概念 — ⭐ 9.0
- 输入 prompt 与 Content IR 摘要
- Few-shot 可视化范式应用：三层布局（定义 → 2D 语义空间散点图 → king-queen 类比）
- NER F1=0.348, RE F1=0.118 — RE 低分原因分析（关系 source/target 混用非实体名）
- 重跑通过记录：首轮 information_completeness=6 未通过 → 重跑后补全训练模型内容
- 挑战分析：5 个样例中抽象程度最高，Agent 1 NER/RE 稳定性仍有波动
- 最终效果截图与说明

### 5.4 样例 3：中山大学发展历程 — ⭐ 8.3
- 输入 prompt 与知识检索过程：Fallback DB 命中 12 节点（5ms）
- Agent 2 配色：学术庄重紫蓝色系
- NER F1=0.774（最高），RE F1=0.083（14 FP 关系——target 混入非实体名）
- 知识增强效果分析：Phase 2（无检索，4 模糊节点）→ Phase 3（12 精确节点，9.0 分）→ A+B+D（8.3 分，评分更严格但内容更丰富）
- 最终效果截图与说明

### 5.5 样例 4：咖啡生产链 — ⭐ 9.0
- 输入 prompt 与 Content IR 摘要
- 唯一触发精炼的样本（2 轮）：Agent 4→3 反馈成功提升 information_completeness 和 aesthetics
- Agent 2 配色：暖调大地棕绿色系（情境化：从生豆绿到烘焙棕）
- Baseline vs Multi-Agent 视觉质量对比（引用 `docs/discussions.md` §2.1 的逐项对比表）
- 反馈闭环验证：首轮不通过 → 补充趣味细节 → 第二轮 pass
- 最终效果截图与说明

### 5.6 样例 5：视频数量对比 — ⭐ 7.0
- 输入 prompt 与数值关系抽取：`quantifier: "10 times more than"` / `"2 times more than"`
- 数值推理优化历程：Phase 3 初版 4:2:1 错误 → P0 修复三步公式 → content_accuracy: 10/10
- 标题溢出热修复验证：55 字符/990px 溢出 → 缩写版标题，未溢出
- RE F1=0.800（最高）— 数值关系抽取精度最高
- aesthetics=7 — 箭头标注对比度不足
- 最终效果截图与说明

### 5.7 系统整体定量评估
#### 5.7.1 NER/RE 评估结果汇总
- 完整评估表：Per-sample + Micro Avg + Macro Avg（P/R/F1）
- Phase 3 基线 vs A+B+D+热修复对比：NER F1 +67%，RE F1 -13%

#### 5.7.2 7 维度评分分布
- 逐样例逐维度评分矩阵（syntax/layout/content_accuracy/chart_type/information_completeness/aesthetics/creativity_density）
- 各维度均分分析：哪些维度是强项、哪些是短板

#### 5.7.3 各阶段对比
| 指标 | Phase 1 (A1→A3) | Phase 2 (+A2+A4+验证) | Phase 3 (+知识检索) | A+B+D+热修复 |
|------|-----|-----|-----|-----|
| Agent 数量 | 2 | 4 | 4+KB | 4+KB |
| 通过率 | 5/5 (XML) | 5/5 | 5/5 | 5/5 |
| 平均评分 | — | 8.7 | 8.9 | 8.6 |
| 单样例平均耗时 | ~27s | ~362s | ~353s | ~214s |
| NER Micro F1 | — | — | 0.406 | 0.678 |
| 视觉质量 (人评) | 一般 | 模板化 | 模板化 | 明显改善 |

### 5.8 Baseline vs Multi-Agent 对比分析
- 速度/成本/质量三维度对比（引用 `docs/results.md` §3、§6）
- 核心发现：
  1. 相同模型下，baseline 视觉更优（设计委员会效应 + IR 信息损失）
  2. Multi-agent 在知识准确性和可审查性上胜出
  3. A+B+D 创意解放方案有效缩小视觉质量差距
- 信息充分性决定 baseline 相对表现：sample4（信息充分，差距最小）vs sample3（需外部知识，差距最大）
- 对多 Agent 架构本质取舍的反思（引用 `docs/discussions.md` §5）

---

## 第六章 讨论

### 6.1 多智能体架构的"设计委员会"效应
- 核心发现：将创意任务拆解为子任务导致整体视觉质量下降
- 根因分析（7 个维度）：
  1. 设计委员会效应（Design by Committee）：无人对"整体美感"负责
  2. IR 中间表示对创造性表达的隐性压制：结构化信息 ≠ 美学意图
  3. Thinking Mode 对视觉创意的意外惩罚：分析性思维 → 保守输出
  4. Agent 间信息传递的逐级衰减：有损压缩
  5. 标准化 vs 情境化的配色策略：模板选择 ≠ 情境化设计
  6. Satisficing 天花板：通过线逻辑阻止"更好"
  7. 架构复杂度的隐性代价（Meta-Level）
- 对 Agentic 系统设计的启示：哪些子任务适合分解，哪些不适合

### 6.2 系统局限性
- Agent 1 NER 结构化输出稳定性：同一 prompt 多次运行间 key_points 覆盖度波动
- Agent 1 RE FP 率：source/target 混用非实体名（sample3: 14 FP）
- 纯文本 LLM 审查的局限：Agent 4 无法真正"看到"渲染结果
- 渲染环境一致性问题：cairosvg vs 浏览器渲染差异
- 级联错误风险：线性流水线的结构性缺陷
- Thinking Mode 的延迟代价：Agent 3 延迟 +5.8×
- 单轨道生成：无法在多方案间选优

### 6.3 与参考方法的比较
- vs OmniSVG：训练路线 vs API 路线；端到端 vs 多 Agent
- vs SVGen：微调小模型 vs 调用大模型 API；CoT 标注 vs CoT Prompt
- 本方案的比较优势：零训练成本、高度可解释、IR 可审查
- 本方案的比较劣势：API 依赖、延迟高、视觉质量上限受架构约束

### 6.4 改进方向
#### 6.4.1 微调路线（SVGen-like）
- 使用本项目积累的 prompt-SVG 对构建训练数据
- 微调轻量 LLM（Qwen2.5-3B）实现端到端 SVG 生成
- 推理时用多 Agent 做纠错/美化

#### 6.4.2 多模态视觉评估
- SVG → PNG → 多模态模型视觉检查
- 需解决 self-evaluation bias（生成模型与审查模型相同）
- 需验证渲染环境一致性

#### 6.4.3 渲染引擎集成（双重渲染模式）
- 结构化图表（流程图、柱状图、时间线）走 IR→渲染器路径
- 自由形式图表（概念图、架构图）保留 LLM 直接生成
- Layout IR 增加 `render_mode` 字段

#### 6.4.4 双轨生成 + 选优机制
- 标准版（IR 强约束）+ 自由版（IR 弱约束）并行生成
- Agent 4 对比两版在 aesthetics 和 content_accuracy 上的表现，加权选优

#### 6.4.5 合并 Agent 2+3
- 消除布局规划与 SVG 编码之间的信息损失
- 单一 Agent 在单次 LLM 调用中同时完成布局与编码

#### 6.4.6 动态 SVG 动画与交互
- CSS/SMIL 动画支持
- 交互式 SVG（hover 效果、可展开节点）

---

## 第七章 结论

- 项目成果总结：成功构建 4 Agent + 知识检索 + 渲染验证的 SVG 生成系统，5/5 样例全部通过
- 核心贡献：
  1. 完整的 A+B+E 混合架构，展示了 NLP 知识在工程中的实际运用
  2. 诚实的 Baseline vs Multi-Agent 对比分析，揭示了多 Agent 架构的本质取舍
  3. A+B+D 创意解放方案，在不牺牲量化评估的前提下有效缩小视觉质量差距
  4. 定量 NER/RE 评估体系（5 份 Ground Truth + 自动化评估脚本）
- 核心 Insight：多 Agent 架构以创意换可控性——这不是"失败"而是"取舍"
- 对 NLP 课程设计的意义：完整的"分析→设计→实现→评估→反思"闭环

---

## 参考文献

1. Yang Y, Cheng W, Chen S, et al. Omnisvg: A unified scalable vector graphics generation model[J]. Advances in Neural Information Processing Systems, 2026, 38: 113670-113696.
2. Wang F, Zhao Z, Liu Y, et al. Svgen: Interpretable vector graphics generation with large language models[C]. Proceedings of the 33rd ACM International Conference on Multimedia, 2025: 9608-9617.
3. DeepSeek API 文档. https://api-docs.deepseek.com/
4. OpenAI Python SDK. https://github.com/openai/openai-python
5. cairosvg. https://cairosvg.org/
6. python-pptx. https://python-pptx.readthedocs.io/

---

## 附录

### 附录 A：完整 System Prompt 设计
- A.1 Agent 1 System Prompt（含 P0 实体抽取强化 + 输出质量参考示例）
- A.2 Agent 2 System Prompt（含 A+B+D 去模板化 + 标题长度约束）
- A.3 Agent 3 System Prompt（含 A+B+D 创意充实清单 + 热修复 + 自检清单）
- A.4 Agent 4 System Prompt（含 creativity_density 维度 + 标题溢出检查）
- A.5 SVG 设计规范（svg_guidelines.txt，含柱状图坐标铁律 + 几何图标组件库）

### 附录 B：IR Schema 完整定义
- B.1 Content IR JSON Schema
- B.2 Layout IR JSON Schema
- B.3 Review IR JSON Schema

### 附录 C：关键代码片段
- C.1 BaseAgent 基类（API 调用、重试、JSON 解析）
- C.2 Pipeline Orchestrator（多 Agent 调度、反馈闭环）
- C.3 Rendering Validator（4 项确定性检查）
- C.4 Knowledge Retriever（Wikipedia + Fallback DB）

### 附录 D：全部生成结果
- D.1 最终 SVG 代码（5 个样例）
- D.2 简化版 IR 样例（每样例展示 Content IR + Layout IR + Review IR 的关键字段）
- D.3 Baseline SVG 代码（5 个样例，用于对比）
- D.4 PPT 导出文件（可选）

### 附录 E：NER/RE Ground Truth 标注数据
- E.1 标注规范与原则
- E.2 5 个样例的完整 Ground Truth（entities + relations）

### 附录 F：开发日志摘要
- F.1 Phase 1：核心流水线搭建（Agent 1 + Agent 3，5/5 XML 有效）
- F.2 Phase 2：质量提升（4 Agent + 渲染验证 + 反馈闭环，均分 8.7）
- F.3 Phase 3：知识增强（Wikipedia + Fallback DB + PPT 导出，均分 8.9）
- F.4 Prompt 优化：P0 缺陷修复（NER +67%, RE F1=0.678）
- F.5 A+B+D 创意解放：Agent 2/3/4 Prompt 改造
- F.6 热修复：标题溢出三层防御 + XML 特殊字符安全 + Agent 4 盲区
- F.7 Baseline 对照实验：单次直出 vs 多 Agent 流水线

### 附录 G：项目文件清单
- 源码结构（`src/`、`main.py`、`baseline.py`）
- 输出文件（`outputs/`、`outputs_baseline/`）
- 测试与评估（`tests/`）
- 文档（`docs/`）

---

> **大纲说明**：
> - 本大纲覆盖了项目从需求分析 → 架构设计 → 实现 → 评估 → 反思的完整闭环
> - 所有数据、指标、分析均可从 `docs/results.md`、`docs/changelog.md`、`docs/discussions.md` 中直接提取
> - 第 2-3 章对应 PRD 要求的"系统架构设计与实现细节"
> - 第 4 章对应 PRD 要求的"NLP 知识运用分析"
> - 第 5 章对应 PRD 要求的"不少于 5 组问答结果"
> - 第 6 章体现了项目的学术深度（诚实的自我反思 + 本质取舍分析）
> - 附录提供完整的可复现材料
