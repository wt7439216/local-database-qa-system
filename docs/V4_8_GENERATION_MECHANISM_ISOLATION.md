# KB-V4 — V4.8 Generation / Prompt-Evidence Framing Mechanism Isolation

```text
MODE = CONTROLLED COUNTERFACTUAL / MECHANISM ISOLATION ONLY
       + FROZEN-EVIDENCE REANALYSIS / CLASSIFICATION-CLOSURE（V4.8 Diagnosis Closure）

V4_8_DIAGNOSIS_CLOSURE         = PASS
V4_8_PROTOCOL_EXECUTION        = PASS
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED

PRODUCT_REMEDIATION_AUTHORIZED = NO
BASELINE_CHANGED               = NO
NEW_MODEL_CALLS                = 0
```

机器事实源：`eval/v4_8_generation_mechanism_isolation.json`
Harness：`scripts/analyze_v4_8_generation_mechanism.py`（diagnostic-only）
Tests：`tests/test_v4_8_generation_mechanism_diagnosis.py`（36 tests）
`ARTIFACT_TYPE = DIAGNOSTIC_ONLY` · `IS_PRODUCT_BASELINE = NO`

---

## A. Scope

受控、只读、诊断性质的 **2×2 factorial counterfactual**：在冻结 Product、retrieval evidence、Golden、evaluator、
baseline、runtime DB 与 production implementation 的前提下，判断当前 document-identity Generation failure
主要受 `MATERIAL_INDEX_REPRESENTATION_BIAS`、显式 `PROMPT_FRAMING / NAMING INSTRUCTION`、二者 interaction，
还是其它 Generation mechanism 驱动。

本轮**未**修改任何 production 行为、prompt、material header、retrieval/ranking、Golden、evaluator、citation semantics 或 baseline。
V3 未触碰；Publish 未写入；未 sync / commit / push / tag / release。

## B. Frozen Inputs

```text
eval/v4_7_document_identity_root_cause.json     v4_7_diagnosis_closure = PASS
docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md
docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md

parent_closure:
  generation_remediation_scope_ready = YES（机器事实；见 §AD）
  generation_mechanism_isolation     = NOT_ESTABLISHED
  shared_generation_mechanism_name   = MATERIAL_INDEX_REPRESENTATION_BIAS
```

输入 artifact 的 SHA-256 记录于 artifact `input_artifact_hashes`；全部在 §AE 复核未变。

## C. Sources of Truth / Field Mapping

| expected semantic state | actual field | value | mapping_type |
|---|---|---|---|
| parent closure | `parent_closure.v4_7_diagnosis_closure` | `PASS` | EXACT |
| generation scope readiness | `generation_remediation_scope_ready_machine_fact` | `YES`（原样保留，不进一步解释） | EXACT |
| current baseline | `current_baseline` | `V4_6_2_HASH_PORTABILITY_BASELINE` | EXACT |
| metrics source | `product_metrics_source` | `V4_6_1_EMBEDDING_IDENTITY_BASELINE` | EXACT |
| production hash | `production_hash` | `108fb167…798c` | EXACT |
| measurement issue | `measurement_boundary.MEASUREMENT_SEMANTIC_ISSUE` | `SUPPORTED` | EXACT |
| historical anchor | `historical_claim_boundary.HISTORICAL_SOURCE_ANCHOR_AVAILABLE` | `NO` | EXACT |

```text
FIELD_MAPPING_STATUS = EXACT（无 invented state）
REMEDIATION_SCOPE_READY_DEFINITION_SOURCE = NOT_AVAILABLE
REMEDIATION_SCOPE_READY_SEMANTICS        = NOT_FURTHER_INTERPRETED
```

`GENERATION_REMEDIATION_SCOPE_READY` 的机器事实 `YES` 被**保留**，本轮未将其解释为
"dominant mechanism known / minimal remediation proven / remediation ready / authorized"。

## D. Remote / Cross-reference Preflight

```text
REMOTE_MAIN_HEAD             = 1efc74f1c5aa4021766ed443f68ef8c5046116e4（git ls-remote，只读）
REMOTE_HEAD_MATCHES_EXPECTED = YES

V4_8_CROSS_REFERENCE_AUDIT   = PASS
  patterns                   = V4.8 / History Resolution / Generation Mechanism Isolation /
                               GENERATION_MECHANISM_ISOLATION / MATERIAL_INDEX_REPRESENTATION_BIAS
  hits                       = 92
  CURRENT_STALE_REFERENCE    = 0
  HISTORICAL_REFERENCE       = 3（governance audit report / frozen V4.7 closure / historical V4.6）
  NO_CONFLICT                = 89
  CROSS_REFERENCE_EDIT_AUTHORIZED = NO
```

无 current V4.8 identity 歧义（旧 `V4.8 — History Resolution` 已在上一阶段顺延为 V4.9）⇒ 未触发 STOP。

## E. Production Implementation Mapping

```text
answer-model invocation      core/engine_v2.py::StructuredQAEngine.answer → self.ollama.chat(messages, model=...)
                             core/ollama_http.py::OllamaClient.chat → POST /api/chat
message construction         core/engine_v2.py::build_messages
context serialization        build_messages（re.sub(r"\s+"," ",chunk.text).strip() + token budget）
material/evidence header     header = f"[材料{index}｜{chunk.location}]\n"
retrieval → model-visible    LibraryStore.retrieve → HybridRetriever.retrieve → PreparedAnswer.contexts
                             → build_messages → sent（本轮不重跑）
runtime model parameters     model=qwen2.5:7b, temperature 0, top_p 1, top_k 1,
                             repeat_penalty 1.15, num_predict 800, num_ctx 8192, keep_alive 10m, stream false
```

Harness 复用 **V4.7 已捕获的 production messages**（`per_case_layer_trace[*].final_application_model_request.messages`）
并以**未修改的 production `OllamaClient`** 发送 ⇒ C0 为 production-equivalent control，且未重跑 retrieval / ranking / embeddings。

## F. Pre-change Integrity

```text
CANONICAL_PRODUCTION_HASH_BEFORE = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
core    = ce33e5504bebc1a3941ce381c77baad1716acd845f5e80b97c3f515016a78db0
desktop = 22173f277d0b3ac1fbc6935c24e2f217e2f5df196e43ba4dd8ca5e392b1120a2
web     = 7283dfb676ce5355f6911cf3fdf7790722a97a95479986cf815311161057bbaf

RUNTIME_DB_PATH          = data/library/documents.sqlite3
RUNTIME_DB_IDENTITY_BEFORE = 10698752:c6bc9b3eb63ae4e6
RUNTIME_DB_SHA256        = c6bc9b3eb63ae4e6d96caf859a2b0c5f2f1e5a5b6f438e81aa0bbc3cf4084c97
```

PRE_CHANGE_WORKSPACE_MANIFEST = 296 files；`WORKSPACE_MANIFEST_SCOPE` / `MANIFEST_EXCLUSIONS` 沿用上一阶段既有治理惯例
（`__pycache__/`、`*.pyc/*.pyo`、`.venv/`、`venv/`、`.ruff_cache/`、`.pytest_cache/`、`.mypy_cache/`、`.git/`、
`data/eval_cache/`、`data/logs/`）。

```text
AUTHORIZED_V4_8_DIAGNOSTIC_PATHS =
    scripts/analyze_v4_8_generation_mechanism.py
    tests/test_v4_8_generation_mechanism_diagnosis.py
    eval/v4_8_generation_mechanism_isolation.json
    docs/V4_8_GENERATION_MECHANISM_ISOLATION.md
```

## G. Product / Measurement Separation

```text
Product question      canonical title 已进入 model-visible context 后，为什么模型仍用 generic 材料N 表示文档身份？
Measurement question  frozen Golden/evaluator 对 canonical title 与 semantic-role token（教材）是否存在表示层不一致？
```

```text
MEASUREMENT_SEMANTIC_ISSUE = SUPPORTED（md-004 / md-009 SUPPORTED；md-015 NOT_OBSERVED）
MEASUREMENT_TRACK          = DEFERRED_SEPARATE_TRACK
```

本轮**未**修改 Golden / aliases / evaluator / substring matcher / metric semantics / citation semantics。
O7（role-term emission）仅作为 measurement-supporting observable 记录，**不参与** Product 成败判定。

## H. Control Reproduction

```text
C0 = A0 + B0（production-equivalent）
MODEL_IDENTITY     = qwen2.5:7b
MODEL_DIGEST       = 845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e
GENERATION_PARAMS  = temperature 0 / top_p 1 / top_k 1 / repeat_penalty 1.15 / num_predict 800 / num_ctx 8192
SEED               = NOT_AVAILABLE（production 不设 seed；generation 层为 stochastic）
CONTEXT_IDENTITY   = 与 V4.7 捕获的 sent_contexts / material headers 完全一致（见 §N）
```

| case | CONTROL_FAILURE_REPRODUCED | C0 raw answer |
|---|---|---|
| md-004 | YES | 分集接收在材料1、材料2和材料3中的文档中被提及。[1][2][3] |
| md-009 | YES | 材料1、材料2和材料5都提到了RAKE接收机。[1][2][5] |
| md-015 | YES | 材料1、2明确了OFDMA与LTE的关系[1][2]。…（与 V4.7 逐字一致） |

```text
CONTROL_REPRODUCIBILITY = ESTABLISHED
```

措辞在 stochastic run 间轻微变化（md-004 C0 与 V4.7 相差“中的文档”四字），但目标 phenotype
（**generic material/evidence identity 代替 canonical document identity**）三例稳定复现 ⇒ 无需额外 control run，
且未触发 §17 的任何 drift 停止条件（模型身份、生成参数、evidence identity、context identity 均未漂移）。

## I. Factorial Design

```text
              B0（production instruction）        B1（+ frozen title-naming instruction）
A0（材料N）    C0 = control                        C2 = B main-effect probe
A1（证据块N）  C1 = A main-effect probe             C3 = combined / interaction
```

3 target cases × 4 conditions = 12 cells，`RUN_COUNT_PER_CELL = 1`（control 稳定，未使用 replication）。

## J. M1 Operational Definition

```text
M1_OPERATIONALIZATION =
  the lexical / semantic document-identity cue introduced by the production "材料N" label,
  while preserving the structural numeric evidence index

STRUCTURAL_INDEX_PRESERVED = YES
```

A1 只把证据块 label token `材料` → `证据块`，**保留**结构编号。
因此本轮 M1 结论**仅**覆盖 “材料N” 表示的 semantic identity cue，**不得**外推为 “numeric indexing itself is causal”。

## K. Factor A

```text
A0 = [材料1｜<document_title · 页码 · 章节>] <text>    （production）
A1 = [证据块1｜<完全相同的位置串>] <完全相同正文>       （仅 label token 改变）

FACTOR_A_TRANSFORMATION_RULE（pre-run 冻结）
  regex (?m)^\[材料(\d+)｜ -> [证据块\1｜
  只作用于 USER message 的 material-header 行
```

## L. Factor B

```text
B0 = production task instruction（不改）
B1 = 当问题要求指出哪些文档、哪份文档或文档身份时，请使用上下文中已经提供的真实文档标题回答。
     插入位置：user message 第一行（任务要求）之后；三例共用同一文本
```

```text
B1_contains_anti_material_index_instruction = NO
B1_case_invariant                           = YES
```

## M. Pre-run Factor Freeze

```text
factor_freeze_digest = 8cd479b693f2313f423834c8a27dcf6264aa90cfe679b0fd3da21003202d4a9
frozen_before_first_model_call = True
protocol_adaptation_after_outcome = NO
```

冻结内容：`FACTOR_A_TRANSFORMATION_RULE`、`FACTOR_A_LABEL_REGEX/REPLACEMENT`、`FACTOR_B_INSTRUCTION_TEXT`、
`TITLE_MATCH_NORMALIZATION_POLICY`、`REPLICATION_POLICY`、`AUTHORIZED_INTERVENTION_FIELDS`、`M1_OPERATIONALIZATION`。

> 说明：执行后**未**改动 A1 规则、B1 文本或 success criterion（Y）。为使 matcher 能实现 §32 自身的示例
> （`《移动通信（李兆玉）》` vs canonical `移动通信 (李兆玉)`）、并消除 O7 被 `移动通信测试文档` 内含 `测试文档`
> 污染的问题，做了一次**派生分析澄清**：O5 收紧到 §34 的完整文档集定义、title 比较改为 whitespace-insensitive、
> O7 改为在剔除 canonical title 后的残差上度量。三者**未改变任何 cell 的 Y**（`first_execution_Y` 已记录于 artifact，
> 与最终 Y 完全一致）。这三项以 `derived_analysis_refinements` 显式记录，不写入 pre-run freeze。

## N. Intervention Diff Validation

机械比较每个 case 的四个 condition 的 semantic request object：

```text
case      C0_vs_C1            C0_vs_C2             C0_vs_C3
md-004    [materials]         [instruction_lines]  [materials, instruction_lines]
md-009    [materials]         [instruction_lines]  [materials, instruction_lines]
md-015    [materials]         [instruction_lines]  [materials, instruction_lines]
```

```text
evidence_text_unchanged                          = True（3/3）
evidence_order_unchanged                         = True（3/3）
canonical_title_content_and_position_unchanged   = True（3/3）
structural_numeric_index_preserved               = True（3/3）
system_message identical across conditions       = True
authorized_intervention_diff_only                = YES
counterfactual_validity:
  A1_title_salience_confounded          = NO
  A1_structural_index_confounded        = NO
  B1_case_invariant                     = YES
  B1_contains_anti_material_index_instruction = NO
  citation_representation_confounded    = NO
```

`MODEL_VISIBLE_REQUEST_DIGEST`（canonical JSON → SHA-256）对 12 个 cell 逐一记录于 artifact
`model_visible_request_digests`。无未授权模型可见差异 ⇒ 无 `INVALID_COUNTERFACTUAL`。

## O. C0（production-equivalent control）

```text
md-004  分集接收在材料1、材料2和材料3中的文档中被提及。[1][2][3]     O1=NO O2=YES Y=0
md-009  材料1、材料2和材料5都提到了RAKE接收机。[1][2][5]            O1=NO O2=YES Y=0
md-015  材料1、2明确了OFDMA与LTE的关系[1][2]。…                     O1=NO O2=YES Y=0
```

## P. C1（A1 + B0）

```text
md-004  分集接收在证据块1、证据块2和证据块3中的移动通信测试文档以及证据块4和证据块5中的
        《移动通信 (李兆玉)》一书中被提及。[1-5]                     O1=YES O2=NO Y=1
md-009  [证据块1]、[证据块2]和[证据块3]提到了RAKE接收机。            O1=NO  O2=YES Y=0
md-015  证据块1、2明确提到了LTE使用了OFDMA作为其多址接入技术[1][2]。… O1=NO  O2=YES Y=0
```

## Q. C2（A0 + B1）

```text
md-004  分集接收在以下文档中被提到：- 移动通信测试文档 [1] - 第1章移动通信测试文档 [3]
        - 移动通信 (李兆玉) [4]                                    O1=YES O2=NO Y=1
md-009  材料1、材料2和材料5都提到了RAKE接收机。[1][2][5]            O1=NO  O2=YES Y=0
md-015  材料1明确把 OFDMA 与 LTE 关联[1]。                          O1=NO  O2=YES Y=0
```

## R. C3（A1 + B1）

```text
md-004  分集接收在以下文档中被提到：- 移动通信测试文档 [1] - 第1章移动通信测试文档 [2]
        - 移动通信 (李兆玉) [3]                                    O1=YES O2=NO Y=1
md-009  证据块1、证据块2和证据块5提到了RAKE接收机。[1][2][5]        O1=NO  O2=YES Y=0
md-015  [证据块1]…[证据块5]都提到了OFDMA是LTE采用的多址方式，但最直接关联的是[证据块2]。
        该文档明确指出：…                                          O1=NO  O2=YES Y=0
```

> md-015 C3 值得注意：模型**形成了文档级指代**（「该文档」）却没有给出 canonical title。

## S. Factorial Contrasts

```text
case      Y(C0) Y(C1) Y(C2) Y(C3)   ΔA|B0  ΔA|B1  ΔB|A0  ΔB|A1  interaction
md-004      0     1     1     1         +1     0      +1      0        -1
md-009      0     0     0     0          0     0       0      0         0
md-015      0     0     0     0          0     0       0      0         0
```

样本极小 ⇒ **不报告 p 值、不宣称统计显著性**；contrasts 只用于 mechanical causal pattern attribution。

## T. md-004

```text
PRODUCT_NAMING_BEHAVIOR                    C0 generic only；C1/C2/C3 均命名 canonical title
GENERIC_EVIDENCE_IDENTITY_ONLY_RESPONSE    C0 YES；C1/C2/C3 NO
MEASUREMENT_ROLE_TERM_BEHAVIOR             C1 出现「测试文档」语境词；C2/C3 无（O7 分别 YES/NO/NO）

primary mechanism      MULTIPLE_SUFFICIENT_INTERVENTIONS（C1 与 C2 各自单独足够；A / B 不可分离）
secondary contributors INTERACTION_PATTERN = SUBADDITIVE_BINARY_CEILING_COMPATIBLE（interaction = −1）
isolation status       M1 / M2 均 not isolated（互相遮蔽）⇒ MECHANISM_ISOLATION_STATUS = NOT_ESTABLISHED
```

## U. md-009

```text
PRODUCT_NAMING_BEHAVIOR                    C0/C1/C2/C3 全部 generic only
GENERIC_EVIDENCE_IDENTITY_ONLY_RESPONSE    YES ×4
MEASUREMENT_ROLE_TERM_BEHAVIOR             全程无 role term

primary mechanism      M4_PHASE_LOCAL_RESIDUAL_FAILURE（两个 framing intervention 均无法解释/修复）
secondary contributors 无
isolation status       NOT_ESTABLISHED（residual 位于两个被测 factor 之外 ⇒ M5 residual）
M4 phase-local / global SUPPORTED / NOT_ESTABLISHED
```

## V. md-015

```text
PRODUCT_NAMING_BEHAVIOR                    C0/C1/C2/C3 全部 generic only；C3 出现文档级指代「该文档」但无 title
GENERIC_EVIDENCE_IDENTITY_ONLY_RESPONSE    YES ×4
MEASUREMENT_ROLE_TERM_BEHAVIOR             全程无 role term

primary mechanism      M4_PHASE_LOCAL_RESIDUAL_FAILURE
secondary contributors 无（grouping-related 观察见 §AA）
isolation status       NOT_ESTABLISHED
M4 phase-local / global SUPPORTED / NOT_ESTABLISHED
```

## W. Product Observables

每 cell 完整 `O1..O7` 记录于 artifact `product_observables`。要点：

```text
O1_CANONICAL_TITLE_EMITTED              仅 md-004 C1/C2/C3 = YES（其余 9 cells = NO）
O2_GENERIC_MATERIAL_IDENTITY_USED       相应为 NO / YES
O5_DOCUMENT_SET_CORRECT                 采用 §34 完整文档集定义（3 个 PASS cell 的期望文档集均完整覆盖）
O6_DUPLICATE_DOCUMENT_IDENTITY_EMITTED  全部 NO
O4_FACTUAL_CONTENT_PRESERVED            12/12 YES（无 factual regression）
```

`DOCUMENT_IDENTITY_RESPONSE_SUCCESS`（主 Y）= PASS 仅 3/12 cells（md-004 的 C1/C2/C3）。
canonical title + citation 形式（如 `《移动通信 (李兆玉)》[4]`）计为 PASS；citation 编号本身不构成 Product failure。

## X. Measurement Supporting Observations

```text
O7_ROLE_TERM_EMITTED（MEASUREMENT-SUPPORTING ONLY，不参与 Product 成败）
  在剔除 canonical title 后的残差上度量，避免 移动通信测试文档 / 测试文档 的子串污染
  md-004 C1 = YES（出现「测试文档」字样）；其余 11 cells 中仅 md-004 C2/C3 为 NO
```

Measurement semantic issue（canonical title vs Golden 角色词 `教材`）保持 `SUPPORTED` 且仍为**独立轨道**；
本轮不得以其推翻 Product counterfactual 结果，Product 结果也不得改写 Measurement 结论。

## Y. Per-case Mechanisms

Per-case 归因**先行**；每一字段均由该 case 自身证据机械派生（非先定 aggregate 再复制）。

| case | M1 causal support | M2 causal support | MULTIPLE_SUFFICIENT_INTERVENTIONS | MULTIPLE_CONTRIBUTING_FACTORS | M3 interaction | INTERACTION_PATTERN | M4 phase-local | M4 global | M5 residual | specific M5 | isolation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| md-004 | SUPPORTED | SUPPORTED | YES | NOT_ESTABLISHED | NOT_ESTABLISHED | SUBADDITIVE_BINARY_CEILING_COMPATIBLE | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED | NOT_ESTABLISHED | NOT_ESTABLISHED |
| md-009 | NOT_SUPPORTED | NOT_SUPPORTED | NO | NOT_ESTABLISHED | NOT_SUPPORTED | ADDITIVE_OR_NULL | SUPPORTED | NOT_ESTABLISHED | SUPPORTED | NOT_ESTABLISHED | NOT_ESTABLISHED |
| md-015 | NOT_SUPPORTED | NOT_SUPPORTED | NO | NOT_ESTABLISHED | NOT_SUPPORTED | ADDITIVE_OR_NULL | SUPPORTED | NOT_ESTABLISHED | SUPPORTED | NOT_ESTABLISHED | NOT_ESTABLISHED |

```text
primary_mechanism
  md-004 = MULTIPLE_SUFFICIENT_INTERVENTIONS
  md-009 = M4_PHASE_LOCAL_RESIDUAL_FAILURE
  md-015 = M4_PHASE_LOCAL_RESIDUAL_FAILURE
```

关键语义区分（closure 修正）：

```text
MULTIPLE_SUFFICIENT_INTERVENTIONS ≠ MULTIPLE_CONTRIBUTING_FACTORS
    C1 与 C2 各自修复 C0 是观测事实（YES）；「多个独立 contributory factor」是因果主张，
    predeclared policy 从未建立 ⇒ 只能记 NOT_ESTABLISHED（不得 post hoc 升级）。
FACTORIAL_NUMERIC_INTERACTION ≠ MECHANISTIC_INTERACTION
    md-004 interaction = -1 属 ceiling 兼容的 binary subadditivity，不构成 mechanistic antagism。
M4_PHASE_LOCAL_SUPPORT ≠ M4_GLOBAL_STATUS
    phase-local 仅说明「在已授权的 A/B 干预空间内无法修复」；grouping 等结构残差未排除 ⇒ global 为 NOT_ESTABLISHED。
```

## Z. Shared-vs-Mixed Decision

```text
AGGREGATE_SUPPORT_SEMANTICS = FROZEN（YES / PARTIAL / NO / NOT_ESTABLISHED）

M1_SHARED_SUPPORT             = PARTIAL   （md-004 SUPPORTED；md-009 / md-015 NOT_SUPPORTED）
M2_SHARED_SUPPORT             = PARTIAL   （同上）
M3_SHARED_SUPPORT             = NOT_ESTABLISHED
M4_SHARED_PHASE_LOCAL_SUPPORT = PARTIAL   （md-009 / md-015 SUPPORTED；md-004 NOT_SUPPORTED）

HETEROGENEOUS_RESPONSE_PROFILE = YES
MIXED_GENERATION_MECHANISMS    = NOT_ESTABLISHED
SHARED_CAUSAL_MECHANISM        = NOT_ESTABLISHED
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
```

```text
异质响应（md-004 有反应、md-009/015 无反应）是观测事实，
不等于「已机械建立多种 distinct causal mechanism」⇒ MIXED 只能为 NOT_ESTABLISHED。
只有在存在充分排除证据时才可写 SHARED_CAUSAL_MECHANISM = NO；本轮属「未能建立」⇒ NOT_ESTABLISHED。
```

先完成 per-case 归因（§T–§V），再聚合（本节）；未反向倒填，aggregate 亦不覆盖 per-case。

## AA. Secondary Grouping Assessment

```text
SECONDARY_CHUNK_TO_DOCUMENT_AGGREGATION = NOT_TESTED（本轮不把 grouping 作为第三 factor）

GROUPING_RESIDUAL_EVIDENCE_ITEMS（仅引用 frozen evidence；scope = residual cases md-009 / md-015）
  1 multiple sent chunks map to fewer unique documents        HOLDS (5 → 2 / 5 → 4)
  2 model-visible serialization is chunk-centric              HOLDS (header = [材料N｜…] per chunk)
  3 document membership across chunks is implicit             HOLDS (IMPLICIT；header 无 document_id)
  4 target question requires document-level identity          HOLDS (哪些文档)
  5 failed answer tracks evidence units, not documents         HOLDS (O2 = YES ×4)
  6 duplicate/chunk structure blocks document synthesis        NOT_ESTABLISHED（未机械建立）

GROUPING_RESIDUAL_EVIDENCE  = SUPPORTED（1–5 机械成立）
causal_blocking_established = NOT_ESTABLISHED
counter_signal              = md-015 C3 已形成文档级指代「该文档」却未命名

ADDITIONAL_GROUPING_INTERVENTION_REQUIRED = YES（§37：仅当 GROUPING_RESIDUAL_EVIDENCE = SUPPORTED 才允许）
```

⇒ 按 §38 / §44，**不得**自行扩展为 2×2×2、不得测试 grouping，必须 STOP 并等待单独授权。

## AB. Mechanism Isolation

```text
M1_MATERIAL_INDEX_REPRESENTATION_BIAS   = PARTIAL（仅 md-004 支持 ΔA|B0 = +1）
M1_ISOLATED                             = NO
M2_PROMPT_FRAMING                       = PARTIAL（仅 md-004 支持 ΔB|A0 = +1）
M2_ISOLATED                             = NO
M3_INTERACTION_EFFECT                   = NOT_ESTABLISHED
M4_PURE_GENERATION_SYNTHESIS_FAILURE    = PARTIAL（phase-local；md-009 / md-015）
M5_RESIDUAL_OTHER_GENERATION_SUPPORT    = SUPPORTED
SPECIFIC_M5_MECHANISM_IDENTITY          = NOT_ESTABLISHED
MULTIPLE_SUFFICIENT_INTERVENTIONS       = PARTIAL
MULTIPLE_CONTRIBUTING_FACTORS           = NOT_ESTABLISHED

GENERATION_MECHANISM_ISOLATION          = NOT_ESTABLISHED
V4_8_PROTOCOL_EXECUTION                 = PASS
```

科学读解：V4.7 的 “shared mechanism = `MATERIAL_INDEX_REPRESENTATION_BIAS`” **未获得共享因果支持**。
“材料”semantic cue（以及显式标题命名指令）只在 md-004 上表现为充分条件（两因子互相遮蔽、无法分离），
对 md-009 / md-015 均无效；多数 target 的 failure 落在两个已授权 framing factor **之外**，
属 Generation family 内尚未测试的因素（`SPECIFIC_M5_MECHANISM_IDENTITY = NOT_ESTABLISHED`）。

```text
SUPPORTED < ISOLATED  —— 本轮无任何机制达到 ISOLATED
support（支持）          ≠ isolation（隔离）
failure to isolate       ≠ failure to support
protocol PASS 不得被写成 scientific proof
```

## AC. Remediation Readiness

```text
GENERATION_REMEDIATION_CANDIDATE                = NOT_ESTABLISHED
RECOMMENDED_REMEDIATION_MECHANISM               = NOT_ESTABLISHED
READY_FOR_SEPARATE_REMEDIATION_AUTHORIZATION    = NO
PRODUCT_REMEDIATION_AUTHORIZED                  = NO
GENERATION_REMEDIATION_SCOPE_READY（机器事实保留） = YES
REMEDIATION_SCOPE_READY_SEMANTICS               = NOT_FURTHER_INTERPRETED
```

## AD. Product Mutation Audit

```text
PRODUCT_CODE_MODIFIED        = NO
PRODUCTION_PROMPT_MODIFIED   = NO
RETRIEVAL_MODIFIED           = NO
RANKING_MODIFIED             = NO
RUNTIME_DB_MODIFIED          = NO
EMBEDDINGS_MODIFIED          = NO
GOLDEN_MODIFIED              = NO
EVALUATOR_MODIFIED           = NO
CITATION_SEMANTICS_MODIFIED  = NO
BASELINE_CHANGED             = NO
PRODUCT_METRICS_RECOMPUTED   = NO
no new product baseline / CURRENT_PRODUCT_STATE
```

## AE. Frozen Artifact Audit

pre/post SHA-256 证明以下文件未变：

```text
effcbdfd…  eval/v4_7_document_identity_root_cause.json
7073a64a…  docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md
9e338940…  docs/V4_7_CLOSURE_GOVERNANCE_ALIGNMENT.md
18ca7ccb…  eval/v4_baseline_lineage.json
414e5a71…  eval/v4_6_2_hash_portability_baseline.json
2c7b9d0b…  eval/v4_6_1_embedding_identity_baseline.json
31a68507…  eval/v3_final_golden.json
5a644a3f…  eval/v4_6_post_routing_attribution.json
fbac1e51…  docs/V4_POST_ROUTING_ATTRIBUTION.md

governance freeze（未修改）：README.md / CHANGELOG.md / docs/INDEX.md / docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md
runtime DB identity 一致：10698752:c6bc9b3eb63ae4e6
```

## AF. Tests

```text
TESTS_RUN
  python -m unittest tests.test_v4_8_generation_mechanism_diagnosis     59 tests PASS（含 §44 closure C1–C23）
  python -m unittest tests.test_live_production_hash_guard              6 tests PASS
  python -m unittest tests.test_v4_6_2_hash_portability                15 tests PASS
  ---- total 80 tests OK

TESTS_NOT_RUN_BY_DESIGN
  Full-144 / canonical metric recomputation（禁止）
  与 modified files 无关的其它测试套件
```

## AG. Final Decision

```text
V4_8_DIAGNOSIS_CLOSURE  = PASS
V4_8_PROTOCOL_EXECUTION = PASS
CONTROL_FAILURE_REPRODUCED = YES（3/3）
CONTROL_REPRODUCIBILITY    = ESTABLISHED

M1_MATERIAL_INDEX_REPRESENTATION_BIAS = PARTIAL
M2_PROMPT_FRAMING                     = PARTIAL
M3_INTERACTION_EFFECT                 = NOT_ESTABLISHED
M4_PURE_GENERATION_SYNTHESIS_FAILURE  = PARTIAL（phase-local）
M5_RESIDUAL_OTHER_GENERATION_SUPPORT  = SUPPORTED
SPECIFIC_M5_MECHANISM_IDENTITY        = NOT_ESTABLISHED
MULTIPLE_SUFFICIENT_INTERVENTIONS     = PARTIAL
MULTIPLE_CONTRIBUTING_FACTORS         = NOT_ESTABLISHED

HETEROGENEOUS_RESPONSE_PROFILE = YES
GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
MIXED_GENERATION_MECHANISMS    = NOT_ESTABLISHED
SHARED_CAUSAL_MECHANISM        = NOT_ESTABLISHED

SECONDARY_CHUNK_TO_DOCUMENT_AGGREGATION   = NOT_TESTED
GROUPING_RESIDUAL_EVIDENCE                = SUPPORTED
ADDITIONAL_GROUPING_INTERVENTION_REQUIRED = YES
```

`V4_8_PROTOCOL_EXECUTION = PASS` 仅表示授权协议被正确执行、完整性 gate 通过；**不代表**机制已被隔离。

## AG.1 Diagnosis Closure Audit

### 协议完整性

```text
V4_8_RAW_EVIDENCE_REUSED = YES
NEW_MODEL_CALLS = 0 · NEW_COUNTERFACTUAL_RUNS = 0 · NEW_RETRIEVAL_RUNS = 0

V4_8_RAW_EVIDENCE_DIGEST_BEFORE = da57114b1acc737ddeadb0355598bc3962a18f0f4ba71ba28e4975e1b31af829
V4_8_RAW_EVIDENCE_DIGEST_AFTER  = 同上
RAW_EVIDENCE_CHANGED                = NO
MODEL_VISIBLE_REQUEST_DIGESTS_CHANGED = NO

V4_8_DERIVED_STATE_DIGEST_AFTER = e239ab48cbee2113cd72c66d0d84a8ab2b5a49e931a2ec3627a112ea2f7ce2bb
DERIVED_STATE_CHANGED           = YES（见下方逐项变更原因）
DERIVED_STATE_IDEMPOTENCE_DIGEST_RUN1 == RUN2
V4_8_CLASSIFICATION_GENERATOR_IDEMPOTENT = YES

PRIMARY_Y_CHANGED                  = NO
PER_CASE_CLASSIFICATION_CHANGED    = NO
AGGREGATE_CLASSIFICATION_CHANGED   = NO
RECOMPUTED_MATRIX_MATCHES_REPORTED  = YES
```

> 说明：numeric pre-closure derived digest 在一次中间幂等重跑中被覆盖（保护逻辑尚未加入），
> 因此 `V4_8_DERIVED_STATE_DIGEST_BEFORE = NOT_AVAILABLE_PRECLOSURE_DERIVED_DIGEST_OVERWRITTEN`；
> 审计轨迹由 `DERIVED_STATE_CHANGE_REASON` 逐项变更说明 + pre-change artifact file SHA-256
> `83e1ceae3779829de1c10abcfd35a58961864fd4678097654d43c03df248d402` 承载。

### Derived-state 变更原因（逐项）

```text
1  aggregate support enums 按 §21 冻结语义修正：M1/M2 SHARED_SUPPORT NOT_ESTABLISHED → PARTIAL；M4 → PARTIAL
2  M4 拆分为 M4_PHASE_LOCAL_SUPPORT / M4_GLOBAL_STATUS
3  M5_OTHER_GENERATION_FAMILY_MECHANISM → M5_RESIDUAL_OTHER_GENERATION_SUPPORT
   + SPECIFIC_M5_MECHANISM_IDENTITY = NOT_ESTABLISHED
4  MIXED_GENERATION_MECHANISMS: YES → NOT_ESTABLISHED；SHARED_CAUSAL_MECHANISM: NO → NOT_ESTABLISHED
5  新增 HETEROGENEOUS_RESPONSE_PROFILE = YES
6  MULTIPLE_SUFFICIENT_INTERVENTIONS 与 MULTIPLE_CONTRIBUTING_FACTORS 拆分为不同字段
7  interaction 记录为 SUBADDITIVE_BINARY_CEILING_COMPATIBLE，M3 = NOT_ESTABLISHED
8  additional grouping guidance 改为 §36 grouping-residual evidence audit
```

### Policy provenance（§11/§12/§14）

```text
PREDECLARED_POLICY_PROVENANCE_STATUS = PARTIAL
PRIMARY_CAUSAL_POLICY_PROVENANCE     = PARTIAL
SUPPORTING_POLICY_PROVENANCE         = PARTIAL
OUTCOME_DRIVEN_PROTOCOL_ADAPTATION   = NO

POST_RUN_TITLE_MATCHER_FIX = POLICY_BROADENING_THEN_REVERTED_TO_DECLARED_POLICY
    → primary Y 现按 predeclared policy 计算；broadening 仅作 sensitivity，12/12 cells 不变
POST_RUN_O7_FIX            = SUPPORTING_ONLY_IMPLEMENTATION_FIX（不影响 primary Y）
POST_RUN_O5_FIX            = IMPLEMENTATION_FIX_TO_FROZEN_POLICY（§34 为 predeclared 定义；无 cell 变化）

DERIVED_OUTPUT_ONLY_ERROR = YES
```

时间绑定证据：`factor_freeze_manifest`（由发出模型调用的同一进程写入）的 `frozen_protocol` 与当前常量**完全一致**，
且 `factor_freeze_digest` 与模型调用前 dry-run 的 digest 相同；授权文本中已冻结 A/B 定义、
C0–C3、M1 operationalization、§21 aggregate 语义、§26 interaction 规则、§28 M4 规则、§34 success 定义与 §37 contrasts。

## AH. Next Authorization Boundary

```text
NEXT_PHASE_NUMBERING_AUDIT = PASS（V4.8.1 未被占用；V4.9–V4.13 已由 roadmap 占用）
NEXT_DIAGNOSTIC_PHASE_NUMBER = V4.8.1

NEXT_DIAGNOSTIC_CANDIDATE = V4.8.1_RESIDUAL_GENERATION_MECHANISM_ISOLATION
PRIMARY_RESIDUAL_HYPOTHESIS = CHUNK_TO_DOCUMENT_AGGREGATION

NEXT_DIAGNOSTIC_EXECUTION_AUTHORIZED = NO
PRODUCT_REMEDIATION_AUTHORIZED       = NO

历史边界保持（本轮不升级）：
  HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO
  RELEVANT_PIPELINE_EQUIVALENCE      = NOT_ESTABLISHED
  HISTORICAL_FAILURE_COMPATIBILITY   = STRONGLY_SUPPORTED
  HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED
  禁止宣称 historical V4.6 pipeline equivalence proven / historical V4.6 generation mechanism
  mechanically proven / historical Document Identity attribution mechanically overturned

仅当另获授权才可设计 V4.8.1；本轮已 STOP，未设计、未执行任何第三/第四 factor 实验。
```

## AI. STOP

本轮结束即停止。未修改 production prompt / material header / build_messages / document grouping / retrieval /
ranking / citation logic；未修改 Golden / evaluator / citation semantics；未创建 product baseline；
未移动 baseline pointer；未运行 Full-144；未同步 Publish；未 commit / push / tag / release。

交付物：V4.8 diagnostic machine artifact、本报告、diagnostic harness、diagnostic tests、2×2 controlled
counterfactual evidence、deterministic request digests、factorial contrasts、per-case causal attribution、
shared-vs-mixed conclusion、secondary grouping assessment、pre/post integrity evidence、
candidate remediation authorization boundary。等待下一次明确授权。
