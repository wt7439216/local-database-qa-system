# V4.3 — Failure Attribution Rebuild

> 基于 V4.2 冻结的 canonical measurement system，对 V4 initial baseline 的失败 case 做逐例、可证据化、互斥优先的 root-cause attribution。
> **本阶段只诊断，不修复。** Gate = `FAILURE_ATTRIBUTION_INTEGRITY`，不是产品达标。

## 1. Canonical baseline（唯一测量事实源）

```text
case_exact  0.7083 (102/144)   fact_recall 0.8312 (261/314)
false_refusal 0.0208 (3/144)   citation_coverage 0.4893   high_conf 0.0095
invalid_citation 0 / scope_violation 0
```
artifact：`eval/v4_initial_baseline.json`；evaluator：`scripts/eval_v4_baseline.py`。

## 2. Attribution method

1. `scripts/analyze_v4_attribution.py` — 逐 case 机械导出 route / scope / 最终 context / 事实命中 / citation 重算 → `eval/v4_attribution_evidence.json`
2. `scripts/trace_v4_retrieval.py` — 对每个缺失事实判定证据是否存在于 SQLite、是否被 FTS 命中、是否进入最终 context → `eval/v4_retrieval_traces.json`
3. `scripts/decompose_v4_citation.py` — 2×2 citation 分解 → `eval/v4_citation_decomposition.json`
4. `scripts/build_v4_attribution.py` — 合并机械证据与逐例复核 → `eval/v4_failure_attribution.json`

**关键校验**：用当前 f2-v4 纯函数（`split_claims`）从答案文本重算 coverage，与 engine 存储报告逐例比较 → **117 个可比 case 的 |delta| max=0.0000**，证明 renumber 不影响 coverage，且重算忠实。

## 3. Canonical failure set（机械导出）

```text
answer-eligible        = 144
non-exact              = 42
structured refusals    = 3   (loc-018 / mt-006 / md-014)
failed facts           = 53
```

## 4. Aggregate root-cause distribution

| Primary cause | cases |
|---|---:|
| A GOLDEN_CONTRACT_ISSUE | 10 |
| B EVALUATOR_ISSUE | 9 |
| E RETRIEVAL_FAILURE | 7 |
| H GENERATION_SYNTHESIS_FAILURE | 5 |
| C ROUTING_FAILURE | 4 |
| D SCOPE_FAILURE | 3 |
| F DOCUMENT_IDENTITY_FAILURE | 2 |
| G HISTORY_CONTEXT_FAILURE | 2 |

| Classification | cases |
|---|---:|
| MEASUREMENT_FAILURE | 19 |
| MULTI_CAUSE | 9 |
| **PRODUCT_FAILURE** | **14** |

> 只有 `PRODUCT_FAILURE`（14）进入未来 product remediation backlog；`MEASUREMENT_FAILURE`（19）属尺子问题，单独授权处理。

## 5. Locate deep audit（12 失败 / 20）

| 类型 | cases | 说明 |
|---|---|---|
| Golden/Evaluator：`locate` 确定性模板只输出"位置"，golden 要求复述 query 概念词 | loc-003/004/005/011/012/019（6） | 证据已交付、章节正确；模板结构上不可能输出该词。**非产品缺陷** |
| Golden ordinal 表示不匹配（已证实） | loc-016（`第1` vs `1.`）、loc-017（`第2` vs `2.`）（2） | 语义内容在位，仅序号写法不同 |
| Retrieval ranking（top-3 章节错误） | loc-008、loc-013、loc-015（3） | 期望章节未进 top-3 context |
| Scope/OOS 误拒 | loc-018（1） | 证据已交付仍被 out_of_scope 拒绝 |

关键机制：locate 的通过与否取决于"概念词是否恰好出现在被返回的 section 标题里"——loc-001/002/006/007/009/010/014/020 因标题含该词而通过，其余失败。**这是 Golden/Evaluator 与确定性模板契约不对齐，不是定位能力缺陷。**

## 6. Retrieval miss audit

`trace_v4_retrieval.py` 对每个缺失事实给出判定。**绝大多数缺失事实的 term 判定为 `EVIDENCE_DELIVERED`**（材料已在最终 context 中交给模型）。

真正的检索缺口（`RRF_RANKING_MISS`）：
```text
qa-020 子载波 | qa-030 幅度/起伏 | cmp-001 GMSK | cit-013 200 | mt-009 类型 | md-004 教材 | md-009 教材 | loc-016 第1 | loc-017 第2 | loc-018 第3
```
章节级 miss：`qa-030`(期望2,得到1)、`loc-008`(期望3/5,得到1)、`loc-013`(期望1/6,得到3)、`loc-015`(期望4/5,得到1)。无 `EVIDENCE_ABSENT_FROM_SOURCE`（术语均可检索到）。

## 7. Document identity audit

- title **未进入 FTS**（`chunk_fts.search_text`=正文，`heading_text`=章节）；legacy 教材路径 embedding 输入也不含 title；citation/support 只读取 chunk text。
- 因此 `md-009`/`md-015` 的答案以"材料1/材料2/材料5"指代证据，**不复述文档名**，而 golden 要求文档身份 → 2 个 primary `DOCUMENT_IDENTITY_FAILURE`。
- `md-014`：`教材`/`测试文档` 这类非正式称谓无法解析为稳定身份，叠加 OOS gate 误拒（primary D）。
- `md-004`/`md-019`：被误路由到 locate（primary C）。

## 8. Multi-turn audit（19 eligible）

- 17/19 正确解析 referent（resolution=resolved）并回答正确。
- `mt-011`（primary G，proven）：改写输出语法破损 `CDMA的那` → 模型拒答。
- `mt-006`（primary D，secondary G）：referent 正确解析为 OFDM，但改写只剩裸词 `OFDM`（conf=low）→ OOS gate 误拒。
- `mt-003`（primary G，secondary A/H）：referent 正确解析为第2章，但答案被 history 话题带偏（讨论 OFDM），且未给出章号。
- 其余 `mt-007`/`mt-009` 归入 evaluator 复述问题。

## 9. Generation / completeness audit

仅在"scope 正确 + route 正确 + 证据已交付 + golden/evaluator 要求有效"判定为 generation：

```text
qa-040 (遗漏 OFDMA)                    PRODUCT
qa-036 / qa-039 (材料未直接回答类限答)   MEASUREMENT/MULTI
cmp-014 / cmp-019 (拒绝对比/遗漏维度)    MULTI
qa-032 (未陈述"正交")                   MULTI
```
无证据表明"prompt-only completeness"可行（Q4.1 已证 1/21，不予重试）。

## 10. Citation coverage decomposition（V4.3.1 修正：THREE-CELL PAIRED PATH）

> **V4.3 的 "2×2 decomposed" 表述已作废。** 仅有 3 个 cell 可用，故改称
> `THREE_CELL_PAIRED_PATH_DECOMPOSITION`；`VERIFIER × GENERATION INTERACTION = NOT_IDENTIFIED`。

**统一 case set（frozen INTERSECTION，n=116）** — 所有 cell 使用同一集合：

| Cell | 组合 | case-level |
|---|---|---:|
| A | 旧答案 + f2-v3（stored） | 0.5582 |
| B | 旧答案 + f2-v4（重算） | 0.4863 |
| C | 新答案 + f2-v4（重算） | 0.4911 |
| D | 新答案 + f2-v3 | **不可计算**（f2-v3 已退役；恢复其语义=恢复已退役行为） |

```text
VERIFIER_EFFECT_ON_OLD_ANSWERS          = -0.0719  （主导）
GENERATION_BATCH_EFFECT_UNDER_F2_V4     = +0.0048
PAIRED_PATH_TOTAL                       = -0.0671
VERIFIER x GENERATION INTERACTION       = NOT_IDENTIFIED
```

### 10.1 Case-set cardinality（机械导出，已消除 117/118 歧义）

```text
OLD_F2_V3_REPORT_CASES      = 144      OLD_F2_V3_COVERAGE_CASES = 118
NEW_F2_V4_REPORT_CASES      = 117      NEW_F2_V4_COVERAGE_CASES = 117
INTERSECTION                = 116      UNION = 119
OLD_ONLY = 2   NEW_ONLY = 1   NO_REPORT_NEW = 27   NO_REPORT_OLD = 0
```
集合算术全部通过：`144 = 117 + 27`（新报告分区）、`116 + 2 = 118`、`116 + 1 = 117`、`118 + 117 − 116 = 119`。

### 10.2 三个数值为何不同（0.4893 / 0.4911 / 0.5203）

三者是**同一 metric**，差异**仅来自 case set**，不是聚合方法差异：

| 数值 | 命名集合 | n | 聚合 |
|---|---|---:|---|
| **0.4893** | `CANONICAL_FULL_ELIGIBLE_REPORT_SET`（canonical gate） | 117 | engine stored report 的逐 case 均值 |
| **0.4911** | `PAIRED_COMMON_SET`（= INTERSECTION） | 116 | 配对集合上的重算均值 |
| 0.5203 | `ALL_ELIGIBLE_RECOMPUTED_ALTERNATE` | 144 | **诊断性替代语义**（对 27 个无报告确定性答案离线重跑 f2-v4） |

**method-invariance 已证明**：在 INTERSECTION 上 stored 均值 = recomputed 均值 = **0.4911（delta = 0.0）** →
renumber 与"存储 vs 重算"均无影响，数值差异纯粹由 case set 决定。

> `0.5203 = ALTERNATE_SEMANTIC_B`（离线重跑 f2-v4），**不是** Contract 指标，也**不是**"把无报告 case 当作 0 加入"。

**measurement gap**：engine 对确定性路由（`locate`/`locate_chapter`/`book_toc`）返回 `citation_report=None` →
**27/144 case 不进入 canonical coverage 均值**（含全部 locate）。

## 11. Regression floor 裁定（V4.3.1 保守化）

```text
Is the contract floor >=0.55 directly comparable to canonical 0.4893?
=> PARTIALLY
   - 分母定义可比（两者都排除无 citation report 的确定性路由）
   - verifier 语义不可比（f2-v3 vs f2-v4）
STATUS = LEGACY_REGRESSION_FLOOR_NOT_DIRECTLY_COMPARABLE

归因分量（frozen INTERSECTION, n=116）：
  verifier semantics on a fixed answer batch = -0.0719
  generation-batch under fixed f2-v4          = +0.0048
  case-set effect                             = 已通过冻结集合隔离
  unexplained / interaction                   = NOT_IDENTIFIED
```

**表述纪律**：由于 cell D 不可得、interaction 未识别，本轮**不使用** `NOT A PRODUCT REGRESSION`。
仅允许：

```text
NO_EVIDENCE_OF_A_NEGATIVE_GENERATION_REGRESSION
VERIFIER_EFFECT_DOMINATES_OBSERVED_PAIRED_DELTA
INTERACTION_NOT_IDENTIFIED
```

- 不自动降低 floor，不重新定义 floor，不据此宣布 regression 或无 regression。后续是否迁移 Contract floor 需单独授权。

## 12. Evaluator / Golden findings

```text
PROVEN EVALUATOR/GOLDEN DEFECT:
  qa-029 (信噪比 vs 信号功率与噪声功率谱密度之比)   [V3 已记录]
  qa-035 (错误 vs 差错)                             [V3 已记录]
  loc-016 / loc-017 (第1/第2 vs 1./2.)              [本轮机械证实]
  mt-003 (第二章 中文序号，答案用阿拉伯数字)
LIKELY:
  qa-002 (多址) / qa-006 (合并) / qa-031 (展宽) / cmp-004 (时分) / mt-009 (类型) / meta-013 (章节)
QUESTIONABLE GOLDEN REQUIREMENT:
  qa-036 (覆盖) / cmp-020 (码)
```
共 **19 case 属 MEASUREMENT_FAILURE**，**不得**通过修改 Golden/Evaluator 在本阶段处理。

## 13. Dependency graph

```text
document_identity ─┬─> scope_resolution ──> routing ──> retrieval_ranking ──> generation_synthesis ──> citation_alignment
                   └─> retrieval_ranking
query_rewrite ──> retrieval_ranking
golden_contract ──> evaluator_matcher        (旁路：改变"尺子"而非产品)
```
修复上游会自然改善下游：修 `document_identity` → md-009/015/004/014；修 `routing` → cit-001/007/md-004/md-019（format 连锁）；修 `scope` → loc-018/mt-006/md-014。

## 14. Remediation priority（证据排序，V4.3.1 修正）

### 14.1 MULTI_CAUSE backlog 修正（primary cause ≠ 是否需要 product work）

9 个 MULTI_CAUSE case **全部**含 product 分量：

| case | primary | product component | measurement component |
|---|---|---|---|
| qa-020 | RETRIEVAL | RETRIEVAL | EVALUATOR |
| qa-030 | RETRIEVAL | RETRIEVAL + GENERATION | — |
| cmp-001 | RETRIEVAL | RETRIEVAL + GENERATION | — |
| cit-013 | RETRIEVAL | RETRIEVAL | EVALUATOR |
| qa-032 | GENERATION | GENERATION | GOLDEN |
| qa-039 | GENERATION | GENERATION | GOLDEN |
| cmp-014 | GENERATION | GENERATION | EVALUATOR |
| cmp-019 | GENERATION | GENERATION | EVALUATOR |
| mt-003 | HISTORY | HISTORY | GOLDEN |

```text
PURE_PRODUCT_CASES                      = 14
PURE_MEASUREMENT_CASES                  = 19
MULTI_CAUSE_WITH_PRODUCT_COMPONENT      = 9
MULTI_CAUSE_WITHOUT_PRODUCT_COMPONENT   = 0
TOTAL_CASES_REQUIRING_EVENTUAL_PRODUCT_WORK = 23
```
> V4.3 的 "only 14 enter product backlog" 不完整：**23** 个 case 最终需要 product work。

### 14.2 Priority

```text
Priority 1  D SCOPE/OOS 误拒         3 cases / 7 facts   （上游 gate + 贴近 false_refusal 安全线）
Priority 2  C ROUTING 过触发          4 cases / 7 facts   （确定性、低复杂度）
Priority 3  F DOCUMENT IDENTITY       2 cases / 3 facts   （上游，联动 4 case）
Separate    A/B GOLDEN+EVALUATOR     19 cases             （改尺子，需单独授权，禁止刷分）
Subsequent  E RETRIEVAL(7) -> G HISTORY(2) -> H GENERATION(5)
Deferred    I CITATION scale-up       （先解决 floor 可比性）
Rejected    prompt-only patch / 降 Gate / 模糊 matcher / L2 / reranker
```

**V4.4 priority 重验证 = YES**（Scope/OOS 仍为 Priority 1）：false refusal 在依赖链最上游（直接阻断
retrieval→generation→citation）；是唯一产生"对 in-scope 问题错误拒答"的桶；且贴近 `false_refusal ≤ 0.03`
安全线；MULTI_CAUSE 修正只提高总工作量，不改变排序。

## 14.3 Scope 三 case 残差图（V4.3.1）

| case | failed facts | primary blocker | secondary | scope-only 可修 | scope-only 不可修 |
|---|---|---|---|---|---|
| loc-018 | 参数, 第3（2） | OOS gate 误拒 | locate ranking / ordinal | 取消错误拒答 | `第3` 序号表示；`参数` 仍受 ranking 影响 |
| mt-006 | OFDM（1） | OOS gate 误拒 | query rewrite 只剩裸词 | 取消错误拒答 | 改写仍欠定（conf=low），完整性有风险 |
| md-014 | GSM, WCDMA, CDMA, LTE（4） | OOS gate 误拒 | document identity / 跨文档综合 | 取消错误拒答 | 跨文档 synthesis 仍需 generation |

```text
facts_blocked_total = 7   （V4.3 记 8，已更正）
```
> 因此 **不得**把 "3 cases / 7 facts" 解释为 Scope phase 可恢复全部 7 facts。

未来 V4.4 Objective：
```text
remove proven false OOS refusals without weakening legitimate OOS protection
（不是 "recover all failed facts in the three cases"）
```

**建议 V4.4 gate（本阶段不实施）**：targeted false-OOS case 不再 out_of_scope；`oos_hard_negative` false_accept_rate = 0（29 例）；
Phase E 108/108；`false_refusal_rate ≤ 0.03` 且无新增误拒；scope leakage = 0；既有 scope/security 测试 PASS。
**仅 3 个目标 case PASS 不构成 gate。**

## 15. No implementation

本阶段**未修改**任何 production / evaluator / Golden / Contract / schema。所有结论以
`PROPOSED_FIX_DIRECTION` 形式记录，未提交任何 patch。
