# V4.2 — Evaluation Integrity & Baseline Reconciliation

> 本阶段目标只有一个：建立**唯一、可复现、可追溯**的 V4 产品质量测量基线，使后续 product change 可被可靠归因。
> **本阶段非产品质量优化阶段。** Gate 是 `MEASUREMENT_INTEGRITY = PASS`，不是 `PRODUCT_QUALITY_TARGETS = PASS`。

## 1. Canonical metric definitions（唯一权威口径）

> 生产者为 `scripts/eval_v4_baseline.py::compute_metrics`（唯一实现）。禁止任何脚本再以不同分母重算同名指标。

| Gate | numerator | denominator | eligible | exclusions |
|---|---|---|---|---|
| `case_exact_fact_match_rate` | count(is_answered AND fact_present==fact_total AND fact_total>0) | count(fact_total>0) | 144 answer-eligible | fact_total==0 |
| `fact_recall` | Σ fact_present | Σ fact_total | 144 | — |
| `false_refusal_rate` | count(answer_state==REFUSED) | 144 | 144 | ANSWER_WITH_LIMITATION 计为 answered |
| `citation_coverage` | Σ per-case coverage | count(case with factual_claim_count>0) | 144 | 无 factual claim 的 case |
| `high_confidence_unsupported_rate` | count(claim: UNSUPPORTED AND reason∈{unsupported_number_mismatch, unsupported_missing_key_term}) | Σ factual_claim_count | 144 | `unsupported_no_evidence`（coverage gap）与 `NOT_APPLICABLE`（非事实） |
| `invalid_citation_count` (hard) | Σ invalid_citation_count | n/a | 144 | — |
| `citation_scope_violation` (hard) | Σ citation_scope_violation | n/a | 144 | — |

- `citation_coverage`（gate）= **case-level average**；claim-level 另记为 `citation_coverage_claim_level`（诊断用，**非** gate）。
- 同名不同义已消除：历史 `false_refusal_rate` 在 `eval_v3_release.py` 曾按 in-scope 分母定义；本 canonical 口径为 **answer-level（/144）**。

## 2. Canonical commands（可复现来源）

```text
full run      : python scripts/eval_v4_baseline.py --library data/library/documents.sqlite3
report only   : python scripts/eval_v4_baseline.py --report-only
determinism   : python scripts/eval_v4_baseline.py --report-only     （连续两次；输出必须一致）
resume chunks : python scripts/eval_v4_baseline.py --limit N --max-seconds S
```

- 每个数字均可回答：which command / which dataset / which evaluator / which production state / which artifact。

## 3. Identity / provenance

```text
evaluator_version        = v4-baseline-v1
citation_verifier_version= f2-v4
answer_model             = qwen2.5:7b
library_identity         = 10698752:c6bc9b3eb63ae4e6  (data/library/documents.sqlite3)
golden file_sha256_16    = 31a68507456714c9   (post metadata-correction)
golden cases_sha256_16   = 0837e83333c858c6   (metadata-independent grading semantics)
golden historical file   = 6e18ee4ee9669bef   (pre metadata-correction)
production_source_sha256 = ceb4e1244cf9f265... (core/desktop/web)
answer_artifact_sha256   = 7da8547cd08c6144...
total 185 / answer-eligible 144 / expected-refusal 41
```

## 4. F. high_conf Metric Resolution（V4.2 重点 blocker）

**结论：`HIGH_CONF_METRIC_DEFINITION_RESOLVED`（非 BLOCKED）。**

- 冻结定义来自机器可读合同 `eval/v3_quality_acceptance.json` 与 `docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md §1.5`：
  `(number_mismatch + missing_key_term) / total_claims`，明确排除 `no_evidence`。
- 分母语义经合同算术唯一确定：`total_claims` = Σ factual_claim_count（= supported+unsupported+uncertain，排除 NOT_APPLICABLE）。
  - 复现：`(35+10)/554 = 0.0812`，`(36+10)/555 = 0.0829`（两个历史值均精确重算）。
- 该定义在 **f2-v3 cache** 上重算得 `9/559 = 0.0161`，**与历史文档记录的 Q3 值 0.0161 完全一致**
  → 定义恢复成功，且先前"无脚本产出"的缺陷已修复。

## 5. D. Historical Baseline Conflict Table（逐项裁定）

| metric | value | source | evaluator/verifier | status | reason |
|---|---:|---|---|---|---|
| case_exact | 0.6111 | contract v1.0 / V3 contract doc | f4.1-v1 / f2-v2 | **SUPERSEDED** | 裸 substring 拒答启发式误判 |
| case_exact | 0.7014 | v3_corrected_baseline / V3_FINAL_BASELINE | answer-eval-v2 / f2-v2 | **LEGACY** | Q1 修正 |
| case_exact | **0.7083** | **v4_initial_baseline** | v4-baseline-v1 / f2-v4 | **CANONICAL** | 本次 frozen run |
| fact_recall | 0.8248 | v3_corrected_baseline | answer-eval-v2 / f2-v2 | **LEGACY** | 259/314 |
| fact_recall | **0.8312** | **v4_initial_baseline** | v4-baseline-v1 / f2-v4 | **CANONICAL** | 261/314 |
| false_refusal | 0.0278 | 多处 | 多版本 | **LEGACY** | 4/144（含 Q4.2 前的 cmp-015） |
| false_refusal | **0.0208** | **v4_initial_baseline** | v4-baseline-v1 / f2-v4 | **CANONICAL** | 3/144 |
| coverage | 0.5534 | contract v1.0 | f4.1-v1 / f2-v2 | **SUPERSEDED** | — |
| coverage | 0.5524 | v3_corrected_baseline (case-level) | answer-eval-v2 / f2-v2 | **LEGACY** | — |
| coverage | 0.5558 | v3_final_answer_report avg | answer-eval-v4 / f2-v3 | **LEGACY** | Q3 rerun |
| coverage | 0.4577 | v3_corrected_baseline (claim-level) | answer-eval-v2 | **DIFFERENT_DENOMINATOR** | claim-level，非 gate |
| coverage | **0.4893** | **v4_initial_baseline** | v4-baseline-v1 / f2-v4 | **CANONICAL** | case-level |
| high_conf | 0.0812 | contract v1.0 | f4.1-v1 / f2-v2 | **SUPERSEDED** | 结构数字 false positive |
| high_conf | 0.0829 | v3_corrected_baseline | answer-eval-v2 / f2-v2 | **LEGACY** | 46/555 |
| high_conf | 0.0161 | docs/README | f2-v3 (Q3) | **LEGACY（V4.2 前不可复现；现可复现）** | 9/559 |
| high_conf | **0.0095** | **v4_initial_baseline** | v4-baseline-v1 / f2-v4 | **CANONICAL** | 5/525 |

**唯一 canonical 值 = `CANONICAL_V4_INITIAL_BASELINE`（见 §7 / `eval/v4_initial_baseline.json`）。**

### 冲突消解的关键证据
- 用**同一 canonical 度量代码**回算历史 cache（`data/eval_cache/answer_10698752_6e18ee4ee9669bef.json`）：
  - f2-v3 组 → case_exact 0.7014 / fact_recall 0.8217 / false_refusal 0.0278 / coverage 0.5558 / **high_conf 0.0161(9/559)**
  - f2-v2 组 → coverage 0.5533 / high_conf 0.0802
  → 度量代码与历史口径一致，差异来自 **verifier 版本 + 生成批次**。
- citation marker 数：新 run 527 vs 旧 run 526（≈相同）→ 生成体量稳定；
  `factual_claim_count` 差异（525 vs 559）主要来自 **verifier f2-v3→f2-v4 的 claim 切分/事实判定变化**，
  故 coverage 的差异**不是** product regression，而是**测量定义/verifier 版本 + 生成随机性**共同作用。
  （精确分解属 V4.3 Failure Attribution，本阶段只记录。）

## 6. Golden Integrity Audit（E）

| 项 | before | after | 方法 | 语义影响 |
|---|---|---|---|---|
| `meta.expected_totals.single_fact_qa` | 40 | 41 | `len(cases where category=='single_fact_qa')` | NONE |
| `meta.expected_totals.oos_hard_negative` | 30 | 29 | `len(cases where category=='oos_hard_negative')` | NONE |

- 原因：`oos-030` 已被重分类/改名为 `qa-041`，meta 未同步（`docs/V3_PHASE_F4_RELEASE_GATE.md` 亦记 41/29）。
- **未修改任何 case**（query / facts / refusal / route / eligibility 全部不变）。
- 修正后 meta 与实体机械统计完全一致（由 `tests/test_v4_evaluation_integrity.py` 锁定）。
- 因 metadata 修正，golden `file_sha256` 由 `6e18ee4ee9669bef` → `31a68507456714c9`；而 `cases_sha256`（grading 语义）**不变**，
  canonical 评测的答案缓存以 `cases_sha256` 绑定，故 metadata 修正不使答案失效。

## 7. Canonical V4 Initial Baseline（J）

```text
case_exact_fact_match_rate        = 0.7083   (102/144)      Target >=0.80  FAIL
fact_recall                       = 0.8312   (261/314)      Target >=0.90  FAIL
false_refusal_rate                = 0.0208   (3/144)        Target <=0.03  PASS
citation_coverage                 = 0.4893   (case-level)   Target >=0.80  FAIL
high_confidence_unsupported_rate  = 0.0095   (5/525)        Target <=0.05  PASS
invalid_citation_count            = 0        (hard)                        PASS
citation_scope_violation          = 0        (hard)                        PASS

2 / 5 quality PASS
Product Quality DoD = NOT_YET_PASS（本阶段不要求达标）
```

> **不可变性与 lineage（V4.4.1）**：`eval/v4_initial_baseline.json` 自 V4.4.1 起**永久**表示
> "任何 V4 remediation 之前的初始状态"，其数值不再随阶段推进而覆盖。后续阶段的测量写入**新的**
> stage baseline artifact，并由 `eval/v4_baseline_lineage.json` 维护父子关系与 current pointer。
> 详见 `docs/V4_INITIAL_BASELINE.md §5`。

## 8. Cache / Evaluator Provenance（G）

- **判定**：`data/eval_cache/answer_10698752_6e18ee4ee9669bef.json` 内含 4 组版本
  （空=26 / f2-v2=118 / answer-eval-v2=236 / answer-eval-v3=118 / **answer-eval-v4=144（verifier f2-v3）**）。
  **没有任何条目对应当前 verifier f2-v4** → 对 citation 指标而言整体 **STALE / NON-CANONICAL**。
  其 answer 层（case_exact/fact_recall/false_refusal）仍可作历史对照，但**不得**作为最终 canonical source，且不与其混用。
- 旧 cache 的缺陷：cache key 仅绑定 `evaluator_version`，**未绑定 citation verifier version** → verifier 升级不失效。
- V4.2 修复：canonical cache key 同时绑定 `evaluator_version` + `citation_verifier_version` + golden `cases_sha256` + library + model；
  文件名形如 `v4_baseline_{lib}_{goldencases}_{model}_{evalver}_{verver}.json`。
- canonical 答案产物：`data/eval_cache/v4_baseline_10698752_0837e83333c858c6_qwen2.5-7b_v4-baseline-v1_f2-v4.json`（runtime，gitignored）。

## 9. Reproducibility（H）

- **measurement layer = DETERMINISTIC**：`--report-only` 连续两次输出 **完全一致（Run1 == Run2）**。
- **generation layer = STOCHASTIC**：本地 Ollama `qwen2.5:7b`，chat API 未暴露固定 seed；两次独立 full run 的方差实测：
  - case_exact 0.7083 / 0.7083（±0.0000）
  - fact_recall 0.8312 / 0.8344（±0.0032）
  - false_refusal 0.0208 / 0.0208（±0.0000）
  - coverage 0.4893 / 0.4750（±0.0143）
  - high_conf 0.0095 / 0.0116（±0.0021）
  → 自然波动**不得**解释为 product regression；比较须在同 evaluator/verifier 口径下进行。

## 10. Contract Rule

- **Target 阈值完全冻结**（本阶段未改）。
- `eval/v3_quality_acceptance.json` 的 `current_baseline` 数值**保留**为 v1.0 历史（verifier f2-v2）以维持回归地板自洽，
  并新增 provenance 字段 `canonical_baseline` 指向 `eval/v4_initial_baseline.json`（标 SUPERSEDES）。
- **caveat（需用户决策，未自行调整）**：`citation_coverage` 的 regression floor（≥0.55）基于 pre-V4 验证口径标定，
  与 canonical（f2-v4）值不可直接比较；重定 regression floor 需**单独授权**。
- V3 历史文档（`docs/V3_*.md`）未修改；如需更正仅在 V4 文档记录 provenance。
