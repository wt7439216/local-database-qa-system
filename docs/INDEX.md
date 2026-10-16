# docs — 文档导航索引

> 本文件是 `docs/` 的**逻辑导航**，不复制其它文档正文。
> 用于区分：当前权威文档 / 当前发布文档 / 当前诊断参考 / 历史阶段证据 / 机器可读证据。
>
> 文档沿用现有路径，目录重排留作未来独立工作。公开路径处理与历史证据重放边界见 [发布说明](V4_RELEASE_SNAPSHOT.md)。

### Current cold-start pointers（冷启动先读）

```text
active development            = V4 本地版；本次公开源码为冻结候选的发布副本
current state entry           = V4_CURRENT_STATE.md（2026-10-16）
current governance baseline   = V4_20261015_LOCAL_CANDIDATE_BASELINE（独立Full144，质量FAIL）
product metrics source        = v4_local_candidate_full144_20261015.json（144条新答案，质量FAIL）
current source snapshot       = v4.0.0-alpha.3（Development Snapshot / Pre-release，NOT V4 Final）
release / remote CI status    = GitHub Releases / Actions 对应 tag、commit 的实际结果
latest completed diagnosis    = V4.8.2 Closure / frozen-evidence attribution ceiling
latest completed governance   = Post-V4.8.2 Priority Review（WS-13 recommendation，support WEAK）
local engineering record      = 2026-10-16；1707 tests / 0 failures / 0 errors / 26 skips
public checkout validation    = 独立 fresh checkout 实测；不能沿用本地测试数或跳过数
current user task             = PUB-01 / PUB-02（公开扫描、同步及源码发布）
current WS-13 status           = V4_CURRENT_STATE.md（实现、重绑定、真实观察、归因的实际进度）
historical Master checkpoint  = 2026-09-16（保留当时授权状态；不代表本轮任务未获用户要求）
```

---

## 1. Current Canonical Docs（当前权威文档）

| 文档 | 用途 |
|---|---|
| [`V4_PROD_EVAL_REL_20261015.md`](V4_PROD_EVAL_REL_20261015.md) | 本轮产品修复、新源码身份、统一质量评测及 EXE 交付记录。 |
| [`V4_CURRENT_STATE.md`](V4_CURRENT_STATE.md) | **当前本地开发入口**：产品基线与指标时间、工程恢复、WS-13 有效设计及接受证据、EXE 与发布状态。 |
| [`V4_MASTER_REQUIREMENTS_AND_ROADMAP.md`](V4_MASTER_REQUIREMENTS_AND_ROADMAP.md) | V4 Must/Should/Deferred、baseline lineage、Gate、路线与 V4 Final 条件；正文保留 2026-09-16 历史治理检查点，当前进度从顶部入口读取。 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 当前**真实架构**（查询流 / Router / Scope / Retrieval / Embedding Identity / 后端 / Citation / 评测 / 治理）；不含 roadmap。 |
| [`../README.md`](../README.md) | 项目对外第一入口：当前状态、模型依赖、快速启动、质量状态、文档导航。 |
| [`../本地使用说明.md`](../本地使用说明.md) | 本地运行 / 配置 / 排错 / 手机访问。 |

## 2. Current Release Docs（当前发布文档）

| 文档 | 用途 |
|---|---|
| [`V4_PUBLICATION_20261016.md`](V4_PUBLICATION_20261016.md) | PUB-01 / PUB-02：实际发布范围、扫描同步规则、公开派生身份、历史原字节不可重放及新 CI 的证据边界。 |
| [`V4_RELEASE_SNAPSHOT.md`](V4_RELEASE_SNAPSHOT.md) | alpha.3 Development Snapshot：源码身份、新 Full144、未达标项、公开证据边界、CI 与本地包范围。 |
| [`../CHANGELOG.md`](../CHANGELOG.md) | 版本变更记录（V4 alpha + 历史）。 |

## 3. Current Diagnostic Reference（当前诊断参考）

> ⚠️ 这些是 **phase / reference evidence**，记录特定阶段的机械证据，**不是当前 master 状态**。
> 当前进度以 `V4_CURRENT_STATE.md` 及其链接的机器证据为准；Master 历史正文的授权字段保持当时事实。

| 文档 | 角色 |
|---|---|
| [`V4_CURRENT_STATE.md`](V4_CURRENT_STATE.md) | WS-13 本轮实现、有效规则、真实观察与归因的统一入口；任务进行中不等于科学结论已经形成。 |
| [`V4_8_2_RESIDUAL_DIFFERENTIAL_ATTRIBUTION.md`](V4_8_2_RESIDUAL_DIFFERENTIAL_ATTRIBUTION.md) | 最近完成的诊断阶段：到达 frozen-evidence attribution ceiling，未形成可发出的下一 residual hypothesis。 |
| [`V4_POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW.md`](V4_POST_V4_8_2_NEXT_WORKSTREAM_PRIORITY_REVIEW.md) | 最近完成的路线评审：推荐 WS-13，readiness `R3 / FRESH_ATTRIBUTION`，支持度 `WEAK`；推荐本身不产生执行或修复授权。 |
| [`V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md`](V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md) | V4.7 冻结证据：Document Identity Loss = `DISPROVEN`；Measurement semantic issue = `SUPPORTED`；阶段性 Generation 解释须结合后续结案边界。 |
| [`V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md`](V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md) | V4.7 当时的文档对齐审计报告。 |
| [`V4_EMBEDDING_IDENTITY_ALIGNMENT.md`](V4_EMBEDDING_IDENTITY_ALIGNMENT.md) | V4.6.1 embedding identity 收编证据（current governance baseline `V4_6_2` 的 parent provenance）。 |

## 4. Historical Phase Evidence（历史阶段证据）

> 记录当时事实，**不因当前状态变化而改写**。仅在有客观错误时修正。

| 文档 | 角色 |
|---|---|
| [`V4_EVALUATION_INTEGRITY.md`](V4_EVALUATION_INTEGRITY.md) | V4.2 canonical evaluator / initial baseline 证据。 |
| [`V4_FAILURE_ATTRIBUTION.md`](V4_FAILURE_ATTRIBUTION.md) | V4.3 failure attribution 重建证据。 |
| [`V4_INITIAL_BASELINE.md`](V4_INITIAL_BASELINE.md) | V4 initial baseline 记录。 |
| [`V4_SCOPE_OOS_REMEDIATION.md`](V4_SCOPE_OOS_REMEDIATION.md) | V4.4 Scope/OOS false-refusal remediation 证据。 |
| [`V4_ROUTING_REMEDIATION.md`](V4_ROUTING_REMEDIATION.md) | V4.5 routing over-trigger remediation 证据。 |
| [`V4_POST_ROUTING_ATTRIBUTION.md`](V4_POST_ROUTING_ATTRIBUTION.md) | V4.6 post-routing residual 归因快照（**历史**：其 `DOCUMENT_IDENTITY_FAILURE` primary 解释已被 V4.7 强挑战；artifact 保持不可变，不再作为 current 优先级依据）。 |
| `V3_*`（见下） | V3 冻结阶段的文档集（历史继承资料）。 |

V3 历史文档（`V3_*`，均为历史阶段记录）：

```text
V3_MASTER_REQUIREMENTS_AND_STATUS.md     V3 需求/实现/待办总清单（历史）
V3_FINAL_BASELINE.md                     V3 冻结锚点
V3_QUALITY_ACCEPTANCE_CONTRACT.md        V3 质量接受合同（Target 档，仍为当前 Gate 依据）
V3_DOD_SCOPE_AMENDMENT.md                V3 DoD scope 修订（deferred 非阻断项来源）
V3_PHASE_E_ROUTER_DECISION.md            V3 Phase E Router 决策
V3_PHASE_F3_CITATION_DECISION.md         V3 Phase F.3 语义引用决策（DEFER_L2）
V3_PHASE_F4_RELEASE_GATE.md              V3 Phase F.4 release gate
V3_PHASE_F4.1_CLOSURE.md                 V3 Phase F.4.1 收口
V3_RUNTIME_LIBRARY_DECISION.md           V3 运行时库身份决策
V3_SCHEMA_IMPACT_NOTE_PHASE_D.md         V3 Phase D schema 影响说明
V3_PROGRESS.md                           V3 进度记录
V3_IMPROVEMENT_PLAN.md                   V3 改进方案（历史建议）
```

其它：

```text
deferred_meta_queries.json               冻结的 deferred-metadata 查询集（数据）
reference/本地知识库问答系统_v3_详细改进方案.docx   历史参考材料
```

## 5. Machine-readable Evidence（机器可读证据）

> 下列 artifact 是**机器事实源**，其位阶高于任何 prose 文档。

| Artifact | 角色 |
|---|---|
| [`../eval/v4_baseline_lineage.json`](../eval/v4_baseline_lineage.json) | baseline lineage 与 current pointer（唯一权威指针）。 |
| [`../eval/v4_local_candidate_full144_20261015.json`](../eval/v4_local_candidate_full144_20261015.json) | **当前产品指标来源**：新候选 144 条答案，2026-10-16 完成；三项质量门槛 FAIL。 |
| [`../eval/v4_prod01_cache_consistency_source_baseline_20261015.json`](../eval/v4_prod01_cache_consistency_source_baseline_20261015.json) | PROD-01 缓存一致性源码阶段；没有另行 Full144。 |
| [`../eval/v4_prod02_numeric_material_header_source_baseline_20261015.json`](../eval/v4_prod02_numeric_material_header_source_baseline_20261015.json) | PROD-02 数字材料头源码阶段，当前候选 production hash 来源。 |
| [`../eval/v4_product_20261015_source_revision.json`](../eval/v4_product_20261015_source_revision.json) | 产品工作源码修订及历史档案 provenance；公开派生字节与私有原件分别核验。 |
| [`../eval/v4_6_2_hash_portability_baseline.json`](../eval/v4_6_2_hash_portability_baseline.json) | **历史 hash portability 基线**及 canonical production hash，不再是 current pointer。 |
| [`../eval/v4_6_1_embedding_identity_baseline.json`](../eval/v4_6_1_embedding_identity_baseline.json) | **历史产品指标**：旧 canonical Full144；V4.6.2 沿用它，不是本次新测量。 |
| [`../eval/v4_7_document_identity_root_cause.json`](../eval/v4_7_document_identity_root_cause.json) | **V4.7 closure 机器事实源**：Document Identity diagnosis + Product/Measurement 分轴 taxonomy + closure gates。 |
| [`../eval/v4_6_post_routing_attribution.json`](../eval/v4_6_post_routing_attribution.json) | V4.6 归因与优先级排序（**历史快照**；其 document-identity 解释已被 V4.7 强挑战，不再是 current next-phase 依据）。 |
| [`../eval/v4_8_2_residual_differential_attribution.json`](../eval/v4_8_2_residual_differential_attribution.json) | V4.8.2 冻结诊断事实源。 |
| [`../eval/v4_post_v4_8_2_next_workstream_priority_review.json`](../eval/v4_post_v4_8_2_next_workstream_priority_review.json) | Priority Review 冻结结论；本轮授权记录另列于当前状态入口。 |
| [`../eval/v4_engineering_recovery_20261014.json`](../eval/v4_engineering_recovery_20261014.json) | STATE-01 / ENG-01..04 工程身份登记；不是新产品或科学基线。 |
| [`../eval/v4_ws13_citation_fresh_attribution_preflight.json`](../eval/v4_ws13_citation_fresh_attribution_preflight.json) | WS-13 G0 原始 preflight。 |
| [`../eval/v4_ws13_citation_fresh_attribution_design.json`](../eval/v4_ws13_citation_fresh_attribution_design.json) | WS-13 G1 base；与 A001 / FC1 组成设计链，单独 base 不代表完整接受。 |
| [`../eval/v4_ws13_citation_fresh_attribution_design_amendment_001.json`](../eval/v4_ws13_citation_fresh_attribution_design_amendment_001.json) | G1 A001 修订，保留其写入时阶段字段。 |
| [`../eval/v4_ws13_citation_fresh_attribution_design_amendment_001_boundary_correction.json`](../eval/v4_ws13_citation_fresh_attribution_design_amendment_001_boundary_correction.json) | G1 A001 FC1 边界修正；外部验证状态与冻结正文分别记录。 |
| [`../eval/v4_ws13_canonical_telemetry_permission_rule.json`](../eval/v4_ws13_canonical_telemetry_permission_rule.json) | 历史 TPR1；观察器及测试绑定已过期，真实执行以本轮重新绑定的有效规则为准。 |

---

## 6. 未来目录重排建议（仅建议，未实施）

为避免破坏引用，本轮**未**建立以下物理目录；未来可在独立授权下考虑：

```text
docs/
├── INDEX.md
├── ARCHITECTURE.md
├── V4_MASTER_REQUIREMENTS_AND_ROADMAP.md
├── V4_RELEASE_SNAPSHOT.md
├── current-evidence/     （当前诊断/归因参考）
├── phase-history/        （V4 阶段证据）
└── historical/           （V3 历史文档）
```
