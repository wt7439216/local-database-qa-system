# KB-V4 — Master Requirements & Roadmap

> **文档角色**：KB-V4 当前开发总控文档（authoritative prose-level master）。
> **适用范围**：本地数据库问答系统 / KB-V4。
> **当前状态**：V4 Development Active；尚未达到 V4 Final Product Quality DoD。
> **当前产品基线**：`V4_6_2_HASH_PORTABILITY_BASELINE`。
> **当前 canonical production_source_hash**：`108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c`。
> **历史 raw (CRLF) production hash（V4.6.1 provenance）**：`7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a`。
> **当前下一产品阶段**：`V4.7 — Document Identity Remediation`。
>
> Source-of-truth 优先级：
>
> `code / tests / machine-readable eval artifacts`
> `>`
> `Product Quality Contract / baseline lineage / actual runtime evaluation outputs`
> `>`
> `阶段 evidence / phase reports`
> `>`
> `本 Master prose`
>
> 本文用于导航、状态汇总与路线治理；若与机器可读 artifact 冲突，以更高位阶事实源为准。
> 全文所有机器可核对数值在本轮由现场重算 / 直接读取 artifact 确认，未手工抄写。

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

至少收口已被证明存在的：

- Scope false refusal；
- Routing over-trigger；
- Document Identity；
- Multi-turn History；
- true Retrieval miss；
- Generation completeness。

Citation 是否进入正式 product remediation，由后续 residual evidence 决定。

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

当前 V4.6.1 canonical Full-144（直接读取 `eval/v4_6_1_embedding_identity_baseline.json`）：

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

> 阶段角色区分：`PRODUCT REMEDIATION` / `READ-ONLY DIAGNOSIS` / `GOVERNANCE / FORMALIZATION` / `TOOLING-ONLY FIX`。
> tooling-only 与 diagnosis-only 阶段 **不** 建立 product baseline。

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

当前 evidence-based priority：

```text
Priority 1  Document Identity
Priority 2  History
Priority 3  Retrieval
Subsequent  Generation
Measurement Golden/Evaluator
Deferred    Citation
```

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
metrics_source                             = V4_6_1_EMBEDDING_IDENTITY_BASELINE
```

建立：

```text
V4_6_2_HASH_PORTABILITY_BASELINE
```

历史 raw hashes 继续作为 provenance 保留（旧 artifact 不被覆盖、不被改写）。

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

当前建议建立一次：

```text
V4 DEVELOPMENT SNAPSHOT
```

推荐 release identity：

```text
v4.0.0-alpha.1
```

并使用 GitHub **Pre-release**。

本次 release 表示：

- 评测体系稳定；
- Scope/OOS 已完成一轮 remediation；
- Routing over-trigger 已完成一轮 remediation；
- Embedding Identity / Model Alignment 已正式收编；
- baseline governance 与 live hash drift detection 已建立；
- workspace relocation 与 publication tooling portability 已收口。

本次 release **不表示**：

- V4 已达到最终 Product Quality DoD；
- Document Identity 已完成；
- History 已完成；
- Retrieval 已完成；
- Generation completeness 已完成；
- Measurement closure 已完成；
- Citation coverage 已完成。

---

# 13. Next Product Phase — V4.7

```text
V4.7 — Document Identity Remediation
```

当前主要目标：

```text
md-004
md-009
md-015
```

当前现象：

```text
真实文档已检索到
但回答使用：
材料1 / 材料2 / 材料3

而不是：
canonical document title
```

V4.7 必须首先判断真实 title 落在哪一层：

```text
A. 未进入 final model-visible context
B. 已进入 final model-visible context，但 model 不输出
```

- 若为 A → Document Identity（证据 framing 未给出真实标题）为正确 root cause；
- 若为 B → 必须重新归因为 `Generation`，**不得为了维持 roadmap 强行修改错误层**。

---

# 14. Candidate Post-V4.7 Sequence

以下为 **CURRENT CANDIDATE SEQUENCE**（当前证据支持的候选顺序），**不是不可修改的硬承诺**。

## Candidate V4.8 — History Resolution

重点：

```text
mt-011
```

已知 malformed rewrite：

```text
CDMA的那
```

V4.7 后必须重新 attribution 后再授权。

## Candidate V4.9 — Retrieval Remediation

当前候选包括：

```text
cit-013
qa-020
qa-030
cmp-001
loc-008
loc-013
loc-015
```

重点为 RRF ranking miss。

Document Identity 修复后必须重新确认这些 case 是否仍是真 Retrieval failure。

## Candidate V4.10 — Generation Completeness

当前 residual family 包括：

```text
qa-040
md-019
cit-001
mt-006
...
```

典型模式：

```text
evidence delivered
but answer omitted / refused / pointer-only
```

必须在上游 Identity / History / Retrieval 修完后重新导出 failure set。

## Candidate V4.11 — Measurement / Golden / Evaluator Closure

当前 measurement residual 包括：

- locate 模板不复述 query concept；
- 序数表达差异；
- 同义词 / paraphrase；
- Golden route 与 deterministic answer contract 冲突。

必须单独处理。

禁止：

```text
降低标准
为单个 case 特判
为提高 metric 修改事实
```

## Candidate V4.12 — Citation Alignment / Coverage

Citation 保持后置。

仅在 Answer Quality 稳定后再处理：

```text
multi-evidence citation coverage
citation alignment
```

同时保持：

```text
invalid = 0
scope violation = 0
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
V4.8 / V4.9 / V4.10 / V4.11 / V4.12
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

因此 Development Snapshot 发布完成后：

```text
CURRENT PRODUCT BASELINE
=
V4_6_1_EMBEDDING_IDENTITY_BASELINE
```

开发主线继续：

```text
V4.7 — Document Identity Remediation
```

无需因为一次 GitHub publication 重新编号研发 phase。

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

Documentation Alignment              REQUIRED BEFORE RELEASE
Publication Safety / Leak Triage     REQUIRED BEFORE RELEASE
Publish Workspace Sync Verification  REQUIRED BEFORE RELEASE

Document Identity                    NEXT PRODUCT PHASE
History                              PENDING
Retrieval                            PENDING
Generation                           PENDING
Measurement Closure                  PENDING
Citation Coverage                    DEFERRED / PENDING
Unified Final Closure                PENDING
```

当前：

```text
V4 DEVELOPMENT = ACTIVE
V4 FINAL       = NOT YET
RELEASE TYPE   = DEVELOPMENT SNAPSHOT / PRE-RELEASE
NEXT PRODUCT PHASE = V4.7 DOCUMENT IDENTITY
```

---

# 19. Phase / Artifact / Test References

| 主题 | 阶段文档 | 机器 artifact | 测试 |
|---|---|---|---|
| Evaluation Integrity | `docs/V4_EVALUATION_INTEGRITY.md` | `eval/v4_initial_baseline.json` | `tests/test_v4_evaluation_integrity.py` |
| Failure Attribution | `docs/V4_FAILURE_ATTRIBUTION.md` | `eval/v4_failure_attribution.json` / `eval/v4_attribution_closure.json` | `tests/test_v4_attribution_integrity.py` / `tests/test_v4_attribution_closure.py` |
| Scope/OOS (V4.4) | `docs/V4_SCOPE_OOS_REMEDIATION.md` | `eval/v4_4_scope_remediation_baseline.json` / `eval/v4_scope_remediation.json` | `tests/test_v4_scope_oos_remediation.py` |
| Routing (V4.5) | `docs/V4_ROUTING_REMEDIATION.md` | `eval/v4_5_routing_baseline.json` / `eval/v4_routing_remediation.json` | `tests/test_v4_routing_remediation.py` |
| Post-Routing Attribution (V4.6) | `docs/V4_POST_ROUTING_ATTRIBUTION.md` | `eval/v4_6_post_routing_attribution.json` / `eval/v4_6_post_routing_evidence.json` | `tests/test_v4_6_post_routing_attribution.py` |
| Embedding Identity (V4.6.1) | `docs/V4_EMBEDDING_IDENTITY_ALIGNMENT.md` | `eval/v4_6_1_embedding_identity_baseline.json` / `eval/v4_6_1_embedding_identity_formalization.json` | `tests/test_embedding_identity.py` / `tests/test_live_production_hash_guard.py` |
| Baseline Lineage | `docs/V4_INITIAL_BASELINE.md` | `eval/v4_baseline_lineage.json` | `tests/test_v4_baseline_lineage.py` |
| Product Quality Contract | `docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md` | `eval/v3_quality_acceptance.json` | `tests/test_quality_acceptance.py` |
| Relocation / publication tooling | `KB-V4_Workspace_Relocation_Audit.md`（父目录） | — | `tests/test_publication_scan.py` |

---

> 本 Master 于 `KB-V4 — Master Requirements & Roadmap Documentation Alignment`（DOCUMENTATION-ONLY）授权下
> 机械核验后建立：live production hash 现场重算 = `7216c885…`，current baseline =
> `V4_6_1_EMBEDDING_IDENTITY_BASELINE`，metrics 直接读取 `eval/v4_6_1_embedding_identity_baseline.json`。
> 本轮未修改任何 production / evaluator / Golden / Contract / baseline artifact。
