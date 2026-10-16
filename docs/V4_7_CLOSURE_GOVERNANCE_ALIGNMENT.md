# KB-V4 — V4.7 Closure Governance Alignment & V4.8 Authorization Preparation

```text
MODE = GOVERNANCE / DOCUMENTATION ALIGNMENT ONLY

PRODUCT_CODE_CHANGE_AUTHORIZED  = NO
MEASUREMENT_CHANGE_AUTHORIZED   = NO
V4_8_EXECUTION_AUTHORIZED       = NO
PUBLICATION_AUTHORIZED          = NO

V4_7_CLOSURE_GOVERNANCE_ALIGNMENT = PASS
GOVERNANCE_ALIGNMENT_REQUIRED     = PARTIAL
```

---

## A. Scope

唯一 ACTIVE DEVELOPMENT workspace：

```text
E:\Project_ws\Local Database Q&A System\Local Database Q&A System本地版v4
```

本轮只做：审计 current governance 文档是否停留在 V4.7 前状态；对**确实是 stale 的 current-governance 文档/章节**做最小对齐。

未执行：产品修复 / V4.8 / measurement 变更 / baseline 变更 / publication。
V3 workspace：`FROZEN / READ-ONLY / UNTOUCHED`。
Publish workspace：`READ-ONLY`（仅用 `git ls-remote` 只读验证远端 HEAD；未 fetch / 未 pull / 未改动任何 ref 或 worktree）。

## B. Inputs / Sources of Truth

按事实域分别判定（不使用单一全局 precedence）。

**S1. Release / Baseline / Metrics lineage**

```text
eval/v4_baseline_lineage.json                 -> current_baseline_id = V4_6_2_HASH_PORTABILITY_BASELINE
eval/v4_6_2_hash_portability_baseline.json    -> canonical production hash 108fb167…798c
                                                 parent_raw_production_source_hash = 7216c885…a22a
                                                 production_behavior_changed_in_stage = false
                                                 measurement_hash_contract_changed_in_stage = true
eval/v4_6_1_embedding_identity_baseline.json  -> product metrics source；metrics_recomputed_in_v4_6_2 = false
                                                 case_exact 0.7292 / recall 0.8535 / false_refusal 0.0000
                                                 coverage 0.4657 / high_conf 0.0132 / invalid 0 / scope 0
```

**S2. V4.7 current diagnosis**

```text
eval/v4_7_document_identity_root_cause.json
docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md
```

**S3. Historical V4.6 attribution（只表示当年结论）**

```text
eval/v4_6_post_routing_attribution.json
docs/V4_POST_ROUTING_ATTRIBUTION.md
```

**S4. Current governance prose（可总结 machine artifact，不得覆盖）**

```text
docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md
docs/INDEX.md
README.md
CHANGELOG.md ([Unreleased] 段)
```

**Remote verification（只读）**

```text
REMOTE_MAIN_HEAD               = 1efc74f1c5aa4021766ed443f68ef8c5046116e4
                               （refs/heads/main，git ls-remote 只读获得）
REMOTE_HEAD_MATCHES_EXPECTED   = YES
=> 未触发 "STOP BEFORE EDITING"
```

**Existing alignment artifact check**

```text
EXISTING_ALIGNMENT_ARTIFACT = ABSENT（本轮开始前不存在 docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md 或等价物）
```

## C. Field Mapping

required semantic state → actual frozen V4.7 closure artifact field（§8）。mapping_type ∈ {EXACT, MECHANICALLY_EQUIVALENT, NOT_AVAILABLE}。

| expected_state | actual_field_or_structure | mapped_value | mapping_type | evidence |
|---|---|---|---|---|
| V4_7_DIAGNOSIS_CLOSURE | `v4_7_diagnosis_closure` | `PASS` | EXACT | eval/v4_7…json |
| V4_7_ENVIRONMENT_EQUIVALENCE | `environment_equivalence` | `PASS` | EXACT | 同上 |
| CURRENT_PIPELINE_ROOT_CAUSE | `current_pipeline_root_cause` | `GENERATION` | EXACT | 同上 |
| CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS | `current_pipeline_document_identity_loss` | `DISPROVEN` | EXACT | 同上 |
| DOCUMENT_IDENTITY_ROOT_CAUSE | `document_identity_root_cause` | `NOT_PROVEN` | EXACT | 同上 |
| DOCUMENT_IDENTITY_MECHANISM_APPLICABLE | `document_identity_mechanism_applicable` | `NO` | EXACT | 同上 |
| FIRST_IDENTITY_LOSS_LAYER | `first_identity_loss_layer` | `NONE (…)` | EXACT（含说明后缀） | 同上 |
| PRODUCT_ROOT_CAUSE_FAMILY_SHARED | `product_root_cause_family_shared` | `YES` | EXACT | 同上 |
| SHARED_PRODUCT_ROOT_CAUSE_FAMILY | `shared_product_root_cause_family` | `GENERATION` | EXACT | 同上 |
| MIXED_PRODUCT_ROOT_CAUSE_FAMILIES | `mixed_product_root_cause_families` | `NO` | EXACT | 同上 |
| SHARED_GENERATION_MECHANISM | `shared_generation_mechanism` | `YES` | EXACT | 同上 |
| SHARED_GENERATION_MECHANISM_NAME | `shared_generation_mechanism_name` | `MATERIAL_INDEX_REPRESENTATION_BIAS…` | MECHANICALLY_EQUIVALENT（含长说明，前缀为规范名） | 同上 |
| GENERATION_MECHANISM_ISOLATION | `generation_mechanism_isolation` | `NOT_ESTABLISHED (…)` | EXACT（含说明后缀） | 同上 |
| GENERATION_REMEDIATION_SCOPE_READY | `generation_remediation_scope_ready` | **`YES`** | EXACT | 同上 |
| MEASUREMENT_SEMANTIC_ISSUE | `measurement_semantic_issue` | `SUPPORTED` | EXACT | 同上 |
| per-case measurement | `per_case_measurement_issue` | md-004 `SUPPORTED` / md-009 `SUPPORTED` / md-015 `NOT_OBSERVED` | EXACT | 同上 |
| HISTORICAL_SOURCE_ANCHOR_AVAILABLE | `historical_source_anchor.historical_source_anchor_available` | `NO` | EXACT（嵌套） | 同上 |
| RELEVANT_PIPELINE_EQUIVALENCE | `relevant_pipeline_equivalence` | `NOT_ESTABLISHED` | EXACT | 同上 |
| HISTORICAL_FAILURE_COMPATIBILITY | `historical_failure_compatibility` | `STRONGLY_SUPPORTED` | EXACT | 同上 |
| HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION | `historical_v4_6_document_identity_attribution` | `STRONGLY_CHALLENGED` | EXACT | 同上 |
| GENERATION_WORKSTREAM_CANDIDATE | `generation_workstream_candidate` | `SUPPORTED` | EXACT | 同上 |
| DOCUMENT_IDENTITY_REMEDIATION | `ready_for_document_identity_remediation` | `NO`（= BLOCKED） | MECHANICALLY_EQUIVALENT | 同上 |
| APPLICATION_REQUEST_TITLE_VISIBILITY | `application_request_title_visibility` | `YES_FOR_ALL_TARGETS` | EXACT | 同上 |
| EVIDENCE_CONTINUITY | `evidence_continuity` | `PRESERVED_FOR_ALL_TARGETS` | EXACT | 同上 |
| POST_PROCESSING_CAUSE | `post_processing_cause` | `EXCLUDED` | EXACT | 同上 |

**FIELD_MAPPING_STATUS = EXACT**（1 项为 MECHANICALLY_EQUIVALENT 的命名归一化）。

### C.1 记录一处 expected-shape 差异（非 artifact 冲突）

```text
expected_state                    = GENERATION_REMEDIATION_SCOPE_READY
prompt_expected_value             = NOT_ESTABLISHED
machine_mapped_value              = YES
mapping_type                      = EXACT
```

说明与处理：

```text
1. 该字段在冻结 V4.7 closure artifact 中存在且为 EXACT 命名 ⇒ mapping_type = EXACT（不构成 §8 的 NOT_AVAILABLE / INSUFFICIENT_EVIDENCE）。
2. 依 §9 不得修改 V4.7 closure artifact；依 §36「必须以实际 machine evidence 为准」，以 machine 值 YES 为准。
3. 该值语义为 “mechanism-class scope 已知（因 SHARED_GENERATION_MECHANISM = YES）”，
   与同时存在的 generation_mechanism_isolation = NOT_ESTABLISHED 并不矛盾。
4. 治理层结论（§12 / §19）保持不变：机制隔离未建立 ⇒ **统一 generation remediation 不可实施**，
   本轮 current docs **不**表达 “generation remediation ready”。
5. 该差异被记录而非静默；本轮**不**修改任何 machine artifact 以消除差异。
```

## D. Pre-change Integrity Snapshot

```text
CANONICAL_PRODUCTION_HASH_BEFORE = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
core = ce33e5504bebc1a3941ce381c77baad1716acd845f5e80b97c3f515016a78db0
desktop = 22173f277d0b3ac1fbc6935c24e2f217e2f5df196e43ba4dd8ca5e392b1120a2
web = 7283dfb676ce5355f6911cf3fdf7790722a97a95479986cf815311161057bbaf

RUNTIME_DB_PATH       = data/library/documents.sqlite3
RUNTIME_DB_HASH_BEFORE = c6bc9b3eb63ae4e6d96caf859a2b0c5f2f1e5a5b6f438e81aa0bbc3cf4084c97
RUNTIME_DB_SIZE       = 10698752
RUNTIME_DB_IDENTITY   = 10698752:c6bc9b3eb63ae4e6   （== baseline == metrics source）
```

PRE_CHANGE_FROZEN_HASH_MANIFEST（byte-exact SHA-256）：

```text
414e5a711d6bfbf0825469e09e6c9c31d52ca66dc2e0df7cabe719e6dc99ed95  eval/v4_6_2_hash_portability_baseline.json
2c7b9d0beca0af94bc80496874e95ac4a9ad7d613843bf70da7c3e8ec5a94ddb  eval/v4_6_1_embedding_identity_baseline.json
18ca7ccb445d46c2b38fd711d07e4f59e0d515d2992b9bce948b854df27ac54c  eval/v4_baseline_lineage.json
effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d  eval/v4_7_document_identity_root_cause.json
7073a64a7b1a537a1d16b31d858a62ad8d11620a9348d756cce4ade961870849  docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md
5a644a3fe9a9b280ff095493627844cea745f44d06d2c2f249feb6c4e444a5f8  eval/v4_6_post_routing_attribution.json
fbac1e51ca621d93c04a66db396fde1cbeffa7237e3034fb3b1b2c4a777f703a  docs/V4_POST_ROUTING_ATTRIBUTION.md
31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb  eval/v3_final_golden.json
```

candidate governance docs（写入前）：

```text
01703cc36cea612060bd970957212dadbb963626c7420fbfaa16717184bb9926  docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md
0caf048c598aa80724d2ea1e5af96725811ab02e2c69a732607a95d7a7f6e1a8  docs/INDEX.md
8c2d70f53ad633712378decdbc42e4454c783b70b08070138ff78e1be86af775  README.md
f2ac450afacfd576dbc5e841f7bc8b587324dcd93d483dfe3176cc3d9a2ec77c  docs/V4_RELEASE_SNAPSHOT.md
80e62ae17c2e6b2893ee8a93d5cb8da92971596928371a1a610592a132dc457f  CHANGELOG.md
```

## E. Workspace Manifest Scope / Exclusions

见 §N 的机械 pre/post manifest diff。

```text
WORKSPACE_MANIFEST_SCOPE =
    整个 ACTIVE V4 workspace 的全部常规文件（含 core/ desktop/ web/ eval/ docs/ scripts/ tests/
    reranker_service/ data/ 以及项目根目录文件），逐文件 byte-exact SHA-256。

MANIFEST_EXCLUSIONS（写入前即声明，未在事后追加）=
    __pycache__/            （Python 字节码缓存目录）
    *.pyc / *.pyo           （字节码文件）
    .venv/ · venv/          （虚拟环境）
    .ruff_cache/ · .pytest_cache/ · .mypy_cache/   （工具缓存）
    .git/                   （版本库内部数据）
    data/eval_cache/        （runtime answer cache；baseline artifact 已声明为 gitignored runtime 数据）
    data/logs/              （append-only telemetry）
```

`data/library/documents.sqlite3`（runtime DB）**未**被排除，并已单独记录完整 SHA-256（§D），用于证明 `RUNTIME_DB_UNCHANGED`。

pre-change manifest：`295` files。

## F. V4.7 Closure Accepted State

```text
V4_7_CLOSURE_INPUT_VALID = YES
```

依据：machine artifact 内部一致（`gate_results` 全 PASS、`closure_gate_results` C1–C37 全 PASS、
`raw_evidence_preservation = VERIFIED_BY_SEMANTIC_DIGEST`），且 machine artifact 与 human report
`docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md` 在全部核心事实上一致（§C 逐字段核对）。

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
SHARED_GENERATION_MECHANISM                    = YES（MATERIAL_INDEX_REPRESENTATION_BIAS）
GENERATION_MECHANISM_ISOLATION                 = NOT_ESTABLISHED
MEASUREMENT_SEMANTIC_ISSUE                     = SUPPORTED
HISTORICAL_SOURCE_ANCHOR_AVAILABLE             = NO
RELEVANT_PIPELINE_EQUIVALENCE                  = NOT_ESTABLISHED
HISTORICAL_FAILURE_COMPATIBILITY               = STRONGLY_SUPPORTED
HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION  = STRONGLY_CHALLENGED
```

未发现 machine artifact 与 human report 的实质冲突 ⇒ 未触发 §7 的 STOP。

## G. Document Semantic Classification

| file | semantic_role | stale_current_state_present | historical_sections_present | modification_required | reason |
|---|---|---|---|---|---|
| `docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md` | CURRENT_GOVERNANCE（MIXED_SECTION_LEVEL） | YES（header / §13 / §14 / §17 / §18） | YES（§10 phase history、§11 relocation） | **YES（section-level only）** | 仍是 V4.7 前状态；V4.8 名称与 §18 冲突；§17 基线陈旧 |
| `docs/INDEX.md` | CURRENT_GOVERNANCE（cold start 导航） | YES（§3 把 V4.6 attribution 当作 current 依据；缺 V4.7） | 部分（§4/§5 表） | **YES（minimal）** | 新 Agent 无法看出 latest completed diagnosis 与 candidate V4.8 |
| `README.md` | CURRENT_USER_FACING / ROLLING_STATUS | YES（“下一产品阶段 = V4.7”；已知限制 “Document Identity — NEXT”） | NO | **YES（minimal）** | current-status wording 陈旧 |
| `docs/V4_RELEASE_SNAPSHOT.md` | HISTORICAL_RELEASE_SNAPSHOT | NO（其 “Next product phase = V4.7” 是 **alpha.2 时点的历史事实**） | YES（整篇） | **NO** | §23：point-in-time release snapshot；contract 非 rolling-current |
| `CHANGELOG.md` | MIXED_SECTION_LEVEL | YES（仅 `[Unreleased]` 段仍为“暂无尚未发布的变更”） | YES（alpha.1 / alpha.2 / v3-final） | **YES（仅 Unreleased）** | 历史 entries 不改写；当前段与事实不符 |

其它 current prose 复核（classification = F / 无需修改）：

```text
docs/ARCHITECTURE.md          —— 只描述当前真实架构，无 roadmap/phase 声明 ⇒ NO change
本地使用说明.md                 —— 使用说明，无 phase 声明 ⇒ NO change
docs/V4_*.md（V4.0–V4.6.1 阶段证据）—— HISTORICAL ⇒ NO change
docs/V3_*.md                  —— HISTORICAL（V3 冻结） ⇒ NO change
```

## H. Conflict Classification Matrix

分类：A TRUE_CONFLICT / B EXPECTED_REMOTE_PUBLICATION_LAG / C HISTORICAL_SNAPSHOT / D STALE_CURRENT_DOCUMENTATION / E LOCAL_ONLY_NEW_EVIDENCE / F NO_CONFLICT / G INSUFFICIENT_EVIDENCE。

| file | location | current wording | authoritative evidence | class | action | reason |
|---|---|---|---|---|---|---|
| MASTER | header | 「当前下一产品阶段：V4.7」 | V4.7 closure artifact（COMPLETE） | D | EDIT | V4.7 已完成 |
| MASTER | §13 | 「Next Product Phase — V4.7」+ A/B 未判定 | `application_request_title_visibility = YES_FOR_ALL_TARGETS` ⇒ B | D | EDIT | 结论已确定 |
| MASTER | §14 | 「Candidate V4.8 — History Resolution」 | §18/§21 要求 V4.8 = Generation Mechanism Isolation | A | EDIT | 命名真冲突 |
| MASTER | §17 | 「CURRENT PRODUCT BASELINE = V4_6_1…」 | lineage：current = V4_6_2 | A | EDIT | 与 lineage 直接冲突 |
| MASTER | §18 | 「Document Identity NEXT PRODUCT PHASE」「NEXT PRODUCT PHASE = V4.7」 | V4.7 closure | D | EDIT | 陈旧 |
| MASTER | §10 V4.6 entry（Priority 1 Document Identity 等） | V4.6 阶段当时的优先级 | V4.6 历史结论 | C | NO CHANGE | phase history，不改写 |
| INDEX | §3 | 「V4_POST_ROUTING_ATTRIBUTION …（当前优先级排序的来源）」 | V4.7：STRONGLY_CHALLENGED | D | EDIT | 不再是 current 依据 |
| INDEX | §3/§5 | 无 V4.7 条目 | V4.7 closure artifact 存在 | E | EDIT（add） | 本地新证据需可导航 |
| README | 状态表 | 「下一产品阶段：V4.7」 | V4.7 COMPLETE | D | EDIT | 陈旧 |
| README | 已知限制 | 「Document Identity — NEXT（V4.7）」 | V4.7：DISPROVEN | D | EDIT | 陈旧 |
| CHANGELOG | `[Unreleased]` | 「（暂无尚未发布的变更。）」 | V4.7 closure 为未发布变更 | D | EDIT | 陈述已不成立 |
| CHANGELOG | `[v4.0.0-alpha.2]` Known Limitations | 「Document Identity — 下一产品阶段（V4.7）」 | alpha.2 时点事实 | C | NO CHANGE | 历史 release entry |
| V4_RELEASE_SNAPSHOT | §7 | 「Document Identity NEXT / Next product phase: V4.7」 | alpha.2 时点事实 | C | NO CHANGE | §23 fail-conservative |
| V4_POST_ROUTING_ATTRIBUTION(.md/.json) | 全文 | `DOCUMENT_IDENTITY_FAILURE` primary | V4.6 时点结论 | C | NO CHANGE | 历史 artifact 不可变 |
| V4_ROUTING_REMEDIATION.md | 290-296 | 「RECOMMENDED_NEXT_PHASE = V4.6 …」 | V4.5 时点结论 | C | NO CHANGE | 历史阶段证据 |
| ARCHITECTURE.md / 本地使用说明.md | — | 无 phase 声明 | — | F | NO CHANGE | 无冲突 |

`B`（remote publication lag）与 `G`（INSUFFICIENT_EVIDENCE）均未出现；无 `G` ⇒ 未触发 fail-conservative STOP。

## I. Governance Alignment Decision

```text
GOVERNANCE_ALIGNMENT_REQUIRED = PARTIAL
```

理由：current-governance 真值中确实存在 stale wording（`D`）与一处命名真冲突（`A`），但并非全部 current docs 都 stale
（`docs/V4_RELEASE_SNAPSHOT.md` 属于 point-in-time release snapshot、`docs/ARCHITECTURE.md` 无 phase 声明）。

```text
AUTHORIZED_STALE_CURRENT_GOVERNANCE_PATHS =
    docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md
    docs/INDEX.md
    README.md
    CHANGELOG.md            （仅 [Unreleased] 段）
+ optional governance alignment report
    docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md
```

## J. Current-state Corrections Applied

**MASTER**

```text
1. header  —「当前下一产品阶段 = V4.7」→「V4.7 COMPLETE / CLOSED；下一候选诊断阶段 = V4.8 …（NOT AUTHORIZED）」；
            并显式标注 Document Identity Remediation = BLOCKED。
2. §10     — 新增 “V4.7 — Document Identity Root-Cause Confirmation + Diagnosis Closure” 条目
            （COMPLETE / CLOSED · READ-ONLY DIAGNOSIS；不建立 product baseline）。历史条目未改写。
3. §13     —「Next Product Phase — V4.7」改写为 “Completed Diagnosis — V4.7 (Outcome)”，记录 B 判定与四轴结论。
4. §14     — 标题改为 “Candidate Next-phase Sequence”；新增 Candidate V4.8 =
            Generation / Prompt-Evidence Framing Mechanism Isolation（含 M1–M5 candidate families）；
            原 V4.8–V4.12 顺延为 V4.9–V4.13；Retrieval 段说明 Document Identity 已被 V4.7 排除；
            Measurement 段纳入 V4.7 提出的独立 semantic issue。
5. §15     — candidate naming 列表改为 V4.9 / V4.10 / V4.11 / V4.12 / V4.13。
6. §17     —「CURRENT PRODUCT BASELINE = V4_6_1…」修正为 V4_6_2_HASH_PORTABILITY_BASELINE，
            并标注 publication 不推进 baseline；开发主线更新为 V4.7 CLOSED + V4.8 candidate。
7. §18     — 状态清单：Document Identity → RESOLVED AS ROOT CAUSE（Loss = DISPROVEN）、
            Remediation → BLOCKED、Generation → ROOT CAUSE FAMILY、Generation Mechanism Isolation →
            CANDIDATE NEXT（V4.8）；current 块：V4.7 = COMPLETE / CLOSED、NEXT PRODUCT PHASE = V4.8（NOT AUTHORIZED）。
8. §19     — 引用表新增 V4.7 行（doc / machine artifact / test）。
9. closing — 核验说明改为 V4.7 Closure Governance Alignment，并声明本轮未改 production/evaluator/Golden/baseline。
```

**INDEX**

```text
10. 新增 “Current cold-start pointers” 块（current baseline / metrics source / release / latest completed diagnosis /
    V4.6 = historical / candidate V4.8 / V4.8 execution = NOT AUTHORIZED）。
11. §3 重命名为 “Current Diagnostic Reference”，纳入 V4.7 closure 与本 alignment 报告；移除 V4.6 attribution 的 current 地位。
12. §4 新增 V4_POST_ROUTING_ATTRIBUTION.md 为历史阶段证据（标注解释已被 V4.7 强挑战）。
13. §5 新增 eval/v4_7_document_identity_root_cause.json；V4.6 attribution artifact 标注为历史快照。
```

**README**

```text
14. 状态表：删除「下一产品阶段 = V4.7」；新增「最近完成阶段 = V4.7（COMPLETE / CLOSED）」与
    「下一候选阶段 = V4.8（candidate，尚未授权）」。
15. 新增 published-vs-local 说明块（GitHub main 仍为 alpha.2；local development 已推进至 V4.7 closure，尚未发布）。
16. 已知限制：Document Identity 改为“已结案 / Loss = DISPROVEN / remediation BLOCKED”；
    新增 Generation / Prompt-Evidence Framing 行与独立 Measurement 语义行。
```

**CHANGELOG**

```text
17. 仅在 [Unreleased] 段新增最小 V4.7 closure / governance 记录
    （diagnosis & governance only；production behavior unchanged；no new product baseline；
     Document Identity remediation blocked；generation mechanism isolation pending）。
    历史 entries（alpha.1 / alpha.2 / v3-final）逐字未改。
```

未在 current docs 中把 observed candidate mechanism 升级为 proven dominant causal mechanism；
未声称 generation remediation ready；未声称 V4.8 已开始 / 活跃 / 完成。

## K. Historical Artifacts Intentionally Preserved

```text
eval/v4_6_post_routing_attribution.json       UNCHANGED（继续表示 V4.6 阶段当时的结论）
docs/V4_POST_ROUTING_ATTRIBUTION.md           UNCHANGED
docs/V4_RELEASE_SNAPSHOT.md                   UNCHANGED（point-in-time alpha.2 release snapshot）
CHANGELOG [v4.0.0-alpha.1] / [v4.0.0-alpha.2] / [v3-final]  entries  UNCHANGED
docs/V4_ROUTING_REMEDIATION.md 等 V4.x 阶段证据 UNCHANGED
eval/v4_7_document_identity_root_cause.json    UNCHANGED（V4.7 closure 冻结输入）
docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md     UNCHANGED
```

## L. Product / Measurement Separation

```text
Product 轴：
  CURRENT_PIPELINE_ROOT_CAUSE            = GENERATION
  SHARED_PRODUCT_ROOT_CAUSE_FAMILY       = GENERATION
  SHARED_GENERATION_MECHANISM            = YES（MATERIAL_INDEX_REPRESENTATION_BIAS）
  GENERATION_MECHANISM_ISOLATION         = NOT_ESTABLISHED
  DOCUMENT_IDENTITY_REMEDIATION          = BLOCKED
  => 不得宣称 dominant mechanism proven / minimal remediation ready

Measurement 轴（独立，不重新定义 Product root cause）：
  MEASUREMENT_SEMANTIC_ISSUE             = SUPPORTED
  per case                               = md-004 SUPPORTED / md-009 SUPPORTED / md-015 NOT_OBSERVED
  MEASUREMENT_TRACK                      = DEFERRED_SEPARATE_TRACK
  => 本轮未修改 Golden / expected facts / matcher / evaluator / metric 语义
```

## M. V4.8 Candidate Boundary

```text
NEXT_PRODUCT_DIAGNOSIS_CANDIDATE        = V4.8_GENERATION_MECHANISM_ISOLATION
阶段名（推荐）                           = V4.8 — Generation / Prompt-Evidence Framing Mechanism Isolation
性质                                    = READ-ONLY / COUNTERFACTUAL / PRODUCT DIAGNOSIS
目标                                    = 通过受控 counterfactual / ablation 隔离 Generation family 内
                                          真正具有因果作用的机制（而非直接实施 product remediation）
candidate mechanism families            = M1 MATERIAL_INDEX_REPRESENTATION_BIAS
                                          M2 PROMPT_FRAMING
                                          M3 CHUNK_TO_DOCUMENT_AGGREGATION
                                          M4 PURE_GENERATION_SYNTHESIS
                                          M5 INTERACTION_EFFECT
                                          （仅为 candidate，不是已证明结论）

V4_8_READY_FOR_SEPARATE_AUTHORIZATION   = YES
V4_8_EXECUTION_AUTHORIZED               = NO
```

本轮**未**创建 V4.8 script / test / experiment / ablation / baseline；未调用任何模型做机制实验。

## N. Files Changed

pre/post workspace manifest 由 `v4_7_ga_manifest.py` 机械生成后 diff（非手工填写）：

```text
WORKSPACE_MANIFEST_SCOPE（pre == post）
MANIFEST_EXCLUSIONS（pre-declared, unchanged）
PRE_CHANGE_WORKSPACE_MANIFEST  file count = 295
```

| path | change | before | after |
|---|---|---|---|
| `docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md` | CONTENT_CHANGED | 01703cc36cea612060bd970957212dadbb963626c7420fbfaa16717184bb9926 | 94e335dbf36c9ed09f84d0f6815a9bfdf14ad29afe288b9be087c80d3557504d |
| `docs/INDEX.md` | CONTENT_CHANGED | 0caf048c598aa80724d2ea1e5af96725811ab02e2c69a732607a95d7a7f6e1a8 | ff34988dcf4dcde82fd444d7340d88347ccba6b20ae177b77b886b472e0c760b |
| `README.md` | CONTENT_CHANGED | 8c2d70f53ad633712378decdbc42e4454c783b70b08070138ff78e1be86af775 | b1b2fb80eea687a93f15e7881d206ea241465e98336e60e41b5123c875e5a701 |
| `CHANGELOG.md` | CONTENT_CHANGED | 80e62ae17c2e6b2893ee8a93d5cb8da92971596928371a1a610592a132dc457f | afc4477f66699ea451fe66d9bfbb7b52d6ac90df6652d5a1249f7cea75906310 |
| `docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md` | ADDED | — | 本文件（其 hash 在写入后由 §N.2 post manifest 给出，不自我引用） |

### N.1 Mechanical manifest diff（原样输出，非手工填写）

```text
files=296                      （post-change manifest）
CONTENT_CHANGED = ['CHANGELOG.md', 'README.md', 'docs/INDEX.md', 'docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md']
ADDED           = ['docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md']
DELETED         = []
counts pre/post = 295 / 296
```

```text
ACTUAL_CHANGED_PATHS =
    docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md   (CONTENT_CHANGED)
    docs/INDEX.md                                (CONTENT_CHANGED)
    README.md                                    (CONTENT_CHANGED)
    CHANGELOG.md                                 (CONTENT_CHANGED)
    docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md    (ADDED)
```

```text
ACTUAL_CHANGED_PATHS ⊆ AUTHORIZED_STALE_CURRENT_GOVERNANCE_PATHS + optional governance alignment report
CHANGE_BOUNDARY = PASS
```

## O. Files Intentionally Not Changed

```text
core/ · desktop/ · web/                       （production code）
eval/*                                        （全部 baseline / lineage / metrics / attribution / V4.7 closure artifacts）
eval/v3_final_golden.json                     （Golden）
scripts/ · tests/                              （本轮未新增/修改任何 script 或 test）
data/library/documents.sqlite3                （runtime DB）
docs/V4_RELEASE_SNAPSHOT.md                   （point-in-time release snapshot）
docs/V4_POST_ROUTING_ATTRIBUTION.md           （历史 V4.6）
docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md     （V4.7 closure 冻结输入）
docs/ARCHITECTURE.md · 本地使用说明.md          （无 phase 声明，未 stale）
docs/V4_*.md（V4.0–V4.6.1 阶段证据）· docs/V3_*.md
reranker_service/ · requirements*.txt · ruff.toml · build_windows.ps1 · windows_desktop.spec ·
rebuild_all.py · 启动本地版.bat
V3 workspace（FROZEN）· Publish workspace（READ-ONLY）
```

## P. Baseline / Metrics Preservation

```text
eval/v4_baseline_lineage.json               UNCHANGED（current pointer 仍为 V4_6_2_HASH_PORTABILITY_BASELINE）
eval/v4_6_2_hash_portability_baseline.json  UNCHANGED
eval/v4_6_1_embedding_identity_baseline.json UNCHANGED
eval/v3_final_golden.json                   UNCHANGED
metrics_recomputed                          NO
Full-144 rerun                              NO
answer artifact regeneration                NO
new product baseline / CURRENT_PRODUCT_STATE NO
baseline pointer movement                   NO
```

## Q. Production Hash Verification

```text
CANONICAL_PRODUCTION_HASH_BEFORE = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
CANONICAL_PRODUCTION_HASH_AFTER  = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
PRODUCTION_HASH_CHANGED          = NO
RUNTIME_DB_UNCHANGED             = YES
```

## R. Validation / Tests

```text
TESTS_RUN =
    python -m unittest tests.test_live_production_hash_guard -v      （6 tests，PASS）
    python -m unittest tests.test_v4_6_2_hash_portability -v         （15 tests，PASS）

TESTS_NOT_RUN_BY_DESIGN =
    Full-144 canonical evaluation（禁止）
    V4.8 counterfactual / model ablation（未授权）
    answer model / embedding model 调用（本轮不需要）
    与 modified files 无关的其它测试套件（避免扩大范围）

STRUCTURED FILE PARSE VALIDATION =
    modified files 均为 Markdown（无 JSON/YAML/TOML）⇒ 无结构化 parse 阶段；
    额外对修改后的 docs 做了 anchored-string 复核（旧 stale 短语已消除、新状态短语存在）。
```

## S. Final Current Governance State

```text
CURRENT_RELEASE       = v4.0.0-alpha.2（Development Snapshot / GitHub Pre-release；NOT V4 Final）
CURRENT_BASELINE      = V4_6_2_HASH_PORTABILITY_BASELINE
PRODUCT_METRICS_SOURCE = V4_6_1_EMBEDDING_IDENTITY_BASELINE（metrics_recomputed_in_v4_6_2 = false）
CANONICAL_PRODUCTION_HASH = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
PRODUCT_QUALITY_DOD   = NOT_YET_PASS

V4.7                  = COMPLETE / CLOSED
CURRENT_PIPELINE_ROOT_CAUSE            = GENERATION
CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS = DISPROVEN
DOCUMENT_IDENTITY_ROOT_CAUSE           = NOT_PROVEN
DOCUMENT_IDENTITY_REMEDIATION          = BLOCKED
GENERATION_WORKSTREAM_CANDIDATE        = SUPPORTED
SHARED_GENERATION_MECHANISM            = YES
SHARED_GENERATION_MECHANISM_NAME       = MATERIAL_INDEX_REPRESENTATION_BIAS
GENERATION_MECHANISM_ISOLATION         = NOT_ESTABLISHED
MEASUREMENT_SEMANTIC_ISSUE             = SUPPORTED
MEASUREMENT_TRACK                      = DEFERRED_SEPARATE_TRACK
HISTORICAL_SOURCE_ANCHOR_AVAILABLE     = NO
RELEVANT_PIPELINE_EQUIVALENCE          = NOT_ESTABLISHED
HISTORICAL_FAILURE_COMPATIBILITY       = STRONGLY_SUPPORTED
HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED

NEXT_PRODUCT_DIAGNOSIS_CANDIDATE       = V4.8_GENERATION_MECHANISM_ISOLATION
V4_8_READY_FOR_SEPARATE_AUTHORIZATION  = YES
V4_8_EXECUTION_AUTHORIZED              = NO
```

Current governance wording（推荐，已用于 §J 的 docs）：

> V4.7 mechanically excludes Document Identity Loss for the current V4.6.2 pipeline. The observed mechanism
> strongly supports re-attributing the historical target-case failures toward Generation / Prompt-Evidence
> Framing, while exact historical pipeline equivalence remains not established.

## T. Gates

```text
G1  remote main verified read-only                     PASS (1efc74f…)
G2  V4.7 closure artifact mechanically read            PASS
G3  V4.7 closure input internally consistent           PASS
G4  required states resolved via EXACT/MECH-EQUIV      PASS (1 discrepancy recorded)
G5  current baseline remains V4_6_2                    PASS
G6  product metrics source remains V4_6_1              PASS
G7  pre-change production hash verified                PASS
G8  frozen-file pre-change manifest created            PASS
G9  workspace-wide pre-change manifest created         PASS (295 files)
G10 manifest exclusions explicitly recorded            PASS
G11 governance docs semantically classified            PASS
G12 conflicts classified before editing                PASS
G13 alignment necessity explicitly decided             PASS (PARTIAL)
G14 authorized stale paths frozen before editing       PASS (4 paths)
G15 only stale current-governance docs changed         PASS
G16 historical release snapshot semantics respected    PASS (SNAPSHOT unchanged)
G17 V4.6 historical artifacts unchanged                PASS
G18 V4.7 closure artifacts unchanged                   PASS
G19 baseline lineage unchanged                         PASS
G20 V4.6.2 baseline unchanged                          PASS
G21 V4.6.1 metrics source artifact unchanged           PASS
G22 Golden unchanged                                   PASS
G23 evaluator unchanged                                PASS
G24 citation semantics unchanged                       PASS
G25 production code unchanged                          PASS
G26 runtime DB unchanged                               PASS
G27 V3 untouched                                       PASS
G28 Publish untouched                                  PASS
G29 no new product baseline                            PASS
G30 Product / Measurement tracks remain separate       PASS
G31 Document Identity remediation remains blocked      PASS
G32 Generation mechanism isolation remains NOT_ESTABLISHED  PASS
G33 V4.8 defined only as candidate diagnosis           PASS
G34 V4.8 execution remains unauthorized                PASS
G35 no Full-144 / model ablation run                   PASS
G36 live production hash guard PASS                    PASS
G37 hash portability tests PASS                        PASS
G38 production canonical hash unchanged                PASS
G39 frozen-file hashes unchanged                       PASS
G40 workspace-wide post-change manifest created        PASS
G41 ACTUAL_CHANGED_PATHS mechanically derived          PASS
G42 changed paths within authorized surface            PASS
G43 no sync / commit / tag / push / release            PASS
```

## U. STOP Boundary

本轮结束即 STOP。未执行 V4.8；未创建 V4.8 script / test / experiment；未做 counterfactual / ablation；
未调用模型；未修改 prompt / build_messages / material header / document grouping / retrieval / ranking /
Golden / evaluator / citation semantics；未创建新 baseline；未推进 baseline pointer；
未修改 runtime DB；未修改 V3；未写入 Publish；未 sync / commit / push / tag / release。

交付物：本 governance audit report、必要的 current-doc 最小对齐、FIELD_MAPPING 证据、
pre/post frozen-file 与 workspace-wide manifest 证据、tests/hash 证据、最终 current governance state、
以及建议的 V4.8 authorization boundary。等待下一次明确授权。
