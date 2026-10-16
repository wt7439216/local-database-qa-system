# KB-V4 — V4.7 Document Identity Root-Cause Confirmation
## + V4.7 Diagnosis Closure & Report Correction

> 本文件是 **V4.7 diagnosis closure** 的最终冻结版本。
> 阶段一：`V4.7 — Document Identity Root-Cause Confirmation`（READ-ONLY diagnosis）。
> 阶段二：`V4.7 — Diagnosis Closure & Report Correction`（本轮；NOT a product / remediation / measurement / baseline / publication phase）。
> 模式：`READ_ONLY PRODUCT DIAGNOSIS` + `DIAGNOSIS-CLOSURE / REPORT-CORRECTION ONLY`
>
> 机器事实源：`eval/v4_7_document_identity_root_cause.json`
> 工具：`scripts/analyze_v4_7_document_identity.py` · 测试：`tests/test_v4_7_document_identity_diagnosis.py`（48 tests）
>
> 本报告按**四条互相独立的轴**组织：
>
> ```text
> 1. Current pipeline scientific finding
> 2. Product root-cause family / mechanism
> 3. Historical compatibility / equivalence
> 4. Measurement semantic side issue
> ```
>
> ```text
> V4_7_DIAGNOSIS_CLOSURE                         = PASS
> V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE_CONFIRMATION = PASS
> V4_7_ENVIRONMENT_EQUIVALENCE                   = PASS
> CURRENT_PIPELINE_ROOT_CAUSE                    = GENERATION
> CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS        = DISPROVEN
> DOCUMENT_IDENTITY_ROOT_CAUSE                   = NOT_PROVEN
> DOCUMENT_IDENTITY_MECHANISM_APPLICABLE         = NO
> FIRST_IDENTITY_LOSS_LAYER                      = NONE
> CURRENT_BASELINE                               = V4_6_2_HASH_PORTABILITY_BASELINE
> PRODUCTION_BEHAVIOR_CHANGED                    = NO
> ```

---

## A. Scope / Boundary

```text
MODE = DIAGNOSIS-CLOSURE / REPORT-CORRECTION ONLY
NOT a product phase · NOT a remediation phase · NOT a measurement remediation phase
NOT a new baseline phase · NOT a publication phase
```

授权可写范围（实际 changed paths 见 §R）：

```text
eval/v4_7_document_identity_root_cause.json
docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md
scripts/analyze_v4_7_document_identity.py
tests/test_v4_7_document_identity_diagnosis.py
```

未触碰：`core/` `desktop/` `web/`（未做任何 prompt / build_messages / material-header / document-grouping / retrieval / ranking / citation / generation 修改）；
V3 workspace `FROZEN / READ-ONLY / UNTOUCHED`；Publish workspace `READ-ONLY`（仅用只读 git plumbing 做 anchor 审计，未 sync / write / commit / push / tag / release）；
未创建任何 `V4_7_*_BASELINE`；current pointer 保持 `V4_6_2_HASH_PORTABILITY_BASELINE`。

本轮的 correction 原则：

```text
derived-output-only error          -> 只改 JSON / Markdown
generator-logic error              -> 同步修 script + tests
禁止只手工篡改输出 artifact 而让 generator 再次执行时恢复错误结论
```

以下结论由 script 自动产生、因此**必须**同时修 script（不是只改 JSON）：

```text
RELEVANT_PIPELINE_EQUIVALENCE = PROVEN_EQUIVALENT
MIXED_ROOT_CAUSES / SINGLE_MECHANISM taxonomy
historical "机械推翻" over-claim
Product root-cause 与 Measurement issue 混轨
```

## B. Pre-correction Integrity Snapshot

本工作区非 git repository，故写入前建立只读 byte-exact 快照（`Get-FileHash -Algorithm SHA256` + canonical production hash）。

**Production（写入前）**

```text
canonical production hash = 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
core                       = ce33e5504bebc1a3941ce381c77baad1716acd845f5e80b97c3f515016a78db0
desktop                    = 22173f277d0b3ac1fbc6935c24e2f217e2f5df196e43ba4dd8ca5e392b1120a2
web                        = 7283dfb676ce5355f6911cf3fdf7790722a97a95479986cf815311161057bbaf
```

**4 个允许文件（写入前）**

```text
689c2920f2c63242bab6d23750ee1d732f796e906891bf0fe68cc17fb7d66cda  eval/v4_7_document_identity_root_cause.json
a3a7d8c77d092fc8bc4bb5e558c9834d8aabdf2ee32549f528c337a2ea521015  docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md
5880c61c7d1133d89b0f5838614cddd6f91e0f4a8f241e3ec06598e1f24407f8  scripts/analyze_v4_7_document_identity.py
944d33ea3e139d2841632ce255532bea4e86384ddf1c47747bc4521dfb2d667a  tests/test_v4_7_document_identity_diagnosis.py
```

**Frozen 文件（写入前）**

```text
5a644a3fe9a9b280ff095493627844cea745f44d06d2c2f249feb6c4e444a5f8  eval/v4_6_post_routing_attribution.json
fbac1e51ca621d93c04a66db396fde1cbeffa7237e3034fb3b1b2c4a777f703a  docs/V4_POST_ROUTING_ATTRIBUTION.md
414e5a711d6bfbf0825469e09e6c9c31d52ca66dc2e0df7cabe719e6dc99ed95  eval/v4_6_2_hash_portability_baseline.json
2c7b9d0beca0af94bc80496874e95ac4a9ad7d613843bf70da7c3e8ec5a94ddb  eval/v4_6_1_embedding_identity_baseline.json
18ca7ccb445d46c2b38fd711d07e4f59e0d515d2992b9bce948b854df27ac54c  eval/v4_baseline_lineage.json
31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb  eval/v3_final_golden.json
01703cc36cea612060bd970957212dadbb963626c7420fbfaa16717184bb9926  docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md
0caf048c598aa80724d2ea1e5af96725811ab02e2c69a732607a95d7a7f6e1a8  docs/INDEX.md
8c2d70f53ad633712378decdbc42e4454c783b70b08070138ff78e1be86af775  README.md
f2ac450afacfd576dbc5e841f7bc8b587324dcd93d483dfe3176cc3d9a2ec77c  docs/V4_RELEASE_SNAPSHOT.md
80e62ae17c2e6b2893ee8a93d5cb8da92971596928371a1a610592a132dc457f  CHANGELOG.md
```

> `eval/v3_final_golden.json` 的 31a685… 正是 lineage 记录的历史 raw golden hash，说明 Golden 自 V4.6.1 起未被改动。

## C. Evidence Reused

**未重跑任何模型。** 本轮 closure 采用 `--from-existing` 模式：从既有 artifact 中抽取 **raw/observed evidence subset**，只重算 derived 层。

```text
python -X utf8 scripts/analyze_v4_7_document_identity.py --from-existing \
    --out eval/v4_7_document_identity_root_cause.json
```

复用的 raw evidence：

```text
captured application-level messages（system + user，含 material headers）
raw model answers（md-004 / md-009 / md-015）
retrieval candidate / final ranked / PreparedAnswer / sent_context traces
material -> chunk -> document mapping
title-visibility observations
evidence-continuity observations
counterfactual evaluator outputs（_build_row 复用）
runtime-library identity + production-hash evidence
historical answer caches（4 个 production-hash-bound cache）
V4.6 attribution / evidence 摘录
```

未新增 `script` 之外的 raw 证据，故不存在“新 replay 覆盖原始 captured evidence”的问题。

`WHY_RERUN_WAS_REQUIRED`：**N/A**（所有 closure 判断均可由既有 artifact 得出，无需 target-case replay）。

## D. Raw Evidence Preservation

machine artifact 明确区分：

```text
immutable observed evidence      -> RAW_EVIDENCE_KEYS（14 个顶层键 + pipeline observation 子块）
corrected derived interpretation -> layer_matrix / per_case_product_root_cause / taxonomy / gates
```

digest 规则（§9）：

```text
只抽取 raw/observed semantic subset（不含 derived field）
-> canonical JSON（UTF-8、sorted keys、compact separators、稳定数组顺序）
-> sha256
```

结果：

```text
RAW_EVIDENCE_DIGEST_BEFORE = 22fe4b4650d85b9a38cda07b2884a690a24d40073ce469daa4ac457c1473c969
RAW_EVIDENCE_DIGEST_AFTER  = 22fe4b4650d85b9a38cda07b2884a690a24d40073ce469daa4ac457c1473c969

RAW_EVIDENCE_PRESERVATION = VERIFIED_BY_SEMANTIC_DIGEST
```

即：raw evidence 未被本轮 closure 改动；被改写的只有 interpreted/derived 字段。

> 说明：`historical_pipeline_equivalence` 同时含观测量与派生的 grade，因此只有其 observational 子键
> （`region_comparisons` / `function_level_diff_v3_to_current` / `relevant_symbols` / `context_selection_symbols` / …）
> 属于 raw subset；`RELEVANT_PIPELINE_EQUIVALENCE`、`basis` 属于 derived，本轮被修正。

## E. Corrections Applied

| # | 上一轮结论（错误/过强） | 本轮修正 | 性质 |
|---|---|---|---|
| E1 | 报告称 V4.6 attribution 被**机械推翻** | `HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED`；禁止 `mechanically overturned / 机械推翻 / exact historical request / mechanically confirmed historical` 表述 | 措辞 + generator |
| E2 | `RELEVANT_PIPELINE_EQUIVALENCE = PROVEN_EQUIVALENT`（无 anchor 即判定等价） | 引入 `HISTORICAL_SOURCE_ANCHOR` gate；无 anchor ⇒ `NOT_ESTABLISHED`；字节级观察降级为 `supporting_observation_only_grade`（non-binding） | generator 逻辑 |
| E3 | 单一 `MIXED_ROOT_CAUSES = YES / SINGLE_MECHANISM = NO` 同时承载产品与测量 | 拆为 **Product 轴**（`product_root_cause_family_shared` / `shared_product_root_cause_family` / `mixed_product_root_cause_families` / `shared_generation_mechanism` / `mixed_product_mechanisms`）与 **Measurement 轴**（`measurement_semantic_issue` / `per_case_measurement_issue`）；废止旧字段 | taxonomy |
| E4 | `subcause = [MATERIAL_INDEX_BIAS, PROMPT_FRAMING, CHUNK_TO_DOCUMENT_AGGREGATION]`（三机制并列为“主因”） | 每例独立派生 `primary_mechanism` 与 `secondary_mechanisms`（`derive_case_generation_mechanism`） | generator 逻辑 |
| E5 | Document Identity 用 `SINGLE_MECHANISM = NO` 表达 | `DOCUMENT_IDENTITY_MECHANISM_APPLICABLE = NO`，`DOCUMENT_IDENTITY_SINGLE_MECHANISM = NOT_APPLICABLE`（避免“identity bug 存在但机制不统一”的误读） | taxonomy |
| E6 | 缺少 current/historical 的显式区分字段 | 新增 `current_pipeline_document_identity_loss = DISPROVEN`、`historical_source_anchor_available`、`historical_v4_6_document_identity_attribution` | 字段 |
| E7 | 缺少 raw evidence 保全证明 | 新增 `raw_evidence_preservation`（BEFORE/AFTER digest） | 字段 + generator |
| E8 | 缺少 closure gates | 新增 `closure_gate_results`（C1–C37） | 字段 |
| E9 | script 硬编码 `grade = PROVEN_EQUIVALENT`、`mixed = len(signatures) > 1`、`single_mechanism = NO` | 上述逻辑已从 script 中移除/替换（见 §A 规则） | generator 逻辑 |

**Evidence Preservation Invariant 检查**：E1–E9 全部落在 derived 层；raw evidence digest 在改动前后一致（§D）。

## F. Historical Source Anchor Audit

`HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO`

审计方法（全部只读）：

```text
method = git ls-tree + cat-file --batch -> canonical production_source_hash per ref
         compared against the recorded historical production hashes
```

只在以下情况才允许作为 exact anchor（§13）：exact historical Git commit / immutable historical source snapshot / equivalent immutable source artifact，且必须与 V4.5/V4.6 的 production provenance **机械绑定**。

| 候选方法 | 结果 |
|---|---|
| active V4 workspace git | **不可用**（无 `.git`） |
| Publish workspace git（read-only plumbing） | 可用，但 **不构成 anchor**（见下） |
| local immutable snapshot（V3 frozen / Publish） | **不可用**：无 provenance 绑定到 `c36d61a1` / `7216c885` |
| production-hash-only | **不充分**：hash 只标识状态，不提供可比较的源码树 |

Publish git 逐 ref 审计结果：

```text
v3-final          -> canonical production hash 15c29f810cf91a85f9d3f214daefda8a9fb7dc7f0b0ca215a764288c976c9fa4
v4.0.0-alpha.1    -> 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
v4.0.0-alpha.2    -> 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
HEAD (1efc74f)    -> 108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
```

结论：

1. 绑定方法**本身有效**——HEAD / alpha.2 精确复现 canonical production hash `108fb167…`，即 git tree ↔ 当前 production provenance 是可机械绑定的。
2. 但**没有任何 ref 复现 V4.5（`c36d61a1…`）或 V4.6.1（`7216c885…`）**。published history 中不存在 V4.4/V4.5/V4.6 开发态的 commit（`v4.0.0-alpha.1` 的 tree 已经是 V4.6.2 代码）。
3. 额外的机械障碍：published git tree 以 **LF** 存储，而 V4.2–V4.6.1 的 provenance hash 是 **RAW CRLF worktree hash**，二者按设计不可互推；且历史 canonical hash 未被记录，故即使存在 LF commit 也无从比对。

```text
anchor_type        = NONE
anchor_identity    = null
comparison_result  = no ref reproduces the V4.5 / V4.6.1 provenance hash
```

本判定**不得**降格用 current V3 / current Publish 替代（§14）。

## G. Historical Pipeline Equivalence

```text
RELEVANT_PIPELINE_EQUIVALENCE = NOT_ESTABLISHED
```

因为 `HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO`。以下观察被保留，但明确标记为 **supporting / non-binding**：

```text
supporting_observation_only_grade = PROVEN_EQUIVALENT
supporting_observation_is_binding  = false
```

支撑观察（不构成等价性证明）：

```text
ChunkRecord.location   sha16 6a3ee45d4c819195  == v3 == publish
build_messages         sha16 8c038d542c500e7d  == v3 == publish
normalize_citations    sha16 36df5fe88e3c7cd5  == v3 == publish
renumber_citations     sha16 a5fd1b0872f30b70  == v3 == publish
hybrid_retriever._fuse sha16 dbfbab59039628ae  == v3 == publish
ollama_http chat       sha16 7dc702acfc7d7c69  == v3 == publish

function-level diff (V3 inheritance base -> current):
  core/engine_v2.py        changed = [StructuredQAEngine]
  core/library_store.py    changed = [EmbeddingIdentityError, _gates_for_model, _normalize_model_name,
                                      embedding_profile, validate_embedding_identity]
  core/hybrid_retriever.py changed = [HybridRetriever]
  core/ollama_http.py      changed = []
```

为什么这仍然不够（§15 明列不足的情形）：`current V3 == current V4`、`current V4 == current Publish`、`phase prose says production unchanged`、`current AST appears unchanged`、`production hash alone without the corresponding historical source tree` —— **均不足以**证明 `PROVEN_EQUIVALENT`。因此 graded `NOT_ESTABLISHED`。

## H. Current Pipeline Root Cause

> **轴 1：Current pipeline scientific finding（机械确认）**

```text
V4_7_CURRENT_PIPELINE_FINDING = MECHANICALLY_CONFIRMED

CURRENT_PIPELINE_ROOT_CAUSE              = GENERATION
CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS  = DISPROVEN
DOCUMENT_IDENTITY_ROOT_CAUSE             = NOT_PROVEN
DOCUMENT_IDENTITY_MECHANISM_APPLICABLE   = NO
FIRST_IDENTITY_LOSS_LAYER                = NONE
POST_PROCESSING_CAUSE                    = EXCLUDED

APPLICATION_REQUEST_TITLE_VISIBILITY = YES_FOR_ALL_TARGETS
EVIDENCE_CONTINUITY                  = PRESERVED_FOR_ALL_TARGETS
```

Layer matrix（三例一致，canonical title 一路可见直至 application-level request）：

```text
Layer                              md-004   md-009   md-015
----------------------------------------------------------
DB canonical title                 YES      YES      YES
ChunkRecord document_title         YES      YES      YES
retrieval candidate title          YES      YES      YES
final ranked context title         YES      YES      YES
PreparedAnswer title               YES      YES      YES
sent_context title                 YES      YES      YES
serialized material header title   YES      YES      YES
application request title          YES      YES      YES
raw answer title                   NO       NO       NO
final answer title                 NO       NO       NO
raw answer uses 材料N              YES      YES      YES
final answer uses 材料N            YES      YES      YES
```

每例最小证据（完整 trace 见 artifact `per_case_layer_trace[*]`）：

```text
md-004  材料1/2/3｜移动通信测试文档…  材料4/5｜移动通信 (李兆玉)…
        raw = 分集接收在材料1、材料2和材料3中被提及。[1][2][3]
md-009  材料1..4｜移动通信 (李兆玉)…  材料5｜移动通信测试文档…
        raw = 材料1、材料2和材料5都提到了RAKE接收机。[1][2][5] -> final [1][2][3]（仅 renumber）
md-015  材料1/2｜移动通信 (李兆玉)…  材料3/4/5｜移动通信测试文档…
        raw = 材料1、2明确了OFDMA与LTE的关系[1][2]…
```

关键机制事实：

```text
MATERIAL_INDEX_SEMANTICS = CHUNK_CONTEXT_INDEX
    for index, chunk in enumerate(contexts, 1): header = f"[材料{index}｜{chunk.location}]"

CHUNK_TO_DOCUMENT_GROUPING = IMPLICIT
    md-004: 5 materials -> 5 chunks -> 4 documents
    md-009: 5 materials -> 5 chunks -> 2 documents
    md-015: 5 materials -> 5 chunks -> 4 documents
    无显式 document grouping block；header 不含 document_id
```

## I. Per-case Product Root Causes

> **轴 2：Product root-cause family / mechanism**

每例由 `derive_case_generation_mechanism()` 从**该例自身证据**独立派生（非先定 aggregate 再复制）：

| case | family | primary_mechanism | secondary_mechanisms | confidence |
|---|---|---|---|---|
| md-004 | GENERATION | MATERIAL_INDEX_BIAS | PROMPT_FRAMING, CHUNK_TO_DOCUMENT_AGGREGATION | HIGH |
| md-009 | GENERATION | MATERIAL_INDEX_BIAS | PROMPT_FRAMING, CHUNK_TO_DOCUMENT_AGGREGATION | HIGH |
| md-015 | GENERATION | MATERIAL_INDEX_BIAS | PROMPT_FRAMING, CHUNK_TO_DOCUMENT_AGGREGATION | HIGH |

共同 supporting evidence（三例逐项一致）：

```text
application_request_title_visible           = true
evidence_continuity                         = PRESERVED
material_index_semantics                    = CHUNK_CONTEXT_INDEX
raw_answer_uses_material_index              = true
raw_answer_contains_canonical_title         = false
prompt_material_index_bias                  = true
prompt_document_title_instruction_present   = false
aggregation_demand (chunks > documents)      = true
chunk_to_document_grouping_implicit         = true
sent_context_headers_carry_document_title   = true
post_processing_changed_identity            = false
```

机制判读：模型回答**用 material index（chunk 级）指代文档**，prompt 强制以「材料编号」为指定引用形式且从未要求按文档标题作答，chunk→document 归并只能由模型自行完成 ⇒ `MATERIAL_INDEX_BIAS` 为直接观测到的 primary，`PROMPT_FRAMING` 与 `CHUNK_TO_DOCUMENT_AGGREGATION` 为 supporting。

> `GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED`：三个共现机制无法由只读诊断分离出“谁主导”；下一阶段必须先做窄范围 mechanism confirmation，再谈修复。

## J. Shared Product Family

```text
PRODUCT_ROOT_CAUSE_FAMILY_SHARED  = YES
SHARED_PRODUCT_ROOT_CAUSE_FAMILY  = GENERATION
MIXED_PRODUCT_ROOT_CAUSE_FAMILIES = NO
```

**Measurement issue 不参与也不改变该判定**（见 §N / §M）。

## K. Per-case Generation Mechanisms

| case | primary | secondary | mechanism_signature |
|---|---|---|---|
| md-004 | MATERIAL_INDEX_BIAS | PROMPT_FRAMING, CHUNK_TO_DOCUMENT_AGGREGATION | [MATERIAL_INDEX_BIAS, CHUNK_TO_DOCUMENT_AGGREGATION, PROMPT_FRAMING] |
| md-009 | MATERIAL_INDEX_BIAS | PROMPT_FRAMING, CHUNK_TO_DOCUMENT_AGGREGATION | 同上 |
| md-015 | MATERIAL_INDEX_BIAS | PROMPT_FRAMING, CHUNK_TO_DOCUMENT_AGGREGATION | 同上 |

taxonomy（§21）：

```text
MATERIAL_INDEX_BIAS · PROMPT_FRAMING · CHUNK_TO_DOCUMENT_AGGREGATION
· PURE_GENERATION_SYNTHESIS · OTHER_GENERATION_FAMILY
```

每例 `observed` 块（title 可见性、材料索引使用、prompt bias、聚合需求、分组方式、counterfactual 结果）均写入 artifact `per_case_generation_mechanisms[*].observed`。
当某例不同时使用 material-index 措辞时，派生逻辑会改为 `PURE_GENERATION_SYNTHESIS`（测试 T2 以合成输入验证该独立性）。

## L. Shared Generation Mechanism

```text
SHARED_GENERATION_MECHANISM = YES
MIXED_PRODUCT_MECHANISMS    = NO
```

三例**机械支持全部**下列条件（§22）：title visible + evidence continuity preserved + `材料N` 是 chunk/context index + 多个 chunk 映射到更少 document + document grouping 仅 implicit + prompt 强强调 material/citation indexing + raw answer 遵循 `材料N` 而非 canonical document identity。

```text
shared_generation_mechanism_name = MATERIAL_INDEX_REPRESENTATION_BIAS
```

> 注意：`SHARED PRODUCT FAMILY = GENERATION` **不自动**推出 `SHARED GENERATION MECHANISM = YES`；本轮两者分别独立判定（测试 T2 覆盖）。
> 反之，`SHARED_GENERATION_MECHANISM` 与 `MIXED_PRODUCT_MECHANISMS` 之间由 `handshake_mechanism_fields()` 强制一致（YES↔NO、NO↔YES、NOT_ESTABLISHED↔NOT_ESTABLISHED，测试 T9）。

## M. Mixed-vs-Shared Product Decision

```text
PRODUCT_ROOT_CAUSE_FAMILY_SHARED      = YES
SHARED_PRODUCT_ROOT_CAUSE_FAMILY      = GENERATION
MIXED_PRODUCT_ROOT_CAUSE_FAMILIES     = NO

SHARED_GENERATION_MECHANISM           = YES
MIXED_PRODUCT_MECHANISMS              = NO
```

上一轮的 `MIXED_ROOT_CAUSES = YES` 之所以出现，是因为它把 **Measurement 语义问题**与 **Product 机制**混在同一字段中。分开之后：

```text
Product 轴的 mixed 判定 = NO（3/3 同 family、同 mechanism signature）
Measurement 轴的差异（md-004/md-009 SUPPORTED vs md-015 NOT_OBSERVED）不构成 product mixed
```

## N. Measurement Side Issues

> **轴 4：Measurement semantic side issue（独立于 Product）**

```text
MEASUREMENT_SEMANTIC_ISSUE = SUPPORTED

per_case_measurement_issue:
  md-004 = SUPPORTED
  md-009 = SUPPORTED
  md-015 = NOT_OBSERVED
```

判据：`canonical_title_only` 反事实答案在 frozen matcher 下的表现（§O）。md-004 / md-009 的 Golden 事实含角色词 `教材`，任何 canonical title 都不含该子串；md-015 只需 `测试文档`（是 `移动通信测试文档` 的子串）故不受影响。

**本轮不修改 Golden / expected facts / alias / matcher / evaluator / metric 语义（§27）。**

## O. Counterfactual Evaluator Interpretation

canonical document title 与 Golden semantic-role token **不是同一种 representation**：

```text
canonical title       = 移动通信 (李兆玉)
Golden expected fact  = 教材            （角色词，非 canonical title）
canonical title       = 移动通信测试文档
Golden expected fact  = 测试文档        （子串命中）
```

复用 canonical matcher（`eval_v4_baseline._build_row`，字面子串 `f in answer`）的只读 probe：

```text
variant A（只用 canonical title）
  md-004  "分集 在《移动通信 (李兆玉)》与《移动通信测试文档》中均有提及。"
          -> 2/3  missing=[教材]          PARTIAL
  md-009  "RAKE 在《移动通信 (李兆玉)》与《移动通信测试文档》中均有提及。"
          -> 2/3  missing=[教材]          PARTIAL
  md-015  "OFDMA、LTE 在《移动通信测试文档》中均有提及。"
          -> 3/3                          YES

variant B（角色词 + canonical title，md-014 风格）
  md-004 / md-009 / md-015 -> 3/3        YES
```

结论：**correct canonical-title answer 仍可能无法获得 frozen literal matcher 的 full credit**。
因此 `Generation remediation track` 与 `Measurement semantic review track` 必须**独立**推进。

## P. Historical Failure Compatibility

```text
V4_7_ENVIRONMENT_EQUIVALENCE           = PASS
HISTORICAL_SOURCE_ANCHOR_AVAILABLE     = NO
RELEVANT_PIPELINE_EQUIVALENCE          = NOT_ESTABLISHED
historical_evidence_consistent         = YES

HISTORICAL_FAILURE_COMPATIBILITY       = STRONGLY_SUPPORTED
HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED
```

`historical_evidence_consistent` 由 script 机械计算，基于 metrics-source 相关 cache（production prefix `4b4e60b1` / `c36d61a1` / `7216c885`）：三例的历史答案均使用 `材料N` 且不含 canonical title，与当前机制一致。

**未使用 `CONFIRMED`**：CONFIRMED 至少要求 runtime/library equivalence + historical source anchor available + relevant pipeline mechanically equivalent + historical failure evidence consistent，本轮 anchor 缺失。

标准措辞（§34）：

> V4.7 已机械排除当前 V4.6.2 pipeline 的 Document Identity Loss。当前观测机制强烈支持将历史 V4.6 目标 case 的当前解释重新归向 Generation / Prompt-Evidence Framing，但尚未机械建立历史 pipeline 与当前 pipeline 的完全等价性。

**禁止表述**（已从 artifact / script / 本报告移除）：`V4.7 mechanically overturned historical V4.6`、`mechanical 推翻`、`exact historical request`、`mechanically confirmed historical mechanism`。

V4.6 历史 artifact **未被回写**：`eval/v4_6_post_routing_attribution.json`、`docs/V4_POST_ROUTING_ATTRIBUTION.md` 继续表示 V4.6 阶段当时的结论；V4.7 记录的是“后续证据挑战该解释”。

## Q. Corrected Machine State

```text
stage / mode                     V4.7 / READ_ONLY_PRODUCT_DIAGNOSIS
current_baseline                 V4_6_2_HASH_PORTABILITY_BASELINE
product_metrics_source           V4_6_1_EMBEDDING_IDENTITY_BASELINE
production_hash                  108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
environment_equivalence          PASS

current_pipeline_root_cause                     GENERATION
current_pipeline_document_identity_loss         DISPROVEN
document_identity_root_cause                    NOT_PROVEN
document_identity_mechanism_applicable          NO
document_identity_single_mechanism              NOT_APPLICABLE
first_identity_loss_layer                       NONE
application_request_title_visibility            YES_FOR_ALL_TARGETS
evidence_continuity                             PRESERVED_FOR_ALL_TARGETS
post_processing_cause                           EXCLUDED

per_case_product_root_cause                     (3 cases, §I)
product_root_cause_family_shared                YES
shared_product_root_cause_family                GENERATION
mixed_product_root_cause_families               NO
per_case_generation_mechanisms                  (3 cases, §K)
shared_generation_mechanism                     YES
shared_generation_mechanism_name                MATERIAL_INDEX_REPRESENTATION_BIAS
mixed_product_mechanisms                        NO
generation_mechanism_isolation                  NOT_ESTABLISHED

measurement_semantic_issue                      SUPPORTED
per_case_measurement_issue                      md-004 SUPPORTED / md-009 SUPPORTED / md-015 NOT_OBSERVED

historical_source_anchor_available              NO
historical_source_anchor                        anchor_type NONE
relevant_pipeline_equivalence                   NOT_ESTABLISHED
historical_failure_compatibility                STRONGLY_SUPPORTED
historical_v4_6_document_identity_attribution   STRONGLY_CHALLENGED

raw_evidence_preservation                       VERIFIED_BY_SEMANTIC_DIGEST
ready_for_document_identity_remediation         NO
generation_workstream_candidate                 SUPPORTED
generation_remediation_scope_ready              YES
measurement_review_candidate                    SUPPORTED
product_code_change_authorized                  NO
```

已从 artifact 中**移除**的旧字段：`single_mechanism`、`mixed_root_causes`、`mixed_root_causes_reason`、`per_case_conclusion[*].subcause`。

## R. Changed Files / Boundary Audit

实际 changed paths（**必须**是授权范围的子集）：

| path | before | after | in-scope |
|---|---|---|---|
| `scripts/analyze_v4_7_document_identity.py` | 5880c61c… | ae3c7b579c86342c32596d40c88a71666e657eaa61aaaa056bd294d6700640e1 | YES |
| `tests/test_v4_7_document_identity_diagnosis.py` | 944d33ea… | a92444fef2add9b322869903ca0fd9b7e6d397a86f977c3a71482947fbafbecb | YES |
| `eval/v4_7_document_identity_root_cause.json` | 689c2920… | effcbdfd18a93b2a52db813e1b19f88b4c65dbb7e9837206a82ebac0b9ee313d | YES |
| `docs/V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE.md` | a3a7d8c7… | 本轮重写（本文件，最终态） | YES |

```text
actual changed paths ⊆ authorized surface = YES
```

Frozen 文件（11 个）**全部 hash 不变**：

```text
5a644a3f…  eval/v4_6_post_routing_attribution.json          UNCHANGED
fbac1e51…  docs/V4_POST_ROUTING_ATTRIBUTION.md              UNCHANGED
414e5a71…  eval/v4_6_2_hash_portability_baseline.json       UNCHANGED
2c7b9d0b…  eval/v4_6_1_embedding_identity_baseline.json     UNCHANGED
18ca7ccb…  eval/v4_baseline_lineage.json                    UNCHANGED
31a68507…  eval/v3_final_golden.json                        UNCHANGED
01703cc3…  docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md       UNCHANGED
0caf048c…  docs/INDEX.md                                    UNCHANGED
8c2d70f5…  README.md                                        UNCHANGED
f2ac450a…  docs/V4_RELEASE_SNAPSHOT.md                      UNCHANGED
80e62ae1…  CHANGELOG.md                                     UNCHANGED
```

`STOP` 条件未触发：未发现授权范围外的文件变化。

## S. Regression / Hash Verification

```text
production hash（closure 开始）= 108fb167…798c
production hash（closure 结束）= 108fb167…798c        UNCHANGED
core = ce33e550…  desktop = 22173f27…  web = 7283dfb6…  UNCHANGED
runtime library identity = 10698752:c6bc9b3eb63ae4e6  UNCHANGED（== baseline == metrics source）
V3 workspace     FROZEN / READ-ONLY / UNTOUCHED
Publish workspace READ-ONLY（仅只读 git plumbing；未 sync/write/commit/push/tag/release）
未执行 Full-144 / 未重算 canonical metrics / 未建立新 baseline
未重跑 target-case 模型；新输出未覆盖原始 captured evidence
```

```powershell
python -m unittest tests.test_v4_7_document_identity_diagnosis -v   # 48 tests OK
python -m unittest tests.test_live_production_hash_guard -v         # 6 tests OK
python -m unittest tests.test_v4_6_2_hash_portability -v            # 15 tests OK
```

## T. Gate Results

**Diagnosis gates（G，沿用并保留）**：`gate_results` 全 PASS（G1–G51，其中 G39 更名为 “generation mechanism determined where applicable”）。

**Closure gates（C1–C37）**：`closure_gate_results` 全 PASS。

```text
C1  original V4.7 raw evidence preserved                  PASS（digest BEFORE == AFTER）
C2  current pipeline root cause remains Generation        PASS
C3  current-pipeline Document Identity loss DISPROVEN     PASS
C4  Document Identity remediation remains blocked         PASS
C5  historical overclaim removed                          PASS
C6  historical source anchor explicitly audited           PASS
C7  PROVEN_EQUIVALENT requires mechanically bound anchor  PASS
C8  without anchor: equivalence = NOT_ESTABLISHED         PASS
C9  historical compatibility independently graded         PASS
C10 Product and Measurement axes separated                PASS
C11 per-case Product family independently derived         PASS
C12 shared Product family explicitly decided              PASS
C13 per-case Generation mechanism independently derived    PASS
C14 shared Generation mechanism explicitly decided        PASS
C15 mixed Product family field consistent                 PASS
C16 mixed Product mechanism field consistent              PASS
C17 measurement issue does not create mixed Product attribution  PASS
C18 Document Identity mechanism = NOT_APPLICABLE          PASS
C19 counterfactual evidence preserved                     PASS
C20 V4.6 historical artifacts unchanged                   PASS
C21 Golden unchanged                                      PASS
C22 evaluator unchanged                                   PASS
C23 citation semantics unchanged                          PASS
C24 baseline lineage unchanged                            PASS
C25 production code unchanged                             PASS
C26 runtime DB unchanged                                  PASS
C27 no new baseline                                       PASS
C28 diagnosis tests PASS                                  PASS（48）
C29 live production hash guard PASS                       PASS
C30 hash portability tests PASS                           PASS
C31 production canonical hash unchanged                   PASS
C32 frozen-file hashes unchanged                          PASS（11/11）
C33 actual changed paths inside authorized surface        PASS
C34 V3 untouched                                          PASS
C35 Publish untouched                                     PASS
C36 no product remediation performed                      PASS
C37 no sync / commit / tag / push / release                PASS
```

## U. Final Decision

```text
V4_7_DIAGNOSIS_CLOSURE                         = PASS
V4_7_DOCUMENT_IDENTITY_ROOT_CAUSE_CONFIRMATION = PASS
V4_7_ENVIRONMENT_EQUIVALENCE                   = PASS

CURRENT_PIPELINE_ROOT_CAUSE              = GENERATION
CURRENT_PIPELINE_DOCUMENT_IDENTITY_LOSS  = DISPROVEN
DOCUMENT_IDENTITY_ROOT_CAUSE             = NOT_PROVEN
DOCUMENT_IDENTITY_MECHANISM_APPLICABLE   = NO
FIRST_IDENTITY_LOSS_LAYER                = NONE

APPLICATION_REQUEST_TITLE_VISIBILITY = YES_FOR_ALL_TARGETS
EVIDENCE_CONTINUITY                  = PRESERVED_FOR_ALL_TARGETS
POST_PROCESSING_CAUSE                = EXCLUDED

PRODUCT_ROOT_CAUSE_FAMILY_SHARED = YES
SHARED_PRODUCT_ROOT_CAUSE_FAMILY = GENERATION
MIXED_PRODUCT_ROOT_CAUSE_FAMILIES = NO

SHARED_GENERATION_MECHANISM  = YES
MIXED_PRODUCT_MECHANISMS     = NO

MEASUREMENT_SEMANTIC_ISSUE = SUPPORTED

HISTORICAL_SOURCE_ANCHOR_AVAILABLE = NO
RELEVANT_PIPELINE_EQUIVALENCE      = NOT_ESTABLISHED
HISTORICAL_FAILURE_COMPATIBILITY   = STRONGLY_SUPPORTED
HISTORICAL_V4_6_DOCUMENT_IDENTITY_ATTRIBUTION = STRONGLY_CHALLENGED

CURRENT_BASELINE            = V4_6_2_HASH_PORTABILITY_BASELINE
PRODUCTION_BEHAVIOR_CHANGED = NO
```

`V4_7_DIAGNOSIS_CLOSURE = PASS` 只代表 raw evidence + derived taxonomy + historical claim strength + machine artifact + human report + tests + governance boundary 已相互一致并可冻结。

它**绝不**代表：Generation remediation 已完成 / Measurement issue 已修复 / product metrics 有改善 / 建立了新 baseline / 达到 V4 Final。

## V. Recommended Next Authorization Boundary

```text
READY_FOR_MINIMAL_DOCUMENT_IDENTITY_REMEDIATION = NO
PRODUCT_CODE_CHANGE_AUTHORIZED                  = NO

GENERATION_WORKSTREAM_CANDIDATE    = SUPPORTED
    CANDIDATE_NEXT_PRODUCT_WORKSTREAM =
        Generation / Prompt-Evidence Framing for document-identity questions

GENERATION_REMEDIATION_SCOPE_READY = YES（因为 SHARED_GENERATION_MECHANISM = YES）
    窄范围候选（仍 NOT AUTHORIZED）：
        material-index bias
        chunk → document aggregation
        document-level evidence framing
        prompt framing
    注意：GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED
         ⇒ 下一阶段应**先**做窄范围 mechanism confirmation/design，再进入统一修复

MEASUREMENT_REVIEW_CANDIDATE       = SUPPORTED
    CANDIDATE_MEASUREMENT_WORKSTREAM =
        Golden / canonical-document-identity semantic alignment review
    （禁止并入下一 Product remediation；不得为提高分数修改 Golden）
```

建议的下一授权边界：

> 独立的 **Generation / Prompt-Evidence Framing** 窄范围机制确认与设计（document-identity 问题），
> 以及**独立**的 **Measurement semantic review**（Golden 角色词 vs canonical title 的表达语义）。
> 两者仍是 candidate，**本轮未授权任何实施**。

---

本阶段到此**停止**。禁止自动进入 Generation remediation / Prompt remediation / Document grouping remediation / Measurement remediation / Roadmap republish / Publish sync / GitHub publication。

未修改 `core/` `desktop/` `web/`；未修改 Golden / evaluator / citation semantics / runtime DB；未重建 library；未创建新 product baseline；未推进 baseline pointer；V3 未触碰；Publish 未写入；未执行 sync / commit / tag / push / release。
