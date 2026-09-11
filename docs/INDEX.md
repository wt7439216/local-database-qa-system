# docs — 文档导航索引

> 本文件是 `docs/` 的**逻辑导航**，不复制其它文档正文。
> 用于区分：当前权威文档 / 当前发布文档 / 当前诊断参考 / 历史阶段证据 / 机器可读证据。
>
> **本轮不移动任何文件**（避免破坏脚本/测试/文档间的相对引用与发布前 diff）。目录重排留作未来独立授权。

---

## 1. Current Canonical Docs（当前权威文档）

| 文档 | 用途 |
|---|---|
| [`V4_MASTER_REQUIREMENTS_AND_ROADMAP.md`](V4_MASTER_REQUIREMENTS_AND_ROADMAP.md) | **V4 权威总控**：Must/Should/Deferred、当前状态、baseline lineage、Gate、路线与 V4 Final 条件。 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 当前**真实架构**（查询流 / Router / Scope / Retrieval / Embedding Identity / 后端 / Citation / 评测 / 治理）；不含 roadmap。 |
| [`../README.md`](../README.md) | 项目对外第一入口：当前状态、模型依赖、快速启动、质量状态、文档导航。 |
| [`../本地使用说明.md`](../本地使用说明.md) | 本地运行 / 配置 / 排错 / 手机访问。 |

## 2. Current Release Docs（当前发布文档）

| 文档 | 用途 |
|---|---|
| [`V4_RELEASE_SNAPSHOT.md`](V4_RELEASE_SNAPSHOT.md) | 本次 Development Snapshot 发布说明（baseline / 模型 / 指标 / 已完成 / 未完成）。 |
| [`../CHANGELOG.md`](../CHANGELOG.md) | 版本变更记录（V4 alpha + 历史）。 |

## 3. Current Diagnostic / Attribution Reference（当前诊断 / 归因参考）

> ⚠️ 这些是 **phase / reference evidence**，记录特定阶段的机械证据，**不是当前 master 状态**。
> 当前权威状态一律以 `V4_MASTER_REQUIREMENTS_AND_ROADMAP.md` 为准。

| 文档 | 角色 |
|---|---|
| [`V4_POST_ROUTING_ATTRIBUTION.md`](V4_POST_ROUTING_ATTRIBUTION.md) | V4.6 post-routing residual 归因证据快照（当前优先级排序的来源）。 |
| [`V4_EMBEDDING_IDENTITY_ALIGNMENT.md`](V4_EMBEDDING_IDENTITY_ALIGNMENT.md) | V4.6.1 embedding identity 收编证据（当前 baseline 的来源）。 |

## 4. Historical Phase Evidence（历史阶段证据）

> 记录当时事实，**不因当前状态变化而改写**。仅在有客观错误时修正。

| 文档 | 角色 |
|---|---|
| [`V4_EVALUATION_INTEGRITY.md`](V4_EVALUATION_INTEGRITY.md) | V4.2 canonical evaluator / initial baseline 证据。 |
| [`V4_FAILURE_ATTRIBUTION.md`](V4_FAILURE_ATTRIBUTION.md) | V4.3 failure attribution 重建证据。 |
| [`V4_INITIAL_BASELINE.md`](V4_INITIAL_BASELINE.md) | V4 initial baseline 记录。 |
| [`V4_SCOPE_OOS_REMEDIATION.md`](V4_SCOPE_OOS_REMEDIATION.md) | V4.4 Scope/OOS false-refusal remediation 证据。 |
| [`V4_ROUTING_REMEDIATION.md`](V4_ROUTING_REMEDIATION.md) | V4.5 routing over-trigger remediation 证据。 |
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
| [`../eval/v4_6_1_embedding_identity_baseline.json`](../eval/v4_6_1_embedding_identity_baseline.json) | 当前 canonical Full-144 指标 + production hash + frozen targets。 |
| [`../eval/v4_6_post_routing_attribution.json`](../eval/v4_6_post_routing_attribution.json) | V4.6 归因与优先级排序（当前 next-phase 依据）。 |

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
