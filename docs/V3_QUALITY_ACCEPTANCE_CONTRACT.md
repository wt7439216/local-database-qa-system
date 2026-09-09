# V3 Product Quality Acceptance Contract

> 类型：**产品质量接受合同（draft，待用户冻结）**
> 版本：`quality-contract-v1-draft`
> 日期：2026-09-09
> 触发：Final Truthfulness Audit（`FINAL_TRUTHFULNESS_AUDIT_FINDS_OVERCLAIM`）后的真值修复
> 性质：**本轮仅冻结概念与候选阈值，不实施任何质量优化代码，不重新评测。**

---

## 0. 核心原则：两类阈值必须分离

Final Truthfulness Audit 确认了一个关键缺陷：当前把「回归基线」与「质量接受标准」混为同一件事，构成
`THRESHOLD_SEMANTICS_DEFECT`（先测后设：实测 0.65 → 设 0.60）。本合同强制分离两者。

| 概念 | 定义 | 作用 | 命名 |
|---|---|---|---|
| **Regression Baseline** | 当前真实测得的指标值 | 防止未来版本退化 | `CURRENT_REGRESSION_BASELINE` |
| **Product Quality Acceptance Standard** | 判断产品质量是否真正达标的标准 | 判断 V3 DoD 是否成立 | `PRODUCT_QUALITY_THRESHOLD` |

**禁止**：`当前 baseline 是 X，所以 threshold 设为略低于 X` —— 这类只能叫 regression threshold，不能叫 quality acceptance threshold。

---

## 1. Metric Glossary（统一命名，禁止混称）

Final Audit 确认 `METRIC_NAMING_AMBIGUITY`：`answer_fact_accuracy = 0.6111` 与 `fact_present/total = 259/314`
被混称为「回答事实准确率」，实为两个不同指标。以下为正式命名。

### 1.1 `case_exact_fact_match_rate`（原「answer fact accuracy」）

```text
定义：一个 answer case 只有在【所有 expected facts 均命中】且【没有错误拒答】时才算通过。
公式：fact_ok / fact_cases
      fact_ok    = count(case: not refused AND fact_present == fact_total AND fact_total > 0)
      fact_cases = count(case: fact_total > 0)
当前值：0.6111（= 88 / 144）
```

### 1.2 `fact_recall`

```text
定义：单个 expected fact 被命中的比例（fact-level，与 case-level 相对）。
公式：sum(fact_present) / sum(fact_total)
当前值：0.8248（= 259 / 314）
```

### 1.3 `missing_fact_rate`

```text
定义：单个 expected fact 缺失的比例。
公式：1 - fact_recall
当前值：0.1752
```

### 1.4 `citation_coverage`

```text
定义：需要证据支持的 factual claim 中有多少具备 citation。
公式：cited_factual_claims / factual_claims
当前值：0.5534
```

### 1.5 `high_confidence_unsupported_rate`

```text
定义：确定性 verifier 给出 high-confidence 冲突的 claim 占全部 claim 的比例。
      仅计入【number_mismatch + missing_key_term】；【no_evidence 属于 coverage 缺口，不计入本指标】。
公式：(number_mismatch + missing_key_term) / total_claims
当前值：0.0812（= 45 / 554 = (35 + 10) / 554）
```

### 1.6 硬安全指标（不可缺）

```text
invalid_citation_count       = 0（citation validity 100%）
citation_scope_violation     = 0（scope leakage 0）
```

---

## 2. CURRENT_REGRESSION_BASELINE（当前真实基线，非质量标准）

以下为 Final Truthfulness Audit 与 F.4.1 实测冻结的真实基线。**仅用于防退化，不用于判定质量达标。**

| Metric | Current baseline | 测量数据集 |
|---|---|---|
| case_exact_fact_match_rate | 0.6111 | 144-case answer（真实 Ollama，qwen2.5:7b） |
| fact_recall | 0.8248 | 144-case answer |
| missing_fact_rate | 0.1752 | 144-case answer |
| false_refusal_rate | 0.0278 | 144 eligible（4/144） |
| citation_coverage | 0.5534 | 144-case citation（554 claim） |
| high_confidence_unsupported_rate | 0.0812 | 554 claim（45 high-confidence 冲突） |
| invalid_citation_count | 0 | 554 claim |
| citation_scope_violation | 0 | 554 claim |
| E2E latency p50 | 19.77s | 144-case 实测 |
| E2E latency p95 | 50.89s | 144-case 实测 |
| MODEL TTFT p50 / p95 | 2.14s / 2.22s | model-side streaming benchmark |

---

## 3. Hard Gate / Quality Gate / Observation 分层

Final Audit 要求不得把「Hard Gates 全过」推导为「Product Quality PASS」。

### 3.1 Hard Safety / Correctness Gates（阻断级，必须绝对满足）

| Gate | 阈值 | 类型 | 来源 | 当前值 |
|---|---|---|---|---|
| scope leakage | = 0 | hard | 安全边界（Phase D） | 0 ✅ |
| invalid citation | = 0 | hard | 引用有效性安全（Phase F.2） | 0 ✅ |
| security regression | = 0 | hard | 安全边界 | 0 ✅ |
| migration integrity | PASS | hard | 数据完整性（Phase D.1.1） | PASS ✅ |
| unit/integration tests | PASS | hard | 工程闭合 | PASS ✅ |

### 3.2 Product Quality Gates（候选，`USER_DECISION_REQUIRED`）

以下阈值**非权威标准**，是候选等级。用户须明确冻结其一（或另定），冻结后方可作为 V3 DoD 质量判定依据。

### 3.3 Observation Only（记录，不设 SLA）

| Metric | 当前值 |
|---|---|
| E2E latency p50 / p95 | 19.77s / 50.89s |
| MODEL TTFT p50 / p95 | 2.14s / 2.22s |
| L1 uncertain rate | 154 / 554 = 0.2780 |

---

## 4. Candidate Quality Contract（候选等级，待用户冻结）

> **`USER_DECISION_REQUIRED`**：以下三档为候选，Codex 不得自行宣告其为权威标准。
> 用户须明确选择（或另定阈值），写入 `eval/v3_quality_acceptance.json` 并将本文件从 draft 升级为 frozen。

### 4.1 Answer Quality

| Metric | Minimum Acceptable | Target | Stretch | 依据类型 |
|---|---|---|---|---|
| case_exact_fact_match_rate | ≥ 0.70 | ≥ 0.80 | ≥ 0.90 | 可解释工程标准 + 人工审核需求 |
| fact_recall | ≥ 0.85 | ≥ 0.90 | ≥ 0.95 | 可解释工程标准 |
| false_refusal_rate | ≤ 0.05 | ≤ 0.03 | ≤ 0.01 | 用户体验要求 |

### 4.2 Citation Quality

| Metric | Minimum Acceptable | Target | Stretch | 依据类型 |
|---|---|---|---|---|
| citation_coverage | ≥ 0.70 | ≥ 0.80 | ≥ 0.90 | 原始 V3 计划目标（§建议 90%） |
| high_confidence_unsupported_rate | ≤ 0.10 | ≤ 0.05 | ≤ 0.02 | 质量风险等级 |

### 4.3 Scope Safety

| Metric | Minimum Acceptable | Target | Stretch | 依据类型 |
|---|---|---|---|---|
| pure_OOS_false_accept_rate | = 0 | = 0 | = 0 | 安全边界（hard，非候选） |

### 4.4 Multi-document / Multi-turn（需单独测量，候选待定）

```text
multi_document_fact_recall       → 需从 144-case 中按 category 单独聚合（当前未单独拆出）
multi_document_case_exact_rate   → 同上
multi_turn_fact_recall           → 同上
topic_switch_error_rate          → 同上
```

> 这些指标当前未单独测量，候选阈值**暂不给出**，待单独聚合后再由用户冻结。不因「未测量」而伪装达标。

---

## 5. Citation Coverage 专门裁决

```text
Original suggested target = 0.90（V3_IMPROVEMENT_PLAN 建议，合法来源）
Current baseline          = 0.5534

Recommended product acceptance threshold = 候选三档（见 §4.2），USER_DECISION_REQUIRED
Rationale = 90% 是原始计划建议目标，但当前 deterministic L1 无法达到（coverage 缺口主因是
            uncited claim = 301/554，而非引用错误）。90% 定为 Stretch（需 L2 / 引用增强才可达），
            80% 为 Target，70% 为 Minimum Acceptable。最终档位须由用户冻结。
```

**禁止**：因当前只有 0.5534，就把最终标准定为 0.50 / 0.55 / 0.60 —— 除非存在与当前 baseline 无关的充分产品理由（当前无此理由）。

---

## 6. Threshold Provenance Table

| Metric | Current baseline | Regression threshold | Product quality threshold | Source | Status |
| ------ | ---------------: | -------------------: | ------------------------: | ------ | ------ |
| case_exact_fact_match_rate | 0.6111 | ≥ 0.60（防退化） | `USER_DECISION_REQUIRED` | 候选 §4.1 | 待冻结 |
| fact_recall | 0.8248 | ≥ 0.80（防退化） | `USER_DECISION_REQUIRED` | 候选 §4.1 | 待冻结 |
| false_refusal_rate | 0.0278 | ≤ 0.05（防退化） | `USER_DECISION_REQUIRED` | 候选 §4.1 | 待冻结 |
| citation_coverage | 0.5534 | 记录（防退化） | `USER_DECISION_REQUIRED` | 候选 §4.2 / 原计划 90% | 待冻结 |
| high_confidence_unsupported_rate | 0.0812 | 记录（防退化） | `USER_DECISION_REQUIRED` | 候选 §4.2 | 待冻结 |
| invalid_citation_count | 0 | = 0（hard） | = 0（hard） | 安全边界 | 已冻结 hard |
| citation_scope_violation | 0 | = 0（hard） | = 0（hard） | 安全边界 | 已冻结 hard |
| E2E latency p50 / p95 | 19.77s / 50.89s | 记录（observation） | 不设 SLA | observation | observation |

---

## 7. 阈值来源规则（合法 / 禁止）

**允许来源**：
1. 原始 V3 计划明确目标（如 citation coverage 90% 建议）；
2. 明确用户体验要求；
3. 质量风险等级；
4. 可解释的工程标准；
5. 人工审核需求。

**禁止来源**：
> 「当前 baseline 是 X，所以 threshold 设为略低于 X」—— 这类只能叫 regression threshold，不能叫 quality acceptance threshold。

---

## 8. 机器可读合同

本合同的机器可读版本在 `eval/v3_quality_acceptance.json`，由 `tests/test_quality_acceptance.py` 校验 schema 与
语义（如 hard gate 必须为 0、regression threshold 不得与 quality threshold 混用、`USER_DECISION_REQUIRED` 项
不得被当作已冻结 quality threshold）。

---

## 9. L2 触发条件（仅记录，非实施授权）

```text
real L1 uncertain rate = 154 / 554 = 0.2780

触发条件：如果未来 Product Quality Gate 冻结后，仅靠 deterministic L1 无法达到该 gate，
          则重新开启 L2 evaluation（NLI / LLM Judge）。
性质：这是【触发条件】，不是【实施授权】。DEFER_L2 维持。
```

---

## 10. 当前版本定位（诚实）

```text
Engineering complete                → 是（代码/测试/CI/迁移/安全/文档闭合）
Evaluation complete                 → 是（Golden 185 + 分层评测 + 指标 + telemetry）
Quality baseline established        → 是（CURRENT_REGRESSION_BASELINE 已冻结）
Product quality target satisfied    → 否（PRODUCT_QUALITY_THRESHOLD 待用户冻结，未独立满足）

结论：CONDITIONALLY_READY（非 FAILED）
```
