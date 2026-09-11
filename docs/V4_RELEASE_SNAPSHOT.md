# V4 Release Snapshot — Development Snapshot

> 本文描述当前**已经正式发布并接受**的 KB-V4 Development Snapshot。
> 它**不是** V4 Final，也**不代表**产品已完成。
>
> ```text
> CURRENT_RELEASE            = v4.0.0-alpha.2
> RELEASE_TYPE               = GitHub Pre-release
> ALPHA_2_RELEASE_ACCEPTANCE = PASS
> REMOTE_CI                  = PASS
> V4_FINAL                   = NO
> ```

---

## 1. Release Type

```text
Development Snapshot
GitHub Pre-release
NOT V4 Final
```

## 2. Accepted Release

```text
v4.0.0-alpha.2
```

```text
RELEASE_TYPE               = GitHub Pre-release（Development Snapshot）
ALPHA_2_RELEASE_ACCEPTANCE = PASS
REMOTE_CI                  = PASS（fresh LF GitHub Actions checkout）
```

> 已发布并接受。`v4.0.0-alpha.1` 因跨平台 CRLF/LF hash portability 问题被 **supersede**（tag/commit 保持不变）。

## 3. Current Baseline

```text
V4_6_2_HASH_PORTABILITY_BASELINE
```

Canonical production hash（line-ending portable，`sha256-path-content-v2-canonical-lf`）：

```text
108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c
```

历史 raw (CRLF) production hash provenance（V4.6.1）：

```text
7216c885d9ab315333973b9af6d9e0406da2a316f0f7abdcf89bef686d70a22a
```

（机器事实源：`eval/v4_6_2_hash_portability_baseline.json`；lineage current pointer：`eval/v4_baseline_lineage.json`。）

## 4. Current Models

```text
Answer model       qwen2.5:7b
Embedding model    bge-m3（dimension = 1024）
Vector backend     sqlite（默认）
Reranker           disabled by default
```

- Embedding identity 启动校验为 **fail-closed**；无自动 re-embed、无静默切换模型、无自动重建 SQLite / Qdrant。

## 5. Current Metrics（canonical Full-144）

> 产品指标自 V4.6.1 原样沿用（V4.6.2 为 measurement portability 阶段，`metrics_recomputed_in_stage = false`）；
> 机器事实源：`eval/v4_6_2_hash_portability_baseline.json`（其 `metrics` 逐字复制自 `V4_6_1_EMBEDDING_IDENTITY_BASELINE`）。

| 指标 | 当前值 | 最终 Target | 状态 |
|---|---:|---:|:--:|
| case_exact_fact_match_rate | 0.7292 | ≥ 0.80 | FAIL |
| fact_recall | 0.8535 | ≥ 0.90 | FAIL |
| false_refusal_rate | 0.0000 | ≤ 0.03 | PASS |
| citation_coverage | 0.4657 | ≥ 0.80 | FAIL |
| high_confidence_unsupported_rate | 0.0132 | ≤ 0.05 | PASS |
| invalid_citation_count | 0 | = 0 | PASS |
| citation_scope_violation | 0 | = 0 | PASS |

```text
Product Quality DoD = NOT_YET_PASS
```

## 6. Completed（本次快照包含）

```text
Evaluation Integrity            （canonical evaluator + 单一 Golden）
Failure Attribution framework   （持续刷新机制）
Scope/OOS remediation           （V4.4；false_refusal=0 / pure-OOS 0/7 / leakage=0）
Routing over-trigger remediation（V4.5）
Embedding Identity alignment    （V4.6.1；bge-m3 / 1024 + fail-closed 校验）
Baseline Governance             （不可变 stage baseline + 单一 current pointer）
Live Production Drift Guard     （live hash == current baseline 记录值）
Workspace Relocation            （数据库 / baseline / ImportPathPolicy 可移植）
Publication Scanner Portability （泄漏扫描无硬编码路径）
```

## 7. Known Unfinished

```text
Document Identity     NEXT
History               PENDING
Retrieval             PENDING
Generation            PENDING
Measurement Closure   PENDING
Citation Coverage     PENDING / DEFERRED
V4 Final              PENDING
```

Next product phase：

```text
V4.7 — Document Identity Root-Cause Confirmation（先诊断后修复）
```

## 8. Pre-release & CI Status

```text
v4.0.0-alpha.2 = PUBLISHED + ACCEPTED（REMOTE_CI = PASS）
v4.0.0-alpha.1 = SUPERSEDED / IMMUTABLE（tag/commit 保持不变）
```

alpha.1 的 CI 曾因内容哈希 / byte-identity guard 对 raw 字节敏感（Windows CRLF 工作树 vs Git LF checkout）失败；
V4.6.2 引入 canonical hash contract（`sha256-path-content-v2-canonical-lf`，仅规范化行尾）修复，
并由 alpha.2 的 **fresh LF GitHub Actions checkout** 验证通过。

## 9. Positioning

本快照当前**已作为 GitHub Pre-release 发布并接受**，可用于**试用与评测复现**。

它**不表示**：

- V4 已达到最终 Product Quality DoD；
- Document Identity / History / Retrieval / Generation / Measurement / Citation 已完成；
- 当前可称为稳定版 / 最终版。

```text
This snapshot is NOT V4 Final.
```

相关文档：[`V4_MASTER_REQUIREMENTS_AND_ROADMAP.md`](V4_MASTER_REQUIREMENTS_AND_ROADMAP.md) · [`../CHANGELOG.md`](../CHANGELOG.md) · [`INDEX.md`](INDEX.md)
