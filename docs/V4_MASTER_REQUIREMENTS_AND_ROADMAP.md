<!-- V4_CURRENT_STATE_BEGIN -->
> **当前导航（2026-10-16）**：本地活跃开发、工程验收、产品修复和本地候选交付从 [V4_CURRENT_STATE.md](V4_CURRENT_STATE.md) 及[产品执行记录](V4_PROD_EVAL_REL_20261015.md)读取。
> **本轮用户要求**：执行 `PUB-01 / PUB-02`，从独立公开候选同步上传版并验证源码交付，详见[发布说明](V4_PUBLICATION_20261016.md)。生产基线和 Full144 不因发布改写；alpha.3 保留开发快照与三项质量 FAIL。
> **历史正文边界**：以下完整正文保留 2026-09-16 检查点，其“当前”“未授权”等字样记录当时事实。本轮用户要求与后续证据在当前入口独立登记，不改写历史授权、旧指标或历史科学结论。
<!-- V4_CURRENT_STATE_END -->

# KB-V4 — Master Requirements & Roadmap

> **文档角色**：KB-V4 当前开发总控文档（authoritative prose-level master）。
> **适用范围**：本地数据库问答系统 / KB-V4。
> **Master 对齐检查点**：Post-V4.8.2 Next-Workstream Priority Review — Final Governance Closure / R6-C（2026-09-16）。
> **本次 replacement source SHA256（旧 Master）**：`2db9292d8785ce138f74d2e2e7d250ec95ec60b1cdeb2b39a08d3c8b9b804800`（已独立核验）。
> **本次更新性质**：`DOCUMENTATION / GOVERNANCE ALIGNMENT ONLY`；不推进 Product baseline，不产生执行授权。
> **当前状态**：V4 Development Active；尚未达到 V4 Final Product Quality DoD。
> **当前产品基线**：`V4_6_2_HASH_PORTABILITY_BASELINE`。
> **当前 canonical production_source_hash**：`108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c`。
> **历史 raw (CRLF) production hash（V4.6.1 provenance）**：`7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a`。
> **当前最近完成诊断阶段**：`V4.8.2 — Residual Failure Differential Attribution & Hypothesis Formation` 已 **COMPLETE / CLOSED / FINAL ACCEPTED**。
> **当前最近完成治理阶段**：`Post-V4.8.2 Next-Workstream Priority Review` 已 **CLOSED / FINAL_ACCEPTED**（R6-C final validation 247/247 PASS）。
> **当前 Generation 机制状态**：`GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED`；`CAUSAL_MECHANISM_ESTABLISHED = NO`。
> **当前下一 residual hypothesis**：`NOT_ESTABLISHED`。
> **当前下一诊断阶段编号 / candidate**：`NOT_ESTABLISHED`；`NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO`。
> **当前 Product remediation**：`PRODUCT_REMEDIATION_AUTHORIZED = NO`。
> **当前路线决策点**：`RECOMMENDED_NEXT_WORKSTREAM = WS-13`，`RECOMMENDATION_SUPPORT = WEAK`；WS-13 对应 candidate `V4.13 Citation`，但 `NEXT_WORKSTREAM_EXECUTION_AUTHORIZED = NO`，不得把 recommendation 解释为 authorization。
> **Document Identity Remediation**：继续 `BLOCKED`（当前 pipeline 的 Document Identity Loss 已在 V4.7 被机械排除；不存在相应 remediation 授权）。
>
> Source-of-truth 优先级：
>
> `code / tests / machine-readable eval artifacts`
> `>`
> `Product Quality Contract / baseline lineage / actual runtime evaluation outputs`
> `>`
> `阶段 evidence / phase reports / governance review`
> `>`
> `本 Master prose`
>
> 本文用于导航、状态汇总与路线治理；若与更高位阶事实源冲突，以更高位阶事实源为准。
> 本次更新同步 V4.8 / V4.8.1 / V4.8.2 已接受状态以及 Post-V4.8.2 Next-Workstream Priority Review 的最终治理结论；不创建新科学证据、不修改 Product / baseline / Golden / evaluator / runtime DB。
>
> **重要解释边界**：
>
> - V4.7 的 `MATERIAL_INDEX_REPRESENTATION_BIAS` 必须保留为 **V4.7 当时的阶段性诊断表述**，不得继续升级为当前已建立的全局 shared causal mechanism；
> - V4.8 已建立 heterogeneous intervention-response profile，但 `MIXED_GENERATION_MECHANISMS = NOT_ESTABLISHED`；
> - V4.8.1 只否定当前 operationalized `EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION`，不得外推为“所有 chunk-to-document aggregation 均无效”；
> - V4.8.2 到达 frozen-evidence attribution ceiling：存在机械差异，但没有满足 governed emission gate 的 top hypothesis；
> - 因此当前不能自动进入 V4.8.3，也不能直接授权任何 generation remediation；
> - Post-V4.8.2 Priority Review 已机械选出 `WS-13` 为唯一推荐 workstream，但其 readiness 仍为 `R3 / FRESH_ATTRIBUTION`，且 recommendation support 仅为 `WEAK`；这不构成 V4.13 execution/remediation authorization。

---

## 0. V4 核心治理原则

V4 继续执行以下不可降级原则：

1. **单一 workstream 单独授权**
   每个 remediation / measurement / publication / tooling 阶段独立授权，不自动跨阶段。

2. **Preflight-first**
   每个阶段开始前必须确认 workspace、baseline、production hash、Git 状态和边界条件。

3. **Product 与 Measurement 分离**
   Product defect、Evaluator defect、Golden defect、Citation defect 不得混为同一原因。

4. **单一主要 root-cause family**
   一个 remediation phase 原则上只处理一个主要 subsystem；无证据不得捆绑 Router / Retrieval / Generation / Citation。

5. **Historical Baseline 不可覆盖**
   历史 stage baseline 一旦形成即 immutable。新的 production remediation 只能追加新的 child baseline。

6. **Diagnosis-only 阶段不建立 product baseline**
   纯诊断、归因、审计阶段不得伪造新的 CURRENT_PRODUCT_STATE。

7. **不通过修改 Golden 为产品提分**
   Golden/Evaluator 修复必须基于可证明的 measurement defect，而不是为了提高 metric。

8. **CI PASS ≠ Product Quality PASS**
   测试、lint、compile、CI 通过仅代表工程回归通过，不代表最终质量 Gate 达标。

9. **不降低 Gate**
   V4 最终 Contract 不因阶段性发布、pre-release 或 checkpoint 而下调。

10. **每次 remediation 后重新归因**
    下游阶段顺序只能基于最新 post-remediation evidence，而不能机械照抄旧路线图。

---

# 1. V4 Product Goal

V4 的目标不是单纯增加功能，而是把 V3 已有 RAG 系统推进到：

1. 可复现评测；
2. 可追踪 baseline lineage；
3. 可机械归因 residual failure；
4. 可隔离修复真实产品缺陷；
5. 可检测未登记 production drift；
6. 模型配置、向量库、检索链路与回答链路身份一致；
7. 可安全迁移 workspace，不依赖本机旧绝对路径；
8. 最终通过统一 Full-144 Product Quality Closure。

---

# 2. Must-have

## M1 — Evaluation Integrity

必须具备：

- 单一 canonical evaluator；
- 单一 canonical Golden；
- verifier / evaluator provenance 明确；
- baseline artifact 可复现；
- answer cache 与 production hash / evaluator / Golden 绑定；
- historical baseline immutable；
- live production hash 能与 current baseline 自动交叉验证。

## M2 — Failure Attribution

所有真实 residual failure 必须能够区分：

- Scope/OOS
- Routing
- Document Identity
- Retrieval
- History
- Generation
- Citation
- Evaluator
- Golden Contract
- Multi-cause

不得仅根据 case prefix 推断 root cause。

## M3 — Measurement Correctness

Golden / Evaluator 中被机械证明错误的部分必须独立修正：

- 不降低标准；
- 不针对单个失败 case 特判；
- 不为提高分数修改 expected facts；
- product remediation 与 measurement remediation 必须分轨。

## M4 — Product Remediation

对经**最新受治理 evidence**机械证明存在的 Product defect，必须在对应 subsystem 的独立授权阶段完成 remediation / closure；不得把历史 attribution 直接当作当前 remediation 授权。

当前状态：

- **Scope false refusal**：已证明并已完成 remediation；
- **Routing over-trigger**：已证明并已完成 remediation；
- **Document Identity**：当前 V4.7 targets 中 `CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS = DISPROVEN`，`DOCUMENT_IDENTITY_ROOT_CAUSE = NOT_PROVEN`，因此 remediation `BLOCKED / NOT AUTHORIZED`；
- **Multi-turn History**：存在历史 residual signal，但进入 Product remediation 前必须基于最新 product state 做 fresh attribution；
- **Retrieval**：仅对重新确认的 `true retrieval miss` 进入 remediation，必须排除 generation omission / history / measurement / multi-cause；
- **Generation completeness**：存在 generation-family residual，但 `GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED`，不得假定一个已证明的统一 generation fix 可覆盖全部 residual。

Citation 是否进入正式 product remediation，继续由后续 residual evidence 与独立 authorization 决定。

## M5 — Unified Product Quality Closure

最终统一执行 canonical Full-144，并依据冻结 Contract 做 PASS / FAIL 判定。

---

# 3. Should-have

## S1 — 提升核心回答质量

重点提升：

- case_exact
- fact_recall

目标为达到或尽量逼近最终 Contract target。

## S2 — 提升 citation coverage

但必须继续保持：

- invalid citation = 0；
- citation scope violation = 0。

不得以 Citation 安全退化换 coverage。

## S3 — 保守改进 evaluator fact matcher

允许支持合理语义等价，但必须：

- 防止 false-positive；
- 有独立 measurement attribution；
- 不与 product fix 混合实施。

---

# 4. Deferred / Out-of-scope

当前仍 deferred：

- KB Summary 产品化扩展；
- Multi-document Summary 产品化扩展；
- 通用 Document/library metadata query；
- Production L2 verifier；
- Production Citation Completion；
- Rich Citation UX；
- Performance SLA；
- Reranker 重新启用。

这些事项不得为了当前主质量 Gate 临时插入主线。

---

# 5. Current Production Architecture

> 机械核验来源：`core/config.py`、`core/library_store.py`、`eval/v4_6_1_embedding_identity_baseline.json`。

## 5.1 Answer Model

```text
qwen2.5:7b
```

## 5.2 Embedding Model

```text
bge-m3
dimension = 1024
```

## 5.3 Vector Backend

当前默认：

```text
SQLite
```

Qdrant 保持兼容/服务型 backend。

当前存量向量与：

```text
bge-m3 / 1024
```

一致。

## 5.4 Reranker

```text
disabled by default
```

历史 BGE reranker 实验结果不作为当前 V4 默认 product path。

---

# 6. Embedding Identity Contract

V4 当前明确要求：

```text
configured embedding model
==
stored embedding model
==
stored vector dimension contract
```

对于已有向量库：

```text
bge-m3
1024
```

启动时执行 fail-closed identity validation。

禁止：

- 静默切换 embedding model；
- 仅因向量维度相同而把不同模型向量视为兼容；
- 自动 re-embed；
- 自动重建数据库；
- 自动重建 Qdrant。

---

# 7. Quality Gates

V4 Final 质量 Gate 保持（与机器 Contract `frozen_targets` 一致，不得修改）：

| Metric | Target |
|---|---:|
| case_exact_fact_match_rate | ≥ 0.80 |
| fact_recall | ≥ 0.90 |
| false_refusal_rate | ≤ 0.03 |
| citation_coverage | ≥ 0.80 |
| high_confidence_unsupported_rate | ≤ 0.05 |
| invalid_citation_count | 0 |
| citation_scope_violation | 0 |
| pure_OOS_false_accept_rate | 0 |
| Phase E Router | PASS |
| F.2 Citation Safety | PASS |

这些 Gate 不因 Development Snapshot / Pre-release 发布而改变。

---

# 8. Baseline Governance

原则：

```text
Historical stage baselines are immutable.

Production remediation
→ creates a NEW baseline.

Diagnosis-only / tooling-only / publication-only phase
→ does NOT create product baseline.
```

当前 lineage：

```text
V4_INITIAL_BASELINE
        ↓
V4_4_SCOPE_REMEDIATION_BASELINE
        ↓
V4_5_ROUTING_BASELINE
        ↓
V4_6_1_EMBEDDING_IDENTITY_BASELINE
        ↓
V4_6_2_HASH_PORTABILITY_BASELINE
```

当前：

```text
current_baseline_id =
V4_6_2_HASH_PORTABILITY_BASELINE
```

当前 canonical production hash（line-ending portable）：

```text
108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
```

历史 raw (CRLF) production hash provenance：

```text
V4_6_1 = 7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a
```

已有 live production drift guard（`tests/test_live_production_hash_guard.py`）：

```text
lineage current pointer
→ current baseline artifact
→ recorded canonical production hash
==
recomputed live canonical production hash
```

任何未登记 production drift 必须立即导致测试失败。该身份为 canonical
（`sha256-path-content-v2-canonical-lf`），跨 Windows CRLF 工作树与 LF checkout 一致。

---

# 9. Canonical Current Product Quality

当前 canonical Full-144（**product metrics source** = `V4_6_1_EMBEDDING_IDENTITY_BASELINE`，
`metrics_recomputed_in_v4_6_2 = false`；current governance baseline = `V4_6_2_HASH_PORTABILITY_BASELINE`；
现场直接读取 `eval/v4_6_1_embedding_identity_baseline.json`）：

```text
case_exact        = 0.7292
fact_recall       = 0.8535
false_refusal     = 0.0000

citation_coverage = 0.4657
high_conf         = 0.0132

invalid citation  = 0
scope violation   = 0
```

因此当前：

```text
Product Quality DoD = NOT_YET_PASS
```

已达标：

```text
false_refusal
high_conf
invalid citation
scope violation
pure-OOS safety
Phase E
F.2 citation safety
```

仍未达到最终 target：

```text
case_exact
fact_recall
citation_coverage
```

因此当前只能发布为：

```text
DEVELOPMENT SNAPSHOT / PRE-RELEASE
```

不能称为：

```text
V4 FINAL
```

---

# 10. Completed Phase History

> 阶段角色区分：`PRODUCT REMEDIATION` / `READ-ONLY DIAGNOSIS` / `CONTROLLED COUNTERFACTUAL DIAGNOSIS` / `FROZEN-EVIDENCE ATTRIBUTION` / `GOVERNANCE / FORMALIZATION` / `TOOLING-ONLY FIX`。
> tooling-only、diagnosis-only、counterfactual diagnosis 与 frozen-evidence attribution 阶段 **不** 建立 product baseline。

## V4.0 — Cold Start / Baseline Inheritance

```text
COMPLETE  ·  GOVERNANCE
```

完成 V3 → V4 冷启动边界与 workspace 角色确认。

## V4.1 — Requirements / Roadmap Planning

```text
COMPLETE  ·  GOVERNANCE
```

冻结 Must / Should / Deferred 与开发纪律。

## V4.2 — Evaluation Integrity & Baseline Reconciliation

```text
COMPLETE  ·  GOVERNANCE
```

建立 canonical evaluator 与 `V4_INITIAL_BASELINE`。

初始 canonical：

```text
case_exact    0.7083
fact_recall   0.8312
false_refusal 0.0208
coverage      0.4893
high_conf     0.0095
```

## V4.3 — Failure Attribution Rebuild

```text
COMPLETE  ·  READ-ONLY DIAGNOSIS
```

重建 case-level root-cause attribution。

## V4.3.1 — Failure Attribution Closure

```text
COMPLETE  ·  GOVERNANCE
```

修正 citation population、multi-cause backlog、Scope attribution 等治理问题。

## V4.4 — Scope/OOS False-Refusal Remediation

```text
COMPLETE  ·  PRODUCT REMEDIATION（首个 production remediation）
```

修复：

```text
loc-018
mt-006
md-014
```

的 false OOS。

核心标定：

```text
dense_only = 0.50
```

结果：

```text
false_refusal = 0
pure-OOS false accept = 0/7
scope leakage = 0
```

> 精度说明：`mt-006` 在本阶段仅移除 **Scope 阻塞**（answer 层不再误拒）；其 HISTORY 残差
> （rewrite 塌缩为裸词 `OFDM`）按授权记录、**未在 V4.4 修复**，留待 History 阶段。

## V4.4.1 — Baseline Lineage & Scope Closure

```text
COMPLETE  ·  GOVERNANCE
```

正式建立 immutable stage baseline lineage。

## V4.5 — Routing Over-trigger Remediation

```text
COMPLETE  ·  PRODUCT REMEDIATION
```

修复：

```text
md-004
md-019
cit-001
cit-007
```

被 `LOCATION_WORDS` 过触发进入 locate route 的问题。

Routing over-trigger 已收口。

## V4.6 — Post-Routing Residual Attribution

```text
COMPLETE  ·  READ-ONLY DIAGNOSIS
```

重新从 post-V4.5 product state 导出 residual failure。

当时 evidence-based priority：

```text
Priority 1  Document Identity
Priority 2  History
Priority 3  Retrieval
Subsequent  Generation
Measurement Golden/Evaluator
Deferred    Citation
```

该 priority 属于历史阶段输出；后续 V4.7–V4.8.2 已进一步重写 Document Identity / Generation 解释。

Routing 当前可以 leave-as-is。

## V4.6.1 — Embedding Identity & Model Alignment Formalization

```text
COMPLETE  ·  GOVERNANCE / FORMALIZATION
```

正式收编：

```text
nomic-embed-text default
→
bge-m3
```

并增加：

```text
Embedding Identity fail-closed startup guard
```

同时确认：

```text
Scope semantics unchanged
Routing unchanged
existing vector data safe
```

建立：

```text
V4_6_1_EMBEDDING_IDENTITY_BASELINE
```

以及 live production drift detection。

## V4.6.2 — Hash Portability & CI Reproducibility Formalization

```text
COMPLETE  ·  GOVERNANCE / MEASUREMENT PORTABILITY
```

正式确立 versioned canonical content-hash contract：

```text
algorithm        = sha256-path-content-v2-canonical-lf
canonicalization = line endings only（CRLF / bare CR → LF；仅限已识别 text 后缀）
binary / unknown = raw bytes（绝不 decode / normalize）
```

修复：V4.0–V4.6.1 的 content-hash / byte-identity guard 直接对 raw 字节取哈希，导致
Windows CRLF 工作树与 Git LF blob / CI checkout 对**同一文本**得到不同身份
（`7216c885…` vs `108fb167…`），使 `v4.0.0-alpha.1` 的远端 CI byte-identity guard 失败。

本阶段**不是** product remediation：

```text
production_behavior_changed_in_stage        = false
measurement_hash_contract_changed_in_stage  = true
metrics_recomputed_in_stage                 = false
metrics_source                              = V4_6_1_EMBEDDING_IDENTITY_BASELINE
```

建立：

```text
V4_6_2_HASH_PORTABILITY_BASELINE
```

历史 raw hashes 继续作为 provenance 保留（旧 artifact 不被覆盖、不被改写）。

## V4.7 — Document Identity Root-Cause Confirmation + Diagnosis Closure

```text
COMPLETE / CLOSED  ·  READ-ONLY DIAGNOSIS（不建立 product baseline）
```

对象：`md-004` / `md-009` / `md-015`。

机械结论（机器事实源：`eval/v4_7_document_identity_root_cause.json`）：

```text
V4_7_DIAGNOSIS_CLOSURE                         = PASS
V4_7_ENVIRONMENT_EQUIVALENCE                   = PASS

CURRENT_PIPELINE_ROOT_CAUSE                    = GENERATION
CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS        = DISPROVEN
DOCUMENT_IDENTITY_ROOT_CAUSE                   = NOT_PROVEN
DOCUMENT_IDENTITY_MECHANISM_APPLICABLE         = NO
FIRST_IDENTITY_LOSS_LAYER                      = NONE

PRODUCT_ROOT_CAUSE_FAMILY_SHARED               = YES（GENERATION）
MIXED_PRODUCT_ROOT_CAUSE_FAMILIES              = NO
SHARED_GENERATION_MECHANISM                    = YES（V4.7 阶段表述：MATERIAL_INDEX_REPRESENTATION_BIAS）
GENERATION_MECHANISM_ISOLATION                 = NOT_ESTABLISHED

MEASUREMENT_SEMANTIC_ISSUE                     = SUPPORTED（独立 Measurement 轨道）
HISTORICAL_SOURCE_ANCHOR_AVAILABLE             = NO
RELEVANT_PIPELINE_EQUIVALENCE                  = NOT_ESTABLISHED
HISTORICAL_FAILURE_COMPATIBILITY               = STRONGLY_SUPPORTED
```

即：canonical document title 在 `documents.title → ChunkRecord.document_title → chunk.location →
serialized material header → application-level Ollama request` 全链路保持可见，
Document Identity Loss 在当前 V4.6.2 pipeline 被机械排除；Document Identity remediation **BLOCKED**。
V4.6 post-routing attribution 的 `DOCUMENT_IDENTITY_FAILURE` 解释被 **STRONGLY_CHALLENGED**，
但历史 pipeline 等价性因缺少 exact historical source anchor 而 **NOT_ESTABLISHED**。

> **后续证据限定**：V4.7 的 `MATERIAL_INDEX_REPRESENTATION_BIAS` 是启动 V4.8 mechanism-isolation 的
> 阶段性候选解释；V4.8 的 heterogeneous response 已证明它不能被当作当前三个 target 上
> 已建立的统一 causal mechanism。

## V4.8 — Generation / Prompt-Evidence Framing Mechanism Isolation + Closure

```text
COMPLETE / CLOSED  ·  CONTROLLED COUNTERFACTUAL DIAGNOSIS
DIAGNOSTIC_ONLY
NO PRODUCT BASELINE
```

对象：`md-004` / `md-009` / `md-015`。

V4.8 使用 contemporaneous controlled counterfactual 对两个 framing factors 进行隔离：

```text
M1 / Factor A =
MATERIAL_INDEX_REPRESENTATION_BIAS operationalization
（材料N → 证据块N；保留结构索引）

M2 / Factor B =
MINIMAL EXPLICIT CANONICAL-TITLE NAMING INSTRUCTION

A+B =
combined intervention
```

接受后的 per-case 结果：

```text
md-004:
M1_CAUSAL_SUPPORT = SUPPORTED
M2_CAUSAL_SUPPORT = SUPPORTED
M1_ISOLATED = NO
M2_ISOLATED = NO
MULTIPLE_SUFFICIENT_INTERVENTIONS = YES
M3_INTERACTION_EFFECT = NOT_ESTABLISHED
INTERACTION_PATTERN = SUBADDITIVE_BINARY_CEILING_COMPATIBLE

md-009:
M1 = NOT_SUPPORTED
M2 = NOT_SUPPORTED
M4_PHASE_LOCAL_SUPPORT = SUPPORTED
M4_GLOBAL_STATUS = NOT_ESTABLISHED

md-015:
M1 = NOT_SUPPORTED
M2 = NOT_SUPPORTED
M4_PHASE_LOCAL_SUPPORT = SUPPORTED
M4_GLOBAL_STATUS = NOT_ESTABLISHED
```

Aggregate：

```text
M1_SHARED_SUPPORT = PARTIAL
M2_SHARED_SUPPORT = PARTIAL
M4_SHARED_PHASE_LOCAL_SUPPORT = PARTIAL

HETEROGENEOUS_RESPONSE_PROFILE = YES
SHARED_CAUSAL_MECHANISM = NOT_ESTABLISHED
MIXED_GENERATION_MECHANISMS = NOT_ESTABLISHED
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED

GROUPING_RESIDUAL_EVIDENCE = SUPPORTED
```

因此：

- `md-004` 对 A/B 均响应；
- `md-009` / `md-015` 对 A/B/A+B 均不响应；
- “V4.7 的 shared material-index mechanism”不得继续作为当前全局已证明机制；
- heterogeneous response **不等于** mixed mechanisms 已证明；
- residual evidence 支持继续窄化诊断，但不授权 Product remediation。

V4.8 永久审计限定：

```text
PARENT_V4_8_PROTOCOL_PROVENANCE_CONFIDENCE =
PARTIAL

PARENT_V4_8_PRIMARY_OUTCOME_INVARIANT_TO_MATCHER_BROADENING =
YES

PARENT_V4_8_PRECLOSURE_DERIVED_SEMANTIC_DIGEST =
NOT_AVAILABLE_PRECLOSURE_DERIVED_DIGEST_OVERWRITTEN
```

接受：

```text
V4_8_SCIENTIFIC_CLASSIFICATION = ACCEPTED
```

但禁止把 provenance 升级为 `STRONG`，也禁止重构缺失的 preclosure derived semantic digest。

## V4.8.1 — Residual Generation / Explicit Document-Membership Representation Isolation

```text
COMPLETE / CLOSED  ·  SINGLE-FACTOR CONTROLLED COUNTERFACTUAL DIAGNOSIS
DIAGNOSTIC_ONLY
NO PRODUCT BASELINE
```

primary residual targets：

```text
md-009
md-015
```

测试的唯一新 factor：

```text
G =
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION

G_OPERATIONALIZATION =
EXPLICIT_MEMBERSHIP_METADATA_ONLY
```

保持 A=`A0`、B=`B0`，不做 physical chunk regrouping、不改 chunk order、不改 title salience、不增加 naming instruction。

结果：

```text
md-009:
G0 = FAIL
G1 = FAIL
DELTA_G = 0.0
EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT = NOT_SUPPORTED
EXPLICIT_MEMBERSHIP_ISOLATED = NO

md-015:
G0 = FAIL
G1 = FAIL
DELTA_G = 0.0
EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT = NOT_SUPPORTED
EXPLICIT_MEMBERSHIP_ISOLATED = NO
```

Aggregate：

```text
RESIDUAL_SUBSET_SHARED_MEMBERSHIP_SUPPORT = NO
HETEROGENEOUS_RESIDUAL_RESPONSE = NO
MIXED_RESIDUAL_MECHANISMS = NOT_ESTABLISHED

EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_CAUSAL_SUPPORT = NO
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_ISOLATED = NO

CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS =
NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION

GENERATION_MECHANISM_ISOLATION =
NOT_ESTABLISHED
```

`md-004` 因两个 primary cases 均未得到正 causal support 且 remediation readiness 明显为 NO，
按预声明规则未补跑 reference pair：

```text
MD004_REFERENCE_PAIR_REQUIRED = NO
```

科学解释边界：

> 当前 operationalized explicit-membership metadata 没有修复 `md-009/md-015` residual failure。
> 该结果**不证明** physical regrouping、reordering、document-level summarization 或所有广义
> chunk-to-document aggregation 均无效。

完整性：

```text
V4_8_1_PROTOCOL_EXECUTION = PASS
production hash unchanged = YES
Product code changed = NO
baseline changed = NO
runtime DB changed = NO
```

后续 V4.8.2 对 V4.8.1 manifest accounting 的只读复核认定：

```text
PRE_CHANGE_MANIFEST_COUNT = 300
FINAL_MANIFEST_COUNT = 305
PHASE_WIDE_V4_8_1_PATH_DELTA = 5
POST_SNAPSHOT_OR_RESUME_ADDITIONAL_PATH_DELTA = 4

V4_8_1_MANIFEST_ACCOUNTING_STATUS =
PROSE_LABEL_INCONSISTENCY_ONLY
```

即 frozen machine artifact 的 `300 → 305` 与 5 个 phase-wide paths 一致；
旧 human-report prose 中 `304 = 300 + 4` 仅是 scope/label bookkeeping 不严谨，
不影响 V4.8.1 科学结果，且 parent artifact 未被 V4.8.2 回写。

## V4.8.2 — Residual Failure Differential Attribution & Hypothesis Formation

```text
COMPLETE / CLOSED / FINAL ACCEPTED
FROZEN-EVIDENCE DIFFERENTIAL ATTRIBUTION
DIAGNOSTIC_ONLY
NO PRODUCT BASELINE
```

本阶段不产生新模型证据：

```text
NEW_DIAGNOSTIC_MODEL_CALLS = 0
NEW_COUNTERFACTUAL_RUNS = 0
NEW_PRODUCTION_RETRIEVAL_RUNS = 0
```

目的：

> 用冻结的 V4.7 / V4.8 / V4.8.1 evidence，比较 responsive reference `md-004`
> 与 residual nonresponders `md-009 / md-015`，判断 frozen evidence 是否足以形成
> 下一条 governed residual hypothesis。

最终接受：

```text
V4_8_2_PROTOCOL_EXECUTION = PASS
V4_8_2_FINAL_GOVERNANCE_REVIEW = ACCEPT
V4_8_2_FINAL_ACCEPTED = YES

R6 = FULLY_ACCEPTED
R6_FC = ACCEPTED_WITH_REVIEWER_STATUS_CORRECTION
```

核心机械结果：

```text
MD009_MD015_RESIDUAL_SIMILARITY_SCORE = 0.3333
MD009_MD015_RESIDUAL_SIMILARITY = LOW

MD004_TO_RESIDUAL_DIFFERENCE_SCORE = 0.4286
MD004_TO_RESIDUAL_DIFFERENCE = MEDIUM
```

候选/排名边界：

```text
TOP_DIFFERENTIAL_FEATURES =
NOT_ESTABLISHED_NO_GOVERNED_TOP_FEATURE_RANKING_RULE

RANKED_SHORTLIST_ELIGIBLE_COUNT = 0
TOP_CANDIDATE_HYPOTHESIS = null
TOP_CANDIDATE_SUPPORT = null

SHARED_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED
CASE_SPECIFIC_RESIDUAL_MECHANISM_ESTABLISHED = NO

DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED =
NOT_ESTABLISHED
```

最终 scientific / authorization state：

```text
NEXT_RESIDUAL_HYPOTHESIS =
NOT_ESTABLISHED

NEXT_DIAGNOSTIC_PHASE_NUMBER =
NOT_ESTABLISHED

NEXT_DIAGNOSTIC_CANDIDATE =
NOT_ESTABLISHED

NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED =
NO

CAUSAL_MECHANISM_ESTABLISHED =
NO

PRODUCT_REMEDIATION_AUTHORIZED =
NO
```

因此 V4.8.2 的正确解释不是“没有结果”，而是：

1. frozen evidence 显示 residual cases 之间机械相似度偏低；
2. responsive reference 与 residual subset 存在中等机械差异；
3. 这些差异不足以通过 governed candidate-support / ranking / emission gate 建立 top hypothesis；
4. 不允许为了推进阶段而人工选择 TITLE / redundancy / contamination 等候选；
5. 当前 generation diagnosis 到达 **frozen-evidence attribution ceiling**；
6. 下一步必须经过新的显式 authorization / hypothesis-discrimination design，不能自动生成 V4.8.3，也不能直接 remediation。

---


## Post-V4.8.2 — Next-Workstream Priority Review + Governance Closure

```text
FINAL_ACCEPTED  ·  GOVERNANCE / FROZEN-EVIDENCE PRIORITY REVIEW
NO PRODUCT BASELINE
NO PRODUCT REMEDIATION
```

本阶段不是新的 Product phase，也不是 V4.9–V4.13 中任何一个 workstream 的执行；
它只回答：

> 在 V4.8.2 之后、当前冻结 evidence 与既有 governance contract 下，哪个 candidate
> workstream 应被**推荐为下一治理对象**，以及该 recommendation 的支持强度是什么。

最终治理状态：

```text
POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW =
FINAL_ACCEPTED

R0 = ACCEPTED
R1 / A001-A009 = ACCEPTED
R2 = FULLY_ACCEPTED
R3 = FULLY_ACCEPTED
R4 = FULLY_ACCEPTED
R4_S = FULLY_ACCEPTED_WITH_RECORDED_NONMUTATING_EXECUTION_DEVIATION
R5 = FULLY_ACCEPTED
R6_C = FULLY_ACCEPTED

UNIQUE_LEADER =
WS-13

UNIQUE_LEADER_ESTABLISHED_AT =
P5

RECOMMENDED_NEXT_WORKSTREAM =
WS-13

RECOMMENDATION_SUPPORT =
WEAK

SUPPORT_RESOLUTION_STEP =
S2

NEXT_WORKSTREAM_EXECUTION_AUTHORIZED =
NO

NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED =
NO

PRODUCT_REMEDIATION_AUTHORIZED =
NO

NEXT_STAGE_AUTOMATICALLY_AUTHORIZED =
NO
```

R4 frozen lexicographic priority decision：

```text
P1 = TIED
P2 = TIED
P3 = TIED

P4 = EVALUATED
P4_OUTPUT_SURVIVORS =
WS-11, WS-12, WS-13

P5 = EVALUATED
P5_CURRENT_ACTION_TARGET_COUNTS =
WS-11 = 19
WS-12 = 32
WS-13 = 1

P5_OUTPUT_SURVIVORS =
WS-13

P6 =
NOT_EVALUATED_UNIQUE_LEADER_ALREADY_ESTABLISHED

P7 =
NOT_EVALUATED_UNIQUE_LEADER_ALREADY_ESTABLISHED
```

因此唯一 leader 在 P5 建立。P5 比较的是每个 survivor 的**当前 next permissible action**
所对应的 purpose-scoped target；当时五个 workstream 的 frozen readiness 均为：

```text
R3 / FRESH_ATTRIBUTION
```

WS-13 的 target 为单一 citation-domain case：

```text
cit-001
```

但 support-only rederivation（A008 + A009）进一步确认：

```text
CRITICAL_EVIDENCE_MISSING = NO
DEPENDENCY_GRAPH_UNRESOLVED = NO
LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE = YES
SMALL_EVIDENCE_CHANGE_SENSITIVITY = NOT_ESTABLISHED

SUPPORT_RESOLUTION_STEP = S2
RECOMMENDATION_SUPPORT = WEAK
```

正确解释：

> `WS-13` 是 frozen lexicographic comparator 下的唯一机械 leader；
> 但决定性 target `cit-001` 仍依赖 historical citation evidence，
> latest-state citation attribution 未被机械建立，且没有 governed replayable
> sensitivity proof。因此 recommendation 成立，但 support 只能为 `WEAK`。

永久完整性限定：

```text
R4_PRE_CHANGE_MANIFEST_DIGEST =
NOT_ESTABLISHED

R4S_PRIOR_VALIDATION_PRIORITY_DECISION_CHECK_EXECUTED =
YES

R4S_PRIOR_VALIDATION_PRIORITY_REEXECUTION =
YES

R4S_PRIOR_VALIDATION_EXECUTION_BOUNDARY_DEVIATION =
YES

R4S_PRIOR_VALIDATION_DEVIATION_WAS_READ_ONLY =
YES

R4S_PRIOR_VALIDATION_DEVIATION_MUTATED_STATE =
NO

R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_PRIORITY_SURFACE =
NO

R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_LEADER =
NO

R4S_PRIOR_VALIDATION_DEVIATION_CHANGED_SUPPORT_RESULT =
NO
```

R6 首次 validation 的 stale test pin 也永久保留：

```text
R6_INITIAL_VALIDATION =
246_OF_247_WITH_STALE_R5_TEST_PIN

R6_C_CORRECTION =
PASS

R6_FINAL_VALIDATION =
247_OF_247_PASS
```

其中旧 R5 test 错误地把 historical R4-S pre-change entry count `19663`
同时作为 future live-workspace invariant；R6 合法新增 human report 后 current count
变为 `19664`。R6-C 只修正 historical-vs-current test semantics，未修改历史 anchor，
未改变任何 scientific / priority / support 结论。

冻结摘要：

```text
EFFECTIVE_ANALYSIS_DESIGN_DIGEST =
7a76f3f6e6963bf1851e9a80f53c50fc1abbfe78c9ba56f87818f066b6958552

FROZEN_PRIORITY_SURFACE_DIGEST =
8c6c17cec9d902b31dce3c5fc4f93f201284639dd79b5fcdea47eb6b741b1b08

PRIORITY_DECISION_DIGEST =
0126975a018e65fc839b989349a1f13f276f90aeecd4cb1ad2c92bae65c59662
```

本阶段未改变 Product identity：

```text
production hash changed = NO
Product code modified = NO
runtime DB modified = NO
Golden/evaluator modified = NO
baseline advanced = NO
release advanced = NO
Product metrics recomputed = NO
```

---

# 11. Workspace Relocation Closure

项目已迁移至新的父目录（本机绝对路径不再写入可发布文档；运行时不依赖任何绝对工作区路径）：

```text
<workspace-parent>/
├── Local Database Q&A System本地版v3   （FROZEN）
├── Local Database Q&A System本地版v4   （ACTIVE）
└── Local Database Q&A System上传版     （Publish）
```

已完成：

```text
Workspace Relocation Audit                      （READ-ONLY AUDIT）
Workspace Relocation publication_scan Tooling Fix（TOOLING-ONLY FIX）
```

结果：

```text
database portable
baseline portable
ImportPathPolicy portable
Qdrant persistence unaffected
production state unchanged
```

`publication_scan.py` 已移除旧 `E:\ZCode_ws\...` 硬编码，改为从脚本位置（`Path(__file__)`）动态推导
active workspace；tooling fix 由 `tests/test_publication_scan.py` 校验。

该 tooling fix **不建立 product baseline**，也不改变 `production_source_hash`。

---

# 12. Current Release Checkpoint

已正式发布并接受：

```text
CURRENT_RELEASE            = v4.0.0-alpha.2
RELEASE_TYPE               = GitHub Pre-release（Development Snapshot）
ALPHA_2_RELEASE_ACCEPTANCE = PASS
REMOTE_CI                  = PASS（fresh LF GitHub Actions checkout；699 tests OK）
```

发布历史：

```text
v4.0.0-alpha.1  = published pre-release, CI postcheck FAILED（CRLF/LF hash portability）
                  → SUPERSEDED（tag/commit 不变，release notes 已标注 superseded）
v4.0.0-alpha.2  = current accepted snapshot（修复 hash portability）
```

本次 release 表示：

- 评测体系稳定、可复现；
- Scope/OOS 与 Routing over-trigger 各完成一轮 remediation；
- Embedding Identity / Model Alignment 已正式收编；
- V4.6.2 hash portability formalization 已建立，canonical hash 跨 CRLF/LF 一致；
- baseline governance 与 live hash drift detection 已建立；
- workspace relocation 与 publication tooling portability 已收口；
- publication / release 支线 **CLOSED**。

本次 release **不表示**：

- V4 已达到最终 Product Quality DoD；
- History 已完成；
- Retrieval 已完成；
- Generation completeness 已完成；
- Measurement closure 已完成；
- Citation coverage 已完成。

关于 Document Identity，需要区分**发布时点语义**与**后续诊断结论**：

- `v4.0.0-alpha.2` 发布本身不宣告 Document Identity remediation 完成；
- 后续 V4.7 独立诊断已经在当前 pipeline / V4.7 targets 上得到 `CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS = DISPROVEN`、`DOCUMENT_IDENTITY_ROOT_CAUSE = NOT_PROVEN`；
- 因而当前状态不是“Document Identity 待修复”，而是 `DOCUMENT_IDENTITY_REMEDIATION = BLOCKED / NOT AUTHORIZED`。

---

# 13. Completed Diagnosis Chain — V4.7 → V4.8.2

本节给出当前应由 Master 携带的**最新 Generation / Document-Identity 诊断解释**。
历史阶段的原始结论仍由各自 frozen artifact 保存；本节负责防止把较早阶段的 provisional wording
误当成当前全局科学结论。

## 13.1 V4.7：Document Identity Loss 在 current pipeline 被排除

对象：`md-004` / `md-009` / `md-015`。

V4.7 原判据：

```text
A. canonical title 未进入 final model-visible context
B. canonical title 已进入 final model-visible context，但 model 不输出
```

机械结果：

```text
APPLICATION_REQUEST_TITLE_VISIBILITY = YES_FOR_ALL_TARGETS
EVIDENCE_CONTINUITY                  = PRESERVED_FOR_ALL_TARGETS
FIRST_IDENTITY_LOSS_LAYER            = NONE
```

因此：

```text
CURRENT_PIPELINE_ROOT_CAUSE              = GENERATION
CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS  = DISPROVEN
DOCUMENT_IDENTITY_ROOT_CAUSE             = NOT_PROVEN
DOCUMENT_IDENTITY_MECHANISM_APPLICABLE   = NO
DOCUMENT_IDENTITY_REMEDIATION            = BLOCKED
```

V4.7 当时把 co-present generation pattern 描述为：

```text
MATERIAL_INDEX_REPRESENTATION_BIAS
```

但同时已经明确：

```text
GENERATION_MECHANISM_ISOLATION =
NOT_ESTABLISHED
```

因此该 mechanism name 从未等价于“已隔离的 causal mechanism”。

## 13.2 V4.8：A/B counterfactual 打破“统一 shared mechanism”解释

V4.8 发现：

```text
md-004:
A positive
B positive
A+B positive

md-009:
A negative
B negative
A+B negative

md-015:
A negative
B negative
A+B negative
```

所以当前必须写成：

```text
M1_SHARED_SUPPORT = PARTIAL
M2_SHARED_SUPPORT = PARTIAL

HETEROGENEOUS_RESPONSE_PROFILE = YES
SHARED_CAUSAL_MECHANISM = NOT_ESTABLISHED
MIXED_GENERATION_MECHANISMS = NOT_ESTABLISHED
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
```

不得继续用：

```text
SHARED_GENERATION_MECHANISM =
MATERIAL_INDEX_REPRESENTATION_BIAS
```

作为当前全局已证明结论。

## 13.3 V4.8.1：Explicit membership metadata 不能解释 residual subset

对 `md-009 / md-015`：

```text
G0 = FAIL
G1 = FAIL
DELTA_G = 0
```

因此：

```text
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_CAUSAL_SUPPORT = NO
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_ISOLATED = NO

CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS =
NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION
```

该结论只覆盖：

```text
EXPLICIT_MEMBERSHIP_METADATA_ONLY
```

不覆盖：

```text
physical chunk regrouping
chunk reordering
document-level summarization
all possible aggregation mechanisms
```

## 13.4 V4.8.2：Frozen evidence 不足以形成 governed next hypothesis

V4.8.2 没有新模型 / retrieval / counterfactual evidence。

机械结果：

```text
MD009_MD015_RESIDUAL_SIMILARITY_SCORE = 0.3333
MD009_MD015_RESIDUAL_SIMILARITY = LOW

MD004_TO_RESIDUAL_DIFFERENCE_SCORE = 0.4286
MD004_TO_RESIDUAL_DIFFERENCE = MEDIUM
```

并且：

```text
TOP_CANDIDATE_HYPOTHESIS = null
TOP_CANDIDATE_SUPPORT = null
SHARED_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED
DIRECT_TITLE_PROBE_MECHANICALLY_JUSTIFIED = NOT_ESTABLISHED

NEXT_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED
NEXT_DIAGNOSTIC_PHASE_NUMBER = NOT_ESTABLISHED
NEXT_DIAGNOSTIC_CANDIDATE = NOT_ESTABLISHED
NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO

CAUSAL_MECHANISM_ESTABLISHED = NO
PRODUCT_REMEDIATION_AUTHORIZED = NO
```

## 13.5 Current accepted generation state

截至本 Master 对齐检查点：

```text
CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS =
DISPROVEN

GENERATION_ROOT_CAUSE_FAMILY =
SUPPORTED_FOR_THE_V4_7_TARGET_FAILURES

UNIFIED_SPECIFIC_GENERATION_MECHANISM =
NOT_ESTABLISHED

GENERATION_MECHANISM_ISOLATION =
NOT_ESTABLISHED

SHARED_RESIDUAL_HYPOTHESIS =
NOT_ESTABLISHED

CAUSAL_MECHANISM_ESTABLISHED =
NO

PRODUCT_REMEDIATION_AUTHORIZED =
NO
```

注意：

```text
GENERATION_ROOT_CAUSE_FAMILY
!=
specific causal mechanism isolated

heterogeneous response
!=
mixed mechanisms proven

repair candidate
!=
mechanism proof

diagnostic signal
!=
Product remediation authorization
```

Measurement 轴继续独立：

```text
MEASUREMENT_SEMANTIC_ISSUE =
SUPPORTED
```

Historical 轴继续：

```text
HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO
RELEVANT_PIPELINE_EQUIVALENCE = NOT_ESTABLISHED
HISTORICAL_FAILURE_COMPATIBILITY = STRONGLY_SUPPORTED
HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED
```

不得因 V4.8–V4.8.2 把历史 pipeline equivalence 升级为 proven。

主要机器事实源：

```text
eval/v4_7_document_identity_root_cause.json
eval/v4_8_generation_mechanism_isolation.json
eval/v4_8_1_residual_generation_mechanism_isolation.json
eval/v4_8_2_residual_differential_attribution.json
```

---


## 13.6 Post-V4.8.2 priority review：下一 workstream 已被推荐，但尚未授权

V4.8.2 本身没有形成 next residual hypothesis，因此没有从 Generation 分支自动产生 V4.8.3。
随后独立执行的 Post-V4.8.2 Next-Workstream Priority Review 对五个 candidate workstream
进行 frozen-evidence / lexicographic governance comparison。

接受结果：

```text
WS-09 / V4.9_HISTORY                 = R3 / FRESH_ATTRIBUTION
WS-10 / V4.10_RETRIEVAL             = R3 / FRESH_ATTRIBUTION
WS-11 / V4.11_GENERATION_COMPLETENESS = R3 / FRESH_ATTRIBUTION
WS-12 / V4.12_MEASUREMENT           = R3 / FRESH_ATTRIBUTION
WS-13 / V4.13_CITATION              = R3 / FRESH_ATTRIBUTION

UNIQUE_LEADER =
WS-13

RECOMMENDED_NEXT_WORKSTREAM =
WS-13

RECOMMENDATION_SUPPORT =
WEAK
```

该结果改变的是**治理优先级状态**，不是 Product / scientific diagnosis：

```text
recommended workstream
!=
authorized workstream

R3 / FRESH_ATTRIBUTION
!=
READY_FOR_SEPARATE_EXECUTION

citation priority leader
!=
citation remediation authorization
```

因此当前合法下一步不是直接“修 citation coverage”，而是：

```text
new independent governance stage
→ decide whether to authorize WS-13
→ if authorized, execute only the governed R3 / FRESH_ATTRIBUTION action
→ use fresh current-state evidence to decide any later V4.13 diagnostic /
   measurement / remediation scope
```

在新的独立授权出现前：

```text
NEXT_WORKSTREAM_EXECUTION_AUTHORIZED =
NO

NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED =
NO

PRODUCT_REMEDIATION_AUTHORIZED =
NO
```

---

# 14. Candidate Next-phase Sequence

以下为 **CURRENT CANDIDATE SEQUENCE / AUTHORIZATION MAP**。
它不是不可修改的硬承诺，也不表示任何候选阶段已经被授权。

## 14.1 Immediate next governance state

Post-V4.8.2 priority review 已完成，所以当前不再处于“下一 workstream 尚未确定”的状态。

当前必须区分：

```text
RECOMMENDED_NEXT_WORKSTREAM =
WS-13

RECOMMENDATION_SUPPORT =
WEAK

WS_13_READINESS =
R3

WS_13_NEXT_PERMISSIBLE_ACTION =
FRESH_ATTRIBUTION

NEXT_WORKSTREAM_EXECUTION_AUTHORIZED =
NO

NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED =
NO

PRODUCT_REMEDIATION_AUTHORIZED =
NO

NEXT_STAGE_AUTOMATICALLY_AUTHORIZED =
NO
```

因此：

> 下一治理阶段应围绕“是否授权 WS-13 / Candidate V4.13 的 fresh citation attribution”
> 建立新的独立 protocol；不得把本次 priority recommendation 直接解释为
> Citation remediation / coverage implementation 的执行许可。

V4.8.2 Generation residual branch 的科学状态仍保持：

```text
NEXT_RESIDUAL_HYPOTHESIS =
NOT_ESTABLISHED

NEXT_DIAGNOSTIC_PHASE_NUMBER =
NOT_ESTABLISHED

NEXT_DIAGNOSTIC_CANDIDATE =
NOT_ESTABLISHED

GENERATION_MECHANISM_ISOLATION =
NOT_ESTABLISHED
```

即 priority review 选择 WS-13，不等于在 Generation branch 内生成了新的 hypothesis。

当前不存在自动授权的：

```text
V4.8.3
V4.9
V4.10
V4.11
V4.12
V4.13 execution/remediation
```

下一阶段必须以新的 governance authorization 为起点。

## 14.2 Candidate V4.9 — History Resolution

```text
AUTHORIZATION_STATUS = NOT_AUTHORIZED
```

该编号继续保留给既有 roadmap candidate，不因 V4.8.1 / V4.8.2 子阶段自动顺延。

重点历史 residual：

```text
mt-011
```

已知 malformed rewrite：

```text
CDMA的那
```

以及 V4.4 已记录但未修复的：

```text
mt-006
rewrite → OFDM
```

但 V4.9 仍只是 candidate。

执行前必须：

```text
fresh preflight
fresh current-state attribution
explicit V4.9 authorization
```

不得因为 V4.8.2 没有形成 generation hypothesis 就自动进入 V4.9。

## 14.3 Candidate V4.10 — Retrieval Remediation

```text
AUTHORIZATION_STATUS = NOT_AUTHORIZED
```

历史候选包括：

```text
cit-013
qa-020
qa-030
cmp-001
loc-008
loc-013
loc-015
```

重点为 RRF ranking / evidence-delivery miss。

由于 V4.6 → V4.7 已改变 Document Identity 解释，且 V4.8.x 又进一步改变 Generation attribution，
这些 case 在真正授权 V4.10 前必须基于**最新 product state**重新确认：

```text
true retrieval miss
vs
generation omission
vs
history failure
vs
measurement issue
vs
multi-cause
```

不得照抄 V4.6 attribution。

## 14.4 Candidate V4.11 — Generation Completeness

```text
AUTHORIZATION_STATUS = NOT_AUTHORIZED
```

历史 residual family 包括：

```text
qa-040
md-019
cit-001
mt-006
...
```

典型：

```text
evidence delivered
but answer omitted / refused / pointer-only
```

但当前必须区分两个层次：

```text
A. V4.7–V4.8.2 的 document-identity / residual mechanism diagnosis branch
B. broader generation completeness residuals
```

V4.8.2 没有建立 unified specific mechanism，因此 V4.11 不得假设：

```text
one already-proven generation fix
```

可以统一修复所有 generation failures。

在进入 V4.11 前必须：

```text
rerun / reuse latest authorized attribution
define exact generation-completeness target set
separate already-tested A/B/G nulls from new mechanisms
```

## 14.5 Candidate V4.12 — Measurement / Golden / Evaluator Closure

```text
AUTHORIZATION_STATUS = NOT_AUTHORIZED
```

当前 measurement residual 包括：

- V4.7 提出的 **canonical document title vs Golden semantic-role token** 表达差异；
- locate 模板不复述 query concept；
- 序数表达差异；
- 同义词 / paraphrase；
- Golden route 与 deterministic answer contract 冲突。

保持：

```text
Product
!=
Measurement
```

禁止：

```text
降低标准
为单个 case 特判
为提高 metric 修改 expected facts
用 Golden 反向定义 Product behavior
```

只有 mechanically proven measurement defect 才允许改 Golden / evaluator。

## 14.6 Recommended Candidate V4.13 — Citation Alignment / Coverage（WS-13）

当前 priority-review 状态：

```text
WORKSTREAM_ID =
WS-13

CANDIDATE_PHASE_NAMESPACE =
V4.13_CITATION

PRIORITY_STATUS =
RECOMMENDED_NEXT_WORKSTREAM

RECOMMENDATION_SUPPORT =
WEAK

READINESS_CLASS =
R3

NEXT_PERMISSIBLE_ACTION =
FRESH_ATTRIBUTION

AUTHORIZATION_STATUS =
NOT_AUTHORIZED
```

WS-13 被选为唯一 leader 的机械原因是：

```text
P4:
HAS_DIRECT_LINK = YES

P5:
CURRENT_ACTION_TARGET_SOURCE =
FROZEN_R3_DOMAIN_ELIGIBLE_CASE_IDS

CURRENT_ACTION_TARGET_CASE_IDS =
[cit-001]

CURRENT_ACTION_TARGET_CASE_COUNT =
1
```

而同一轮 support rederivation 又确认：

```text
CURRENT_CONFIRMED_CASES =
[]

HISTORICAL_OR_STALE_CASES =
[cit-001]

LEADER_MATERIALLY_DEPENDS_ON_STALE_OR_HISTORICAL_EVIDENCE =
YES

LATEST_STATE_EVIDENCE_MECHANICALLY_TRACEABLE =
NO

RECOMMENDATION_SUPPORT =
WEAK
```

所以当前**不能**直接从：

```text
citation_coverage = 0.4657
target >= 0.80
```

跳到 citation remediation。

新的独立 governance stage 若授权 WS-13，首先应执行：

```text
FRESH_ATTRIBUTION
```

至少重新确认：

1. `cit-001` 在 current product state 下是否仍属于 Citation workstream；
2. 当前 citation defect / alignment issue 是否被 case-specific evidence 机械建立；
3. 是否存在 Product-vs-Citation / Measurement-vs-Citation confound；
4. 当前 failing coverage gate 与 case-specific citation evidence 的可追踪关系；
5. fresh attribution 之后是否存在可机械定义的 separate-execution target。

只有后续独立治理再次明确授权，才允许进入：

```text
citation alignment implementation
multi-evidence citation coverage remediation
citation completion
```

且继续保持：

```text
invalid citation = 0
citation scope violation = 0
F.2 citation safety = PASS
```

不得以破坏 citation safety 换 coverage。

## 14.7 Phase-number namespace rule

当前继续保留：

```text
V4.9  History
V4.10 Retrieval
V4.11 Generation Completeness
V4.12 Measurement
V4.13 Citation
```

作为 candidate naming。

V4.8.x 子阶段：

```text
V4.8
V4.8.1
V4.8.2
```

已完成。

不得自动创建：

```text
V4.8.3
```

除非未来独立 authorization 同时建立：

```text
valid phase number
+
scientific question
+
new factor
+
execution boundary
```

---

# 15. Re-attribution Rule

V4.7 以后每个 product remediation 完成时：

```text
rerun canonical evaluation
→ regenerate residual set
→ perform attribution
→ re-prioritize
```

因此：

```text
V4.9 / V4.10 / V4.11 / V4.12 / V4.13
```

只是当前 candidate naming。

任何阶段都可以因新证据：

- 提前；
- 推迟；
- 被证明无需修改；
- 被重新归类；
- 在确有同根因证据时合并。

但不得无证据混改多个 subsystem。

---

# 16. V4 Final — Unified Product Quality Closure

只有满足以下条件才允许进入 `V4 Final`。

## Evaluation

canonical evaluator / Golden / verifier 全部冻结且可复现。

## Product

所有 high-confidence product failures：

```text
resolved
or
explicitly accepted/deferred with evidence
```

## Regression

必须：

```text
Phase E PASS
F.2 PASS
pure-OOS false_accept = 0
scope leakage = 0
invalid citation = 0
citation scope violation = 0
```

## Quality

最终依据 Contract：

```text
case_exact >= 0.80
fact_recall >= 0.90
false_refusal <= 0.03
citation_coverage >= 0.80
high_conf <= 0.05
```

## Governance

必须：

```text
current baseline
==
live production hash

historical baselines immutable

release artifact provenance complete
```

最终才允许：

```text
V4_PRODUCT_QUALITY = PASS
V4_FINAL = READY
```

---

# 17. Publication vs Development

GitHub publication：

```text
does NOT advance product baseline
```

如果 Publish 只是把当前 V4 byte-equivalent snapshot 同步进 Git：

```text
active V4 production state remains unchanged
```

因此 Development Snapshot 发布完成后，当前 Product baseline 仍为：

```text
CURRENT PRODUCT BASELINE
=
V4_6_2_HASH_PORTABILITY_BASELINE
```

publication 不推进 product baseline；current pointer 仍由：

```text
eval/v4_baseline_lineage.json
```

唯一决定。

当前 release：

```text
CURRENT_RELEASE =
v4.0.0-alpha.2

RELEASE_TYPE =
DEVELOPMENT SNAPSHOT / PRE-RELEASE

REMOTE_CI =
PASS
```

V4.7–V4.8.2 以及 Post-V4.8.2 Next-Workstream Priority Review 均没有执行 Product remediation，因此也没有产生新的 Product baseline。

当前 development / governance 状态：

```text
V4.7   → COMPLETE / CLOSED
V4.8   → COMPLETE / CLOSED
V4.8.1 → COMPLETE / CLOSED
V4.8.2 → COMPLETE / CLOSED / FINAL ACCEPTED

POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW
→ CLOSED / FINAL_ACCEPTED

RECOMMENDED_NEXT_WORKSTREAM =
WS-13

RECOMMENDATION_SUPPORT =
WEAK

WS_13_NEXT_PERMISSIBLE_ACTION =
FRESH_ATTRIBUTION

NEXT_WORKSTREAM_EXECUTION_AUTHORIZED =
NO

NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED =
NO

PRODUCT_REMEDIATION_AUTHORIZED =
NO
```

因此当前开发主线不是：

```text
“publication 完成 → 自动 V4.8.3”
```

也不是：

```text
“V4.8.2 结束 → 自动 V4.9”
```

而是：

```text
latest accepted evidence
→ completed priority review
→ WS-13 recommended with WEAK support
→ new explicit WS-13 governance authorization decision
→ if authorized: FRESH_ATTRIBUTION only
→ any later diagnostic / remediation scope requires its own evidence + authorization
```

无需因为 GitHub publication、diagnosis-only 子阶段或 frozen-evidence analysis 自动移动 Product baseline。

---

# 18. Current Status Summary

```text
Evaluation Integrity                  COMPLETE
Failure Attribution                  COMPLETE / continuously refreshed
Scope/OOS                            COMPLETE
Routing                              COMPLETE
Embedding Identity Alignment         COMPLETE
Baseline Governance                  COMPLETE
Live Production Drift Detection      COMPLETE
Workspace Relocation                 COMPLETE
Publication Tooling Portability      COMPLETE

Documentation Alignment              COMPLETE / aligned through Priority Review R6-C
Publication Safety / Leak Triage     COMPLETE
Publish Workspace Sync Verification  COMPLETE（alpha.2 published; remote CI PASS）
Publication / Release Branch         CLOSED（alpha.2）

Document Identity Loss               DISPROVEN in current pipeline（V4.7 targets）
Document Identity Root Cause         NOT_PROVEN
Document Identity Remediation        BLOCKED / NOT AUTHORIZED

Generation Root-cause Family         SUPPORTED for V4.7 target failures
Specific Shared Generation Mechanism NOT_ESTABLISHED
Generation Mechanism Isolation       NOT_ESTABLISHED
Heterogeneous Generation Response    ESTABLISHED at V4.8 response-profile level
Mixed Generation Mechanisms          NOT_ESTABLISHED

Explicit Membership Metadata         NOT_SUPPORTED on md-009/md-015（V4.8.1）
Broader Aggregation Hypothesis       NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION
                                     （not globally disproven）

Frozen-evidence Differential         COMPLETE / FINAL ACCEPTED（V4.8.2）
md-009 vs md-015 similarity          LOW（0.3333）
md-004 vs residual difference        MEDIUM（0.4286）
Top Candidate Hypothesis             NONE / null
Shared Residual Hypothesis           NOT_ESTABLISHED
Direct-title Probe Justification     NOT_ESTABLISHED
Causal Mechanism Established         NO

Next-Workstream Priority Review       FINAL_ACCEPTED
Unique Leader                        WS-13
Recommended Next Workstream          WS-13
Recommendation Support               WEAK
WS-13 Readiness                      R3
WS-13 Next Permissible Action        FRESH_ATTRIBUTION
Next Workstream Execution            NOT AUTHORIZED

History                              CANDIDATE V4.9 / NOT AUTHORIZED
Retrieval                            CANDIDATE V4.10 / NOT AUTHORIZED
Generation Completeness              CANDIDATE V4.11 / NOT AUTHORIZED
Measurement Closure                  CANDIDATE V4.12 / NOT AUTHORIZED
Citation Coverage                    RECOMMENDED WS-13 / CANDIDATE V4.13 / NOT AUTHORIZED
Unified Final Closure                PENDING
```

当前产品与治理状态：

```text
V4 DEVELOPMENT        = ACTIVE
V4 FINAL              = NOT YET

PRODUCT QUALITY DOD   = NOT_YET_PASS

RELEASE TYPE          = DEVELOPMENT SNAPSHOT / PRE-RELEASE
CURRENT_RELEASE       = v4.0.0-alpha.2
REMOTE_CI             = PASS

CURRENT_BASELINE      = V4_6_2_HASH_PORTABILITY_BASELINE
PRODUCT_METRICS_SOURCE=
V4_6_1_EMBEDDING_IDENTITY_BASELINE

CANONICAL_PRODUCTION_HASH =
108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c

LATEST_COMPLETED_DIAGNOSIS =
V4.8.2

LATEST_COMPLETED_GOVERNANCE_REVIEW =
POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW

POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW =
FINAL_ACCEPTED

UNIQUE_LEADER =
WS-13

RECOMMENDED_NEXT_WORKSTREAM =
WS-13

RECOMMENDATION_SUPPORT =
WEAK

SUPPORT_RESOLUTION_STEP =
S2

WS_13_READINESS =
R3

WS_13_NEXT_PERMISSIBLE_ACTION =
FRESH_ATTRIBUTION

NEXT_WORKSTREAM_EXECUTION_AUTHORIZED =
NO

NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED =
NO

PRODUCT_REMEDIATION_AUTHORIZED =
NO

NEXT_STAGE_AUTOMATICALLY_AUTHORIZED =
NO
```

Generation residual branch 继续保持：

```text
NEXT_RESIDUAL_HYPOTHESIS =
NOT_ESTABLISHED

NEXT_DIAGNOSTIC_PHASE_NUMBER =
NOT_ESTABLISHED

NEXT_DIAGNOSTIC_CANDIDATE =
NOT_ESTABLISHED
```

这与 `RECOMMENDED_NEXT_WORKSTREAM = WS-13` 不冲突：前者描述 V4.8.x generation-residual
hypothesis branch，后者描述独立 priority review 的跨-workstream治理结果。

当前 canonical Full-144 指标仍来自 V4.6.1；V4.6.2 仅改变 portable hash governance，
V4.7–V4.8.2 与 priority review 均未授权重算 Product metrics：

```text
case_exact        = 0.7292    target >= 0.80    NOT PASS
fact_recall       = 0.8535    target >= 0.90    NOT PASS
false_refusal     = 0.0000    target <= 0.03    PASS
citation_coverage = 0.4657    target >= 0.80    NOT PASS
high_conf         = 0.0132    target <= 0.05    PASS

invalid citation  = 0         PASS
scope violation   = 0         PASS
```

面向最终 Contract 的当前剩余量化缺口：

```text
case_exact_gap_to_target        = 0.0708
fact_recall_gap_to_target       = 0.0465
citation_coverage_gap_to_target = 0.3343
```

这些 gap 只用于导航。即使 citation gap 最大，也**不是** WS-13 被选为 leader 的权重依据；
R4 明确禁止 gap-size weighting，WS-13 是由 frozen P1→P5 lexicographic comparator
机械建立的唯一 leader。

因此：

```text
V4 FINAL =
NO

V4_PRODUCT_QUALITY =
NOT_YET_PASS
```

当前总控路线：

```text
completed diagnosis chain
→ Post-V4.8.2 priority review FINAL_ACCEPTED
→ WS-13 recommended / WEAK support
→ new independent WS-13 governance stage
→ decide whether to authorize FRESH_ATTRIBUTION
→ fresh attribution under explicit scope (only if authorized)
→ decide later diagnostic / measurement / remediation action from fresh evidence
→ canonical reevaluation after any authorized Product remediation
→ repeat until Full-144 Product Quality Closure gates pass
```

不得把 candidate numbering、priority recommendation 或 quality-gap 大小当成自动执行授权。

# 19. Phase / Artifact / Test References

| 主题 | 阶段文档 | 机器 artifact | 测试 |
|---|---|---|---|
| Evaluation Integrity | `docs/V4_EVALUATION_INTEGRITY.md` | `eval/v4_initial_baseline.json` | `tests/test_v4_evaluation_integrity.py` |
| Failure Attribution | `docs/V4_FAILURE_ATTRIBUTION.md` | `eval/v4_failure_attribution.json` / `eval/v4_attribution_closure.json` | `tests/test_v4_attribution_integrity.py` / `tests/test_v4_attribution_closure.py` |
| Scope/OOS (V4.4) | `docs/V4_SCOPE_OOS_REMEDIATION.md` | `eval/v4_4_scope_remediation_baseline.json` / `eval/v4_scope_remediation.json` | `tests/test_v4_scope_oos_remediation.py` |
| Routing (V4.5) | `docs/V4_ROUTING_REMEDIATION.md` | `eval/v4_5_routing_baseline.json` / `eval/v4_routing_remediation.json` | `tests/test_v4_routing_remediation.py` |
| Post-Routing Attribution (V4.6) | `docs/V4_POST_ROUTING_ATTRIBUTION.md` | `eval/v4_6_post_routing_attribution.json` / `eval/v4_6_post_routing_evidence.json` | `tests/test_v4_6_post_routing_attribution.py` |
| Embedding Identity (V4.6.1) | `docs/V4_EMBEDDING_IDENTITY_ALIGNMENT.md` | `eval/v4_6_1_embedding_identity_baseline.json` / `eval/v4_6_1_embedding_identity_formalization.json` | `tests/test_embedding_identity.py` / `tests/test_live_production_hash_guard.py` |
| Hash Portability (V4.6.2) | — | `eval/v4_6_2_hash_portability_baseline.json` | `tests/test_v4_6_2_hash_portability.py` / `tests/test_live_production_hash_guard.py` |
| Baseline Lineage | `docs/V4_INITIAL_BASELINE.md` | `eval/v4_baseline_lineage.json` | `tests/test_v4_baseline_lineage.py` |
| Document Identity (V4.7) | `docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md` / `docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md` | `eval/v4_7_document_identity_root_cause.json` | `tests/test_v4_7_document_identity_diagnosis.py` |
| Generation Mechanism Isolation (V4.8) | `docs/V4_8_GENERATION_MECHANISM_ISOLATION.md` | `eval/v4_8_generation_mechanism_isolation.json` | `tests/test_v4_8_generation_mechanism_diagnosis.py` |
| Residual Explicit Membership (V4.8.1) | `docs/V4_8_1_RESIDUAL_GENERATION_MECHANISM_ISOLATION.md` | `eval/v4_8_1_preflight_snapshot.json` / `eval/v4_8_1_residual_generation_mechanism_isolation.json` | `tests/test_v4_8_1_residual_generation_diagnosis.py` |
| Residual Differential Attribution (V4.8.2) | `docs/V4_8_2_RESIDUAL_DIFFERENTIAL_ATTRIBUTION.md` | `eval/v4_8_2_preflight_snapshot.json` / `eval/v4_8_2_analysis_design_amendment_001.json` / `eval/v4_8_2_analysis_design_amendment_002.json` / `eval/v4_8_2_analysis_design_amendment_003.json` / `eval/v4_8_2_residual_differential_attribution.json` | `tests/test_v4_8_2_residual_differential.py` |
| Post-V4.8.2 Next-Workstream Priority Review | `docs/V4_POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW.md` | `eval/v4_post_v4_8_2_priority_review_preflight.json` / `eval/v4_post_v4_8_2_priority_review_design_amendment_001.json` … `009.json` / `eval/v4_post_v4_8_2_next_workstream_priority_review.json` | `tests/test_v4_post_v4_8_2_priority_review.py` |
| Product Quality Contract | `docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md` | `eval/v3_quality_acceptance.json` | `tests/test_quality_acceptance.py` |
| Relocation / publication tooling | `KB-V4_Workspace_Relocation_Audit.md`（父目录） | — | `tests/test_publication_scan.py` |

## 19.1 Current frozen identity anchors for V4.8.x

关键 frozen artifact identities（用于导航与审计；若仓库中 machine artifact 提供更高位阶事实，以 machine artifact 为准）：

```text
V4.8 machine artifact:
eval/v4_8_generation_mechanism_isolation.json
SHA256 =
72eaa33f024f9e7f6086149a075b2ae11532bd8dcad7c9fd1890997ae3b66397

V4.8.1 machine artifact:
eval/v4_8_1_residual_generation_mechanism_isolation.json
SHA256 =
3b94017ecb67f68cdb45a2315410f11c5e5d5700c7443b5af98e903af62de5cc

V4.8.2 machine artifact:
eval/v4_8_2_residual_differential_attribution.json
SHA256 =
47e7155badfcecfb03eb48b0f530c12a3f5d0eb03c20918290e91f5f175da470

V4.8.2 immutable preflight:
eval/v4_8_2_preflight_snapshot.json
SHA256 =
96c4f84228121f8bae58f94a69089c55423e3c56bc5d8a2c8afe84945b8c4785
```

V4.8.2 effective design lineage：

```text
snapshot
→ amendment_001
→ amendment_002
→ amendment_003
```

当前 effective design / lower-layer derivation identity 必须区分：

```text
CURRENT_EFFECTIVE_DESIGN_DIGEST =
0ab714e058644529e1b662dca6a8fe29d1a90a4a0a10e952065d8f5fe9449db4

LOWER_LAYER_DERIVATION_DESIGN_DIGEST =
4904bf3fac28ec7361935c355e58297c0667741ee63403091df2e4871f97c038
```

不得把两个 digest 合并解释。

---


## 19.2 Current frozen identity anchors for Post-V4.8.2 Priority Review

```text
Human report:
docs/V4_POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW.md
SHA256 =
da463797e160210e507be3980207eb3a3f69a8a5f401e288b7bef7d91879fc6d

Machine artifact:
eval/v4_post_v4_8_2_next_workstream_priority_review.json
SHA256 =
d80053040f4bbb55f48a95050528f5f3933e408a079888ee6d962e7113752670

Analysis harness:
scripts/analyze_v4_post_v4_8_2_priority_review.py
SHA256 =
3bab1662bf19fa7f084f88431c0ec852ded79c51195a1f2d720edca7510983e2

Final tests after R6-C:
tests/test_v4_post_v4_8_2_priority_review.py
SHA256 =
2c9c96e3c9eb494ee3d5b74545106053a8d15f5296826c8b2f4fd58d891d0da9

A009:
eval/v4_post_v4_8_2_priority_review_design_amendment_009.json
SHA256 =
78a936b4922394071686137e4ed506bef33f8a1cae2b1e93b0aa166525a15410
```

Effective design and accepted final-decision identities：

```text
EFFECTIVE_ANALYSIS_DESIGN_DIGEST =
7a76f3f6e6963bf1851e9a80f53c50fc1abbfe78c9ba56f87818f066b6958552

FROZEN_PRIORITY_SURFACE_DIGEST =
8c6c17cec9d902b31dce3c5fc4f93f201284639dd79b5fcdea47eb6b741b1b08

PRIORITY_DECISION_DIGEST =
0126975a018e65fc839b989349a1f13f276f90aeecd4cb1ad2c92bae65c59662
```

R6-C final test state：

```text
R6_INITIAL_VALIDATION =
246_OF_247_WITH_STALE_R5_TEST_PIN

R6_C_CORRECTION =
PASS

R6_FINAL_VALIDATION =
247_OF_247_PASS
```

这些 identity 仅记录本次 governance review 的 frozen audit state，不推进 Product baseline。

---

> ## Master Alignment Note — Post-V4.8.2 Priority Review Final Closure
>
> 当前 Master 已同步到：
>
> ```text
> V4.8.2 = COMPLETE / CLOSED / FINAL ACCEPTED
>
> POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW =
> FINAL_ACCEPTED
>
> R6_C_FINAL_VALIDATION =
> 247_OF_247_PASS
> ```
>
> 保持不变的 Product identity：
>
> ```text
> CURRENT_RELEASE =
> v4.0.0-alpha.2
>
> CURRENT_BASELINE =
> V4_6_2_HASH_PORTABILITY_BASELINE
>
> PRODUCT_METRICS_SOURCE =
> V4_6_1_EMBEDDING_IDENTITY_BASELINE
>
> CANONICAL_PRODUCTION_HASH =
> 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
> ```
>
> 最近完成的科学诊断链：
>
> ```text
> V4.7   Document Identity Root-Cause Confirmation
>   ↓
> V4.8   Generation / Prompt-Evidence Framing Mechanism Isolation
>   ↓
> V4.8.1 Explicit Document-Membership Representation Isolation
>   ↓
> V4.8.2 Frozen-evidence Residual Differential Attribution
> ```
>
> 随后完成的跨-workstream治理决策：
>
> ```text
> UNIQUE_LEADER =
> WS-13
>
> RECOMMENDED_NEXT_WORKSTREAM =
> WS-13
>
> RECOMMENDATION_SUPPORT =
> WEAK
>
> SUPPORT_RESOLUTION_STEP =
> S2
>
> WS_13_READINESS =
> R3
>
> WS_13_NEXT_PERMISSIBLE_ACTION =
> FRESH_ATTRIBUTION
> ```
>
> 当前授权边界：
>
> ```text
> NEXT_WORKSTREAM_EXECUTION_AUTHORIZED =
> NO
>
> NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED =
> NO
>
> PRODUCT_REMEDIATION_AUTHORIZED =
> NO
>
> NEXT_STAGE_AUTOMATICALLY_AUTHORIZED =
> NO
>
> RECOMMENDATION_IS_AUTHORIZATION =
> NO
> ```
>
> Generation branch 的科学边界继续保持：
>
> ```text
> CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS =
> DISPROVEN
>
> GENERATION_MECHANISM_ISOLATION =
> NOT_ESTABLISHED
>
> SHARED_RESIDUAL_HYPOTHESIS =
> NOT_ESTABLISHED
>
> CAUSAL_MECHANISM_ESTABLISHED =
> NO
>
> NEXT_RESIDUAL_HYPOTHESIS =
> NOT_ESTABLISHED
> ```
>
> 因此新的治理阶段应从：
>
> ```text
> "是否授权 WS-13 / Candidate V4.13 的 FRESH_ATTRIBUTION"
> ```
>
> 开始，而不是直接启动 Citation remediation。
>
> 本次 Master 更新仍仅为 governance / documentation alignment：
>
> ```text
> Product code modified = NO
> production prompt modified = NO
> retrieval/ranking modified = NO
> runtime DB modified = NO
> Golden/evaluator modified = NO
> citation product semantics modified = NO
> baseline changed = NO
> Product metrics recomputed = NO
> publication performed = NO
> ```
