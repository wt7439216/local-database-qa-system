# V3 Product Quality Acceptance Contract

> 类型：**产品质量接受合同（正式冻结）**
> 版本：`quality-contract-v1.0`
> 状态：**FROZEN**
> 冻结日期：2026-09-09
> **frozen_by = explicit user authorization**（用户明确冻结 Target 档为正式质量接受标准，非 Agent 自主决定）
> 触发：Final Truthfulness Audit（`FINAL_TRUTHFULNESS_AUDIT_FINDS_OVERCLAIM`）→ Truthfulness Remediation → 用户明确冻结

---

## 0. 核心原则：两类阈值必须分离（永久）

Final Truthfulness Audit 确认了一个关键缺陷：当前把「回归基线」与「质量接受标准」混为同一件事，构成
`THRESHOLD_SEMANTICS_DEFECT`（先测后设：实测 0.65 → 设 0.60）。本合同强制分离两者，且**永久不得合并**。

| 概念 | 定义 | 作用 | 命名 |
|---|---|---|---|
| **Regression Baseline** | 当前真实测得的指标值 | 防止未来版本退化 | `CURRENT_REGRESSION_BASELINE` |
| **Product Quality Acceptance Standard** | 判断产品质量是否真正达标的标准 | 判断 V3 DoD 是否成立 | `PRODUCT_QUALITY_ACCEPTANCE_THRESHOLD` |

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

以下为 Final Truthfulness Audit 与 F.4.1 实测冻结的真实基线。**仅用于防退化与改进 delta 比较，不用于判定质量达标。**

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

### 3.2 Product Quality Gates（✅ 已冻结 v1.0，见 §4）

以下为**用户明确冻结**的正式质量接受标准（`PRODUCT_QUALITY_ACCEPTANCE_THRESHOLD`，Target 档）。见 §4。

### 3.3 Observation Only（记录，不设 SLA）

| Metric | 当前值 |
|---|---|
| E2E latency p50 / p95 | 19.77s / 50.89s |
| MODEL TTFT p50 / p95 | 2.14s / 2.22s |
| L1 uncertain rate | 154 / 554 = 0.2780 |

---

## 4. Frozen Product Quality Acceptance Thresholds（正式冻结 v1.0）

> **`frozen_by = explicit user authorization`**。以下 **Target 档** 是 V3 Product Quality DoD 的正式质量接受标准，
> 不是 regression baseline，二者永久区分。**Minimum 档**保留为 intermediate milestone / remediation progress
> checkpoint，**达到 Minimum 不得宣称 Product Quality DoD = PASS**。**Stretch 档**为高质量目标，不作为当前 V3
> blocking gate。

### 4.1 Answer Quality

| Metric | Minimum（milestone） | **Target（正式接受）** | Stretch（非 blocking） | 依据 |
|---|---|---|---|---|
| case_exact_fact_match_rate | ≥ 0.70 | **≥ 0.80** | ≥ 0.90 | 回答应在绝大多数 case 完整覆盖全部关键事实 |
| fact_recall | ≥ 0.85 | **≥ 0.90** | ≥ 0.95 | 关键事实粒度高覆盖，避免 case exact 过度严格 |
| false_refusal_rate | ≤ 0.05 | **≤ 0.03** | ≤ 0.01 | 有效问题不应被频繁错误拒绝 |

### 4.2 Citation Quality

| Metric | Minimum（milestone） | **Target（正式接受）** | Stretch（非 blocking） | 依据 |
|---|---|---|---|---|
| citation_coverage | ≥ 0.70 | **≥ 0.80** | ≥ 0.90 | 绝大多数 factual claim 应有引用支持；0.90 为原始计划高质量目标 |
| high_confidence_unsupported_rate | ≤ 0.10 | **≤ 0.05** | ≤ 0.02 | 确定性高置信冲突/缺失的 claim 必须维持低比例 |

### 4.3 Scope Safety（hard，非候选）

| Metric | 阈值 | 类型 |
|---|---|---|
| pure_OOS_false_accept_rate | = 0 | hard（安全边界） |

### 4.4 Multi-document / Multi-turn（需单独测量，阈值待定）

```text
multi_document_fact_recall       → 需从 144-case 中按 category 单独聚合（当前未单独拆出）
multi_document_case_exact_rate   → 同上
multi_turn_fact_recall           → 同上
topic_switch_error_rate          → 同上
```

> 这些指标当前未单独测量，正式阈值**暂不给出**，待单独聚合后再由用户冻结。不因「未测量」而伪装达标。

---

## 5. Citation Coverage 专门裁决（已冻结）

```text
Original suggested target = 0.90（V3_IMPROVEMENT_PLAN 建议，合法来源）
Current baseline          = 0.5534

正式接受阈值（Target）    = 0.80（用户冻结）
Stretch（非 blocking）    = 0.90（原始计划高质量目标，不得删除或改写成已达成）
Rationale = 90% 是原始计划建议目标，但当前 deterministic L1 无法达到（coverage 缺口主因是
            uncited claim = 301/554，而非引用错误）。90% 保留为 Stretch（需 L2 / 引用增强才可达），
            80% 冻结为正式 Target，70% 为 Minimum（milestone）。未因当前 0.5534 baseline 下调标准。
```

**禁止**：因当前只有 0.5534，就把最终标准定为 0.50 / 0.55 / 0.60。

---

## 6. Threshold Provenance Table（已冻结）

| Metric | Current baseline | Regression threshold | **Product quality threshold（正式）** | Source | Status |
| ------ | ---------------: | -------------------: | ------------------------: | ------ | ------ |
| case_exact_fact_match_rate | 0.6111 | ≥ 0.60（防退化） | **≥ 0.80（Target）** | 用户冻结 §4.1 | 已冻结 |
| fact_recall | 0.8248 | ≥ 0.80（防退化） | **≥ 0.90（Target）** | 用户冻结 §4.1 | 已冻结 |
| false_refusal_rate | 0.0278 | ≤ 0.05（防退化） | **≤ 0.03（Target）** | 用户冻结 §4.1 | 已冻结 |
| citation_coverage | 0.5534 | 记录（防退化） | **≥ 0.80（Target）** | 用户冻结 §4.2 / 原计划 90% Stretch | 已冻结 |
| high_confidence_unsupported_rate | 0.0812 | 记录（防退化） | **≤ 0.05（Target）** | 用户冻结 §4.2 | 已冻结 |
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

本合同的机器可读版本在 `eval/v3_quality_acceptance.json`（`quality-contract-v1.0`，frozen=true，frozen_by=explicit user authorization），
由 `tests/test_quality_acceptance.py` 校验 schema 与语义（hard gate 必须为 0、regression threshold 与 quality
threshold 语义分离、冻结阈值与用户授权的 Target 档一致）。

---

## 9. L2 触发条件（仅记录，非实施授权）

```text
real L1 uncertain rate = 154 / 554 = 0.2780

触发条件：如果未来仅靠 deterministic L1 无法达到已冻结的 Product Quality Gate（§4），
          则重新开启 L2 evaluation（NLI / LLM Judge）。
性质：这是【触发条件】，不是【实施授权】。DEFER_L2 维持。
```

---

## 10. 当前版本定位（诚实）

```text
Engineering complete                → 是（代码/测试/CI/迁移/安全/文档闭合）
Evaluation complete                 → 是（Golden 185 + 分层评测 + 指标 + telemetry）
Quality baseline established        → 是（CURRENT_REGRESSION_BASELINE 已冻结）
Quality contract frozen             → 是（PRODUCT_QUALITY_ACCEPTANCE_THRESHOLD = v1.0，用户冻结）
Product quality target satisfied    → 否（当前 baseline 未达 Target 档，见 §11 静态比较）

结论：CONDITIONALLY_READY（非 FAILED）
```

---

## 11. 正式冻结记录 + 当前 Gate Evaluation（静态比较，2026-09-09）

### 冻结记录

```text
version    = quality-contract-v1.0
status     = FROZEN
frozen_by  = explicit user authorization（非 Agent 自主决定）
frozen_date = 2026-09-09
accepted level = Target（Minimum 仅作 milestone，Stretch 仅作高质量目标）
```

### 当前 baseline 对正式质量合同的静态比较

| Metric | Baseline | 正式阈值（Target） | 静态结果 |
|---|---:|---:|---|
| case_exact_fact_match_rate | 0.6111 | ≥ 0.80 | **FAIL** |
| fact_recall | 0.8248 | ≥ 0.90 | **FAIL** |
| false_refusal_rate | 0.0278 | ≤ 0.03 | **PASS** |
| citation_coverage | 0.5534 | ≥ 0.80 | **FAIL** |
| high_confidence_unsupported_rate | 0.0812 | ≤ 0.05 | **FAIL** |

### 最终独立状态（合同冻结后，不因冻结而改变）

```text
Engineering Closure       = PASS
Evaluation Infrastructure = PASS
Quality Contract          = FROZEN（v1.0）
Product Quality DoD       = NOT_YET_PASS
V3 Release Readiness      = CONDITIONALLY_READY

READY_FOR_QUALITY_REMEDIATION_AUTHORIZATION
```

> 合同冻结不改变 Product Quality DoD = NOT_YET_PASS 的事实。当前 5 项质量指标中 4 项未达 Target 档，
> 需要后续质量优化（须单独授权）后重新评测，才可能升级为 Product Quality DoD = PASS。
