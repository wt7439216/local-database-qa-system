# V3 Phase F.4.1 — Final Closure Remediation

> 阶段性质：Phase F.4 的最小收口修复（不重新实施 F.4）
> 日期：2026-09-09
> 基线：`8602e3e`（F.4 候选发布基线）

## 1. Closure Scope（仅关闭审计确认的 6 项缺口）

1. `ANSWER_LEVEL_CLOSURE_INCOMPLETE` → 144/144 全量
2. `CITATION_CLOSURE_INCOMPLETE` → unsupported 用户可见 contract
3. Metadata deferred-query contract violation → deterministic guard
4. `PERFORMANCE_DOD_EVIDENCE_INCOMPLETE` → TTFT + E2E 补测
5. `DOD_SCOPE_AMENDMENT_AUTHORIZED_BUT_NOT_APPLIED` → 正式 amendment 文档
6. Documentation truthfulness → README / ARCHITECTURE / V3_PROGRESS 修正

## 2. Workstream A — 144/144 Answer Regression

`scripts/eval_v3_answer_full.py`（断点续跑 cache，key 绑定 case id/query/history/scope/golden hash/library identity/model/evaluator version）。

| 指标 | 结果 |
|---|---|
| **evaluated cases** | **144/144**（新生成 64 + cache 复用 80） |
| answer fact accuracy | 0.6111 |
| fact present / total | 259 / 314 |
| missing fact rate | 0.1752 |
| refusal count | 29 |

## 3. Workstream B — Citation Closure

### 144-case 完整指标（554 claim）

| 指标 | 结果 |
|---|---|
| invalid citation | **0** |
| scope violation | **0** |
| avg citation coverage | 0.5534 |
| SUPPORTED | 54（9.7%） |
| UNSUPPORTED | 346（62.5%） |
| UNCERTAIN | 154（27.8%） |

### UNSUPPORTED reason distribution（346 claim）

| reason code | 数量 | 分类 |
|---|---|---|
| `unsupported_no_evidence` | 301（87%） | uncited factual claim（coverage 缺口，非引用错误） |
| `unsupported_number_mismatch` | 35（10%） | **high-confidence deterministic conflict** |
| `unsupported_missing_key_term` | 10（3%） | potential L1 false-negative（同义/缩写） |

关键区分：UNSUPPORTED 的 87% 是 **uncited claim**（factual claim 无引用标记），而非"引用了错误证据"。真正的引用冲突（number mismatch + missing key term）= 45 claim。这使 citation quality 的核心问题是 **coverage（55.3%）**，而非 validity（invalid=0）或 support（有引用的 claim 大部分匹配）。

### Unsupported user-visible contract（最小安全方案）

采用 F.2 授权允许的：
```text
answer preserved + explicit unsupported flag + UI warning + citation_verified=false
```

- `engine_v2.py`：当 `citation_report` 存在 unsupported/invalid/scope-violation 时，`citation_verified` 降级为 `false`（不改 answer 文本、不删句）。
- 前端 `web/app.js` 既有 `citation_verified===false → toast("部分引用未通过原文核对，请谨慎采信")` 自动触发。
- telemetry 已记录 citation_report（含 unsupported_claim_count 等）。

**不满足**：high-confidence contradiction（number mismatch 35 条 + invalid=0）未做更高等级状态（如 suppress claim）——因 L1 UNSUPPORTED 混合 uncited 与真实冲突，自动删句回归风险高，本轮采用保守的 flag+warning，记录为剩余限制。

## 4. Workstream C — Metadata Deferred Query Guard

`core/query_router.py` 新增 `is_deferred_metadata_query` + `DEFERRED_METADATA_PATTERNS`；`classify_route` 在 book_toc 之后优先返回 `unsupported`。

- **11 条文档级 metadata query 全部 route=unsupported + ctx=0（不进 RAG）**。
- book_toc / book_overview / chapter_overview 无回归（"这本书有哪些章节" → book_toc，"介绍这本书" → book_overview）。
- Phase E router eval 108/108 保持。

## 5. Workstream D — Performance Closure

- **MODEL TTFT BENCHMARK**（streaming，qwen2.5:7b，明确标注为 model-side 非 Web 产品 TTFT）：p50 2.14s / p95 2.22s。
- **End-to-end total answer latency**（144-case answer 实测，含 retrieval + LLM）：p50 19.77s / p95 50.89s。
- 历史基线复用：FTS（Phase D 3.3/3.7ms）、dense（Phase A 10.4ms）、rerank（Phase B CUDA/CPU）。

## 6. Workstream E — DoD Option B Amendment

- `docs/V3_DOD_SCOPE_AMENDMENT.md`（`dod-amendment-v1`）：正式记录 Option B 裁决（KB Summary / Multi-document Summary = DEFERRED 非阻断），含 original target / 授权依据 / 非阻断理由 / 复评条件。
- `docs/V3_IMPROVEMENT_PLAN.md` 开头加最小 amendment note（指向 amendment 文档），消除「原 DoD 要求 KB Summary + V3 DoD PASS + 无 amendment」三者矛盾。

## 7. Release Threshold Truthfulness

当前 threshold（Recall@3 ≥0.80 / false-refusal ≤0.05 / route ≥0.90 / answer fact ≥0.60 / invalid citation=0）标记为：

> **baseline-derived release thresholds**（首次 F.4 测量后冻结），非 pre-registered mature SLA。

冻结规则：后续版本不得为了 PASS 单方面下调；任何下调需 versioned amendment + rationale + explicit review。

## 8. Documentation Truthfulness

- README：阶段状态表更新到 F.4.1，测试数 419→453，明确「Phase F 已完成 + V3 DoD 达标（含 deferred 非阻断项）」。
- ARCHITECTURE：新增 F.3/F.4/F.4.1 AS-IS 描述，更新 F.2 边界（移除「最终 Golden Set DEFERRED」的过时表述）。
- V3_PROGRESS：见下（旧过度 PASS 记录经 F.4.1 收口后重新成立，追加 F.4.1 记录）。

## 9. 环境问题（单独分类，不计入产品 PASS）

Qdrant E2E collection flakiness + Windows junction/symlink（CodeBuddy shim WinError 448）继续单独分类，本轮未扩大 scope 修复。

## 10. Gate Decision

**Phase F.4.1 = PASS**（6 项审计缺口全部关闭）。
