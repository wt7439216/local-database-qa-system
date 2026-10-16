# V4.8.1 — Residual Generation / Explicit Document-Membership Representation Isolation

> MODE = SINGLE-FACTOR CONTROLLED COUNTERFACTUAL / RESIDUAL-MECHANISM DIAGNOSIS ONLY
> `ARTIFACT_TYPE = DIAGNOSTIC_ONLY` · `IS_PRODUCT_BASELINE = NO`
> 本轮**不是 remediation**。

---

## A. Scope

本轮唯一科学问题：

> 在 `md-009 / md-015` 上，当 query、history、scope、retrieved chunks、chunk text、chunk order、
> canonical titles、material labels、production instruction、model 与 generation parameters 全部保持不变时，
> **仅显式增加 `chunk → source-document membership` 关系**，是否能因果性改善 document-level identity synthesis？

直接测试的 operationalized factor：

```text
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION   (= Factor G)
```

属于既有 `CHUNK_TO_DOCUMENT_AGGREGATION` residual hypothesis 的**严格、窄化 operationalization**。
本轮**不**测试：physical chunk regrouping / chunk reordering / document-level summarization /
`MATERIAL_INDEX_REPRESENTATION_BIAS` / `PROMPT_FRAMING` / title-naming instruction。

---

## B. Parent V4.8 Accepted State

```text
md-004:  M1 SUPPORTED / M2 SUPPORTED / M1_ISOLATED NO / M2_ISOLATED NO
         MULTIPLE_SUFFICIENT_INTERVENTIONS YES / M3 NOT_ESTABLISHED
         INTERACTION_PATTERN SUBADDITIVE_BINARY_CEILING_COMPATIBLE
md-009:  M1 NOT_SUPPORTED / M2 NOT_SUPPORTED / M4_PHASE_LOCAL_SUPPORTED / M4_GLOBAL NOT_ESTABLISHED
md-015:  M1 NOT_SUPPORTED / M2 NOT_SUPPORTED / M4_PHASE_LOCAL_SUPPORTED / M4_GLOBAL NOT_ESTABLISHED
aggregate: M1_SHARED PARTIAL · M2_SHARED PARTIAL · M4_SHARED_PHASE_LOCAL PARTIAL
           HETEROGENEOUS_RESPONSE_PROFILE YES · MIXED_GENERATION_MECHANISMS NOT_ESTABLISHED
           SHARED_CAUSAL_MECHANISM NOT_ESTABLISHED · GENERATION_MECHANISM_ISOLATION NOT_ESTABLISHED
           GROUPING_RESIDUAL_EVIDENCE SUPPORTED
```

已接受，**未**重新运行 V4.8 A/B experiments。

---

## C. Parent Audit Qualifiers

```text
V4_8_PROTOCOL_PROVENANCE_CONFIDENCE = PARTIAL          （永久携带，未升级）
V4_8_PRIMARY_OUTCOME_INVARIANT_TO_MATCHER_BROADENING = YES   （12/12 cells）
V4_8_SCIENTIFIC_CLASSIFICATION = ACCEPTED
```

**未**重新开启 V4.8 closure。

---

## D. Historical Claim Freeze

```text
HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO
RELEVANT_PIPELINE_EQUIVALENCE = NOT_ESTABLISHED
HISTORICAL_FAILURE_COMPATIBILITY = STRONGLY_SUPPORTED
HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED
```

未升级为 historical pipeline proven equivalent / historical mechanism mechanically proven /
historical attribution mechanically overturned。V4.8.1 的全部 causal conclusions 仅针对 **CURRENT PIPELINE**。

---

## E. Why V4.8.1

`V4.9–V4.13` 已被 current roadmap 用于顺延 sequence（History Resolution / Retrieval Remediation /
Generation Completeness / Measurement Closure / Citation Alignment）。因此本 residual phase 使用
`V4.8.1`。机械只读搜索（排除本 phase self-output）：

```text
V4.8.1  → 0 个非 self 占用
V4.9 / V4.10 / V4.11 / V4.12 / V4.13 → 仅出现于 roadmap 与 V4.7 governance 文档的 candidate naming
PHASE_NUMBERING_AUDIT = PASS
```

---

## F. Pre-change Integrity

在任何 V4.8.1 文件创建之前（由上游 prestate-freeze 步骤完成；本轮只读复算并逐项核对）：

```text
CANONICAL_PRODUCTION_HASH_BEFORE              = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
PRE_CHANGE_WORKSPACE_MANIFEST_ENTRY_COUNT     = 300
PRE_CHANGE_WORKSPACE_MANIFEST_DIGEST          = 0ec724ccccc89ee6821bedeb09f262d6c819d657a1a2fc629aa00f070754f2e0
RUNTIME_DB_IDENTITY_BEFORE                    = 10698752:c6bc9b3eb63ae4e6
V4_8_FROZEN_ARTIFACT_HASHES / V4_7_FROZEN / BASELINE / GOLDEN / V4_6_HISTORICAL = 全部匹配
```

manifest 规则（本轮冻结、可复现）：全部 regular files；排除路径段
`{__pycache__, .git, .codebuddy, node_modules, .venv, venv}`；排除顶层目录 `{data, .github}`；
排除根级名 `{.gitignore, .gitattributes}`；排除 `*.pyc/*.pyo`；pre-change 变体额外排除全部 V4.8.1 授权路径；
逐文件哈希采用 V4.6.2 冻结契约 `sha256-path-content-v2-canonical-lf`。

**关键机械事实**：该规则复算出 pre-change 计数恰为 `300`，与 preflight snapshot 记录的
`pre_change_workspace_manifest_entry_count = 300` **精确一致**；且
`CURRENT_WITH_V481 = 304 = 300 + 4`（= snapshot + machine artifact + harness + tests）。
即 **自 pre-change baseline 以来，所有非 V4.8.1 文件零变化**。

---

## G. Immutable Preflight Snapshot

```text
path                        = eval/v4_8_1_preflight_snapshot.json
PREFLIGHT_SNAPSHOT_SHA256   = e73ed965b994fb25ac39923040385333f509c9dc5804e2e023bd9623fd26b6ce
PRESTATE_LOCKED             = YES
DO_NOT_MODIFY               = YES
is_first_v4_8_1_write       = YES
PRESTATE_SNAPSHOT_OVERWRITTEN = NO
```

> **如实记录的 protocol-provenance 事项**：该 snapshot 在本轮授权执行**之前**已存在（文件创建时间早于本轮
> harness/tests/model call，且为本 phase 的**首个** V4.8.1 写入）。它已经完整冻结了 target/control、
> Factor G operationalization、G0/G1 定义、G1 模板、插入规则、group-token 规则、information firewall、
> outcome policy、title matcher identity、replication policy、call-order policy 与 aggregate semantics。
> 本轮将其视为**已锁定的 prestate**，只读复核其内容与当前 workspace 完全一致，
> 并**未**对其进行任何修改或重写。其记录的 manifest 计数已由本轮只读复算精确复现（见 §F）。

---

## H. Experiment-design Digest

从 locked preflight snapshot 抽取 `V4_8_1_EXPERIMENT_DESIGN_SEMANTIC_SUBSET`（21 个 key：
target cases / control reference / factor definitions / G operationalization / G0/G1 定义 /
G1 template / insertion rule / group-token rule / firewall / outcome policy / matcher identity /
replication policy / call-order policy / aggregate enum semantics / nontriviality gate /
runtime freeze / statelessness / residual-failure gate），经 deterministic canonical JSON → SHA-256：

```text
V4_8_1_EXPERIMENT_DESIGN_DIGEST = e11d83797ed89c99f335f58f7317997c513b626c02304e0fe4333d40dc0f48bf
EXPERIMENT_DESIGN_CHANGED_AFTER_FIRST_CALL = NO
```

---

## I. Scientific Question

见 §A。可检验的 causal claim 命名限定为 `EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION`，
**不**等价于「all chunk-to-document aggregation mechanisms」。

---

## J. Operationalization Boundary

```text
G_OPERATIONALIZATION = EXPLICIT_MEMBERSHIP_METADATA_ONLY
PHYSICAL_CHUNK_REGROUPING = NO
CHUNK_REORDERING = NO
DOCUMENT_SUMMARIZATION = NO
```

---

## K. Primary Residual Targets

```text
md-009
md-015
```

未增加其它 primary target。

---

## L. md-004 Reference Role

```text
md-004 = NON_PRIMARY_CONTROL_REFERENCE （NO-REGRESSION / GENERALIZATION REFERENCE）
MD004_REFERENCE_PAIR_REQUIRED = NO
```

判定依据（§52）：两个 primary case 的 `G = NOT_SUPPORTED`，且 remediation readiness 显然为 NO，
因此**不需要** no-regression/reference check。未为「完成矩阵」进行无意义 model call。
`V4.8 md-004 M1/M2 classification` 未改写。

---

## M. Grouping-information Nontriviality

```text
md-009: CHUNK_COUNT=5  UNIQUE_DOCUMENT_COUNT=2  GROUP_SIZES=[4,1]      GROUPING_INFORMATION_NONTRIVIAL = YES
md-015: CHUNK_COUNT=5  UNIQUE_DOCUMENT_COUNT=4  GROUP_SIZES=[2,1,1,1]  GROUPING_INFORMATION_NONTRIVIAL = YES
md-004: CHUNK_COUNT=5  UNIQUE_DOCUMENT_COUNT=4  GROUP_SIZES=[1,1,1,2]  GROUPING_INFORMATION_NONTRIVIAL = YES
```

两 primary case 均满足 `UNIQUE_DOCUMENT_COUNT < CHUNK_COUNT` 且至少一个 `GROUP_SIZE >= 2`，
在**任何** primary model call 之前机械计算。

---

## N. Factor G

```text
G = EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION
```

在不改变已有 chunks、chunk 顺序、chunk 内容、canonical titles、material labels、
production task instruction 与 citation contract 的前提下，**仅**增加由 frozen `document_id`
机械推导的 opaque same-document membership metadata。

---

## O. G0

```text
G0 = A0 + B0 + NO explicit cross-chunk document-membership metadata  （production-equivalent）
```

---

## P. G1

```text
G1 = G0 + exactly one membership-metadata block
```

保持不变：same query / history / scope / retrieved chunks / chunk order / chunk text /
canonical titles / title occurrence count / material labels / production task instruction /
citation contract / model / generation parameters。唯一新增：opaque chunk → document membership metadata。

---

## Q. G1 Template / Insertion Rule

冻结模板：

```text
[同源关系]
组A: 材料1, 材料2, 材料3, 材料4
组B: 材料5
```

```text
[同源关系]
组A: 材料1, 材料2
组B: 材料3
组C: 材料4
组D: 材料5
```

插入规则（首次 model call 前冻结，所有 case 一致）：

```text
在完整 evidence/context serialization 结束后、最终 question/task suffix 之前插入:
pieces = user_content.split('\n\n')
new_content = '\n\n'.join(pieces[:-1] + [membership_block] + [pieces[-1]])
SAME_INSERTION_RULE_ACROSS_CASES = YES
```

未使用 `absolute title character offset unchanged` 作为门禁；仅保持既有 evidence 序列内的**相对位置**。
未加入任何 naming instruction（见 §S）。

---

## R. Group-information Firewall

```text
GROUP_TOKEN_TITLE_LEAKAGE            = NO
GROUP_TOKEN_DOCUMENT_ID_LEAKAGE      = NO
GROUP_TOKEN_SOURCE_NAME_LEAKAGE      = NO
GROUP_TOKEN_PATH_LEAKAGE             = NO
GROUP_TOKEN_GOLDEN_ROLE_LEAKAGE      = NO
GROUP_TOKEN_EXPECTED_ANSWER_LEAKAGE  = NO
NAMING_INSTRUCTION_CONTAMINATION     = NO
GROUP_INFORMATION_FIREWALL           = PASS
```

group token 由「原始 chunk order 中首次出现的 unique document」机械决定（first → 组A，second → 组B，…），
不泄漏 `document_id`；无 manual assignment / alphabetical title sorting / DB iteration order / hash ordering。

---

## S. Counterfactual Equivalence

每个 case 的 G0→G1 semantic diff **仅**含一项：

```text
changed_keys       = ['membership_block']
AUTHORIZED_INTERVENTION_DIFF = PASS
```

结构不变量（两 case 均成立）：

```text
EXISTING_CONTENT_ORDER_UNCHANGED = YES
CHUNK_ORDER_UNCHANGED            = YES
TITLE_TEXT_UNCHANGED             = YES
TITLE_OCCURRENCE_COUNT_UNCHANGED = YES
TITLE_RELATIVE_POSITION_WITHIN_EXISTING_EVIDENCE_UNCHANGED = YES
MATERIAL_LABELS_UNCHANGED        = YES
EVIDENCE_TEXT_UNCHANGED          = YES
TASK_INSTRUCTION_UNCHANGED       = YES
SYSTEM_MESSAGE_UNCHANGED         = YES

TITLE_SALIENCE_CONFOUNDED = NO
ORDER_CONFOUNDED          = NO
```

所有调用为 independent stateless diagnostic call：`CROSS_CALL_GENERATED_STATE = NONE`，
`history` 取自 frozen V4.7 case history（非先验生成答案）。

---

## T. Context-length / Truncation

```text
md-009: prompt_eval_count G0=1577 / G1=1613   num_ctx=8192   TRUNCATION_OCCURRED = NO
md-015: prompt_eval_count G0=1531 / G1=1573   num_ctx=8192   TRUNCATION_OCCURRED = NO

ALL_ORIGINAL_EVIDENCE_MODEL_VISIBLE = YES
ALL_ORIGINAL_TITLES_MODEL_VISIBLE   = YES
HISTORY_MODEL_VISIBLE               = YES
QUESTION_MODEL_VISIBLE              = YES
```

---

## U. Runtime Identity

```text
MODEL_IDENTITY = qwen2.5:7b
MODEL_DIGEST   = 845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e
GENERATION_PARAMETERS = temperature 0 / top_p 1 / top_k 1 / repeat_penalty 1.15 /
                        num_predict 800 / num_ctx 8192 / keep_alive 10m / stream false
SEED = NOT_AVAILABLE（production 不设 seed）
```

每个 comparable pair 使用相同 runtime identity；`PAIR_RUNTIME_VALIDITY = PASS`。

---

## V. md-009 Results

```text
query            = 哪些文档提到了 RAKE 接收机？
GROUPING_INFORMATION_NONTRIVIAL = YES
RESIDUAL_FAILURE_REPRODUCED     = YES
G0_RUN_COUNT = 1    G1_RUN_COUNT = 1
```

| cond | raw answer |
|---|---|
| G0 | `材料1、材料2和材料5都提到了RAKE接收机。[1][2][5]` |
| G1 | `材料1、材料2、材料3和材料4都提到了RAKE接收机。[组A]` |

```text
G0_Y = [0]   G1_Y = [0]   DELTA_G = 0.0
O1_CANONICAL_TITLE_EMITTED    : NO / NO
O2_GENERIC_MATERIAL_IDENTITY_USED : YES / YES
O5_DOCUMENT_SET_CORRECT       : NOT_ESTABLISHED / NOT_ESTABLISHED
EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT = NOT_SUPPORTED
EXPLICIT_MEMBERSHIP_ISOLATED       = NO
SOURCE_REFERENT_PRESERVED = YES   FACTUAL_CONTENT_PRESERVED = YES
TRUNCATION_OCCURRED = NO   AUTHORIZED_INTERVENTION_DIFF = PASS
PAIR_RUNTIME_VALIDITY = PASS   COUNTERFACTUAL_VALIDITY = PASS
RESIDUAL_MECHANISM_STATUS = MEMBERSHIP_REPRESENTATION_UNRESPONSIVE
```

> 观察：G1 的输出**引用了** `[组A]`，即模型确实读取并使用了 membership metadata，但仍以**材料编号**
> 表达文档身份，未产生 canonical title。operationalized G **未**修复该 residual failure。

---

## W. md-015 Results

```text
query            = 哪份文档明确把 OFDMA 与 LTE 关联？
GROUPING_INFORMATION_NONTRIVIAL = YES
RESIDUAL_FAILURE_REPRODUCED     = YES
G0_RUN_COUNT = 1    G1_RUN_COUNT = 1
```

| cond | raw answer |
|---|---|
| G0 | `材料1、2明确了OFDMA与LTE的关系[1][2]。其中，材料1指出“下行OFDMA：上行SC-FDMA”是LTE的一种传输方案；材料2则详细对比了TD-SCDMA、LTE和802.16e三种系统的传输方案，并明确表示LTE使用的是下行OFDMA和上行SC-FDMA的组合[2]。` |
| G1 | `材料2明确把OFDMA与LTE关联[2]。具体表现在材料2中提到“下行OFDMA：上行SC-FDMA”以及“6.1.4 OFDM基本原理 …”，虽然直接关联词不出现，但通过对比表中信息可以推断OFDMA是LTE的一种传输方案。[2]` |

```text
G0_Y = [0]   G1_Y = [0]   DELTA_G = 0.0
O1_CANONICAL_TITLE_EMITTED    : NO / NO
O2_GENERIC_MATERIAL_IDENTITY_USED : YES / YES
O5_DOCUMENT_SET_CORRECT       : NOT_ESTABLISHED / NOT_ESTABLISHED
EXPLICIT_MEMBERSHIP_CAUSAL_SUPPORT = NOT_SUPPORTED
EXPLICIT_MEMBERSHIP_ISOLATED       = NO
SOURCE_REFERENT_PRESERVED = YES   FACTUAL_CONTENT_PRESERVED = YES
TRUNCATION_OCCURRED = NO   AUTHORIZED_INTERVENTION_DIFF = PASS
PAIR_RUNTIME_VALIDITY = PASS   COUNTERFACTUAL_VALIDITY = PASS
RESIDUAL_MECHANISM_STATUS = MEMBERSHIP_REPRESENTATION_UNRESPONSIVE
```

---

## X. md-004 Reference Result

```text
MD004_REFERENCE_PAIR_REQUIRED = NO
md-004: CONTROL_REFERENCE_EXECUTED = NO
        G0_Y = NOT_RUN   G1_Y = NOT_RUN
        CONTROL_REFERENCE_NO_REGRESSION       = NOT_RUN
        CONTROL_REFERENCE_GENERALIZATION_SIGNAL = NOT_RUN
        V4_8_M1_M2_CLASSIFICATION_CHANGED     = NO
```

---

## Y. Per-case Membership Attribution

| case | G0_Y | G1_Y | ΔG | causal support | isolated | hypothesis status |
|---|---|---|---|---|---|---|
| md-009 | [0] | [0] | 0.0 | NOT_SUPPORTED | NO | NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION |
| md-015 | [0] | [0] | 0.0 | NOT_SUPPORTED | NO | NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION |

判据（§46）：G0 stably fails、G1 stably fails、counterfactual valid ⇒ NOT_SUPPORTED。
未计算、也未宣称 p-value / statistical significance。

---

## Z. Residual-subset Aggregate Support

```text
RESIDUAL_SUBSET_SHARED_MEMBERSHIP_SUPPORT = NO
```

按 §49 冻结 enum 机械计算（两 case 均有充分有效证据且均 NOT_SUPPORTED ⇒ NO）。

---

## AA. Heterogeneous vs Mixed Residual State

```text
HETEROGENEOUS_RESIDUAL_RESPONSE = NO      （两 case 响应一致：G0 FAIL / G1 FAIL）
MIXED_RESIDUAL_MECHANISMS       = NOT_ESTABLISHED
```

未因结果一致而**虚构** shared mechanism；未将 heterogeneous/mixed 概念外推。

---

## AB. Broader Aggregation-hypothesis Boundary

```text
CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS = NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION
```

解释**限定**为：当前 operationalized explicit-membership metadata **没有**修复该 residual failure。
**未**扩大为「all possible grouping approaches are impossible」；本轮未测试 physical regrouping /
document-level reordering / document-summary generation。

---

## AC. Product / Measurement Separation

Product 判定完全复用 V4.8 closure 后冻结的 `DOCUMENT_IDENTITY_RESPONSE_SUCCESS` 与
`TITLE_MATCH_NORMALIZATION_POLICY`（matcher 未修改）。Measurement-supporting 观测（O7 role term 等）
单独记录，`O7 = SUPPORTING_ONLY`，**不参与** primary Y。

```text
md-009: O7_ROLE_TERM_EMITTED G0=NO / G1=NO   O6_DUPLICATE=NO   O4_FACTUAL=YES
md-015: O7_ROLE_TERM_EMITTED G0=NO / G1=NO   O6_DUPLICATE=NO   O4_FACTUAL=YES
```

---

## AD. Global Generation-mechanism State

```text
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
```

md-004 仍为 `M1 + M2 multiple sufficient interventions without isolation`；本轮两个 primary case
均未建立 G isolation。因此 global state **未**自动升级。

---

## AE. Remediation Readiness

```text
MEMBERSHIP_REPRESENTATION_REMEDIATION_CANDIDATE = NOT_ESTABLISHED
READY_FOR_SEPARATE_MEMBERSHIP_REMEDIATION_AUTHORIZATION = NO
PRODUCT_REMEDIATION_AUTHORIZED = NO
```

---

## AF. Product Mutation Audit

```text
V4_8_ARTIFACTS_MODIFIED = NO      V4_7_ARTIFACTS_MODIFIED = NO
PRODUCT_CODE_MODIFIED = NO        PRODUCTION_PROMPT_MODIFIED = NO
CONTEXT_PIPELINE_MODIFIED = NO    RETRIEVAL_MODIFIED = NO
RANKING_MODIFIED = NO             RUNTIME_DB_MODIFIED = NO
EMBEDDINGS_MODIFIED = NO          GOLDEN_MODIFIED = NO
EVALUATOR_MODIFIED = NO           CITATION_SEMANTICS_MODIFIED = NO
BASELINE_CHANGED = NO             PRODUCT_METRICS_RECOMPUTED = NO
HISTORICAL_CLAIM_STRENGTH_CHANGED = NO
PRESTATE_SNAPSHOT_OVERWRITTEN = NO
EXPERIMENT_DESIGN_CHANGED_AFTER_FIRST_CALL = NO
```

`CANONICAL_PRODUCTION_HASH_AFTER = 108fb167…798c`（= BEFORE）。

---

## AG. Frozen Artifact Audit

`V4_8_FROZEN_ARTIFACT_HASHES`、`V4_7_FROZEN_ARTIFACT_HASHES`、`BASELINE_ARTIFACT_HASHES`、
`GOLDEN_HASH`、`V4_6_HISTORICAL_ARTIFACT_HASHES` 全部与本轮开始前一致（逐项 SHA-256 匹配）。

---

## AH. Tests

```text
python -m unittest tests.test_v4_8_1_residual_generation_diagnosis -v  → 59 tests OK
python -m unittest tests.test_live_production_hash_guard -v           → 6 tests OK
python -m unittest tests.test_v4_6_2_hash_portability -v              → 15 tests OK
```

覆盖 T1–T55（parent freeze / preflight snapshot / design freeze / targets & factors /
nontriviality / firewall / counterfactual equivalence / runtime & call policy /
contemporaneous control / Product-Measurement separation / causal-isolation policy /
aggregate semantics / md-004 reference boundary / governance boundary / artifact integrity）。
未运行 Full-144、未做 broad Product evaluation、未引入未授权 factor。

---

## AI. Final Decision

```text
V4_8_1_PROTOCOL_EXECUTION = PASS

md-009 / md-015: G0 residual failure 复现，G1 未修复；counterfactual valid。
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_CAUSAL_SUPPORT = NO
EXPLICIT_DOCUMENT_MEMBERSHIP_REPRESENTATION_ISOLATED        = NO
RESIDUAL_SUBSET_SHARED_MEMBERSHIP_SUPPORT                   = NO
CHUNK_TO_DOCUMENT_AGGREGATION_HYPOTHESIS_STATUS = NOT_SUPPORTED_BY_THIS_OPERATIONALIZATION
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
```

科学结论限定于 **CURRENT PIPELINE**；未升级历史 V4.6 claim；未移动 baseline。

---

## AJ. Next Authorization Boundary

```text
NEXT_RESIDUAL_HYPOTHESIS = NOT_ESTABLISHED
NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO
PRODUCT_REMEDIATION_AUTHORIZED = NO
```

本阶段不推进任何后续实验；下一 candidate 必须由下一次独立授权定义。

---

## AK. STOP

V4.8.1 完成，立即停止。未执行：modify build_messages / 向 production 添加 membership metadata /
physical regroup / 修改 material headers / 修改 production prompt / 修改 retrieval/ranking /
修改 Golden/evaluator / 修改 citation semantics / 创建 Product baseline / Full-144 /
修改 roadmap / 修改 V4.8 parent artifacts / sync Publish / commit / push / tag / release。
