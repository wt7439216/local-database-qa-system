# V3 DoD Scope Amendment（正式裁决）

> 类型：Definition of Done 范围修订（Option B，已授权执行）
> 版本：`dod-amendment-v1`
> 日期：2026-09-09
> 关联证据：`docs/V3_PHASE_F4_RELEASE_GATE.md`（F.4 实测）、`docs/V3_PHASE_F4.1_CLOSURE.md`（F.4.1 收口）

## 1. Original Target（原 DoD 要求）

`docs/V3_IMPROVEMENT_PLAN.md` §13.1 hierarchical-summary target 与 §23.3 DoD 明确要求：

```text
Chunk/Block → Section Summary → Document Summary → Knowledge Base / Multi-document Summary
```

其中 §23.3 的「Multi-document」完成项包含：**Document Summary** 与 **Knowledge Base Summary**。

## 2. 授权依据

Phase F.4 授权文档 §24「特别处理 KB / Multi-document Summary」明确给出两个选项：

- **Option A**：实现 KB Summary 是完成 Phase F / V3 DoD 的必要条件 → `F.4 BLOCKED ON SUMMARY COMPLETION`
- **Option B**：现有 multi-document QA 已满足产品需求，KB Summary 属明确 deferred 非核心增强 → 必须修订 DoD / 范围文档，给出理由

F.4 已选择 **Option B**（授权范围内）。本文件是 Option B 的正式落实：修订 DoD 范围，消除「原 DoD 要求 KB Summary + V3 DoD PASS + 无 amendment」三者并存的自相矛盾。

## 3. 裁决：deferred items（非阻断）

| 项 | 原 DoD 状态 | 裁决 | 理由 |
|---|---|---|---|
| **KB Summary（知识库级摘要）** | 要求 | **DEFERRED（非阻断）** | 属「整库一键摘要」增强，非问答核心路径 |
| **Multi-document Summary feature（多文档聚合摘要）** | 要求 | **DEFERRED（非阻断）** | 同上，跨文档聚合摘要 |
| 文档级元数据查询（列表/页数/片段数/状态/scope） | Phase C/D 已 DEFERRED | **DEFERRED（非阻断）** | 已登记 deferred_meta_queries；F.4.1 加 deterministic guard 拒绝进 RAG |
| L2 semantic verifier（NLI/LLM Judge） | Phase F 可选 | **DEFERRED（F.3 决策）** | F.3 = DEFER_L2，未实现 |

## 4. Non-blocking rationale（为什么非阻断）

V3 核心 multi-document requirement 已由以下已实现能力满足：

1. **cross-document retrieval**（QueryScope + FTS/Qdrant 多文档检索，Phase A/D）；
2. **cross-document QA**（scoped retrieval + LLM answer，Phase D.1/F.4 实测 20 条跨文档 case）；
3. **compare**（跨文档比较，Phase E/F.4 实测）；
4. **locate**（跨文档定位，Phase E）；
5. **document summary**（层次摘要 section→document，Phase F.1 已实现）。

KB-wide one-click summary 是对上述能力的「聚合视图增强」，不提供新的问答能力，不阻断核心产品闭环。

## 5. 决策记录

- **decision**：Option B（KB Summary / Multi-document Summary feature deferred，非阻断）
- **decision date**：2026-09-08（F.4）→ 2026-09-09（F.4.1 正式落实本 amendment）
- **decision version**：`dod-amendment-v1`
- **authorized by**：Phase F.4 授权文档 §24（Option B）
- **applied by**：本文件 + `V3_IMPROVEMENT_PLAN.md` §A amendment note

## 6. 触发复评条件（满足任一即重新评估）

- 出现真实的「整库/多文档聚合摘要」产品需求；
- multi-document 规模显著扩大，cross-document QA 无法满足；
- 用户明确要求实现 KB Summary。

复评时不推翻本裁决，只评估是否升级 deferred 项为实现项。
