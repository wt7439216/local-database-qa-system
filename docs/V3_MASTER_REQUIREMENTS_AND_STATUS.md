# KB-V3 本地数据库问答系统
# 需求、已实现能力、待实现能力与当前阶段总清单

> 项目：Local Database Q&A System / KB-V3  
> 当前开发事实源：`Local Database Q&A System本地版v3`  
> 当前 Git 发布基线：见 `docs/V3_FINAL_BASELINE.md`（V3 FINAL SOURCE COMMIT）  
> 当前 Product Quality Contract：`v1.0 / FROZEN`  
> 当前 Product Quality DoD：`NOT_YET_PASS`  
> 当前 V3 Release Readiness：`CONDITIONALLY_READY`  
> 本文状态：基于 Q4.2 完成后的最新项目事实重新整理；V3 开发周期已于本 commit 冻结（见 `docs/V3_FINAL_BASELINE.md`）

---

# 0. 文档目的

本文作为 KB-V3 当前阶段的**总需求 / 实现状态 / 待办总控清单**，用于统一：

1. 产品需求；
2. 系统架构约束；
3. 已实现功能；
4. 已验证但未采用的方案；
5. Deferred 能力；
6. 当前正式 Product Quality Gate；
7. 已完成 Phase / Remediation Workstream；
8. 当前真实缺陷；
9. 后续实施顺序；
10. 最终 V3 Product Quality DoD 判定条件。

本文特别用于避免以下问题再次发生：

- 将工程闭环误写成产品质量达标；
- 将 Deferred 写成 Implemented；
- 将 Citation Validity / Coverage / Support 混为一个指标；
- 将 Multi-document QA 与 Multi-document Summary 混淆；
- 根据当前结果倒推质量门槛；
- 为提高评分修改 Golden；
- 在缺少 failure attribution 时盲目修改 Retriever / Prompt / Router。

---

# 1. 权威事实优先级

若不同材料存在冲突，以以下顺序为准：

1. 当前 production code；
2. 当前 tests；
3. 当前 evaluator 实现；
4. 冻结的机器可读 Product Quality Contract；
5. 实际 evaluation outputs；
6. `docs/ARCHITECTURE.md`；
7. `docs/V3_PROGRESS.md`；
8. `docs/V3_DOD_SCOPE_AMENDMENT.md`；
9. `docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md`；
10. `docs/V3_IMPROVEMENT_PLAN.md`；
11. README；
12. 历史自然语言报告。

---

# 2. 工作区与 Git 发布模型

## 2.1 ACTIVE DEVELOPMENT WORKSPACE

```text
E:\ZCode_ws\.zcode\workspace\Local Database Q&A System\Local Database Q&A System本地版v3
```

角色：

- 唯一最新开发事实源；
- 当前 production code / tests / eval 的开发位置；
- 可以没有 `.git`；
- **禁止执行 `git init`**；
- 不得因为不存在 `.git` 判定环境异常。

状态：

- [x] 工作区角色已冻结
- [x] 多阶段执行均遵循此约束
- [ ] 后续所有 Agent 阶段继续要求 Preflight 确认

## 2.2 GIT PUBLISH WORKSPACE

```text
E:\ZCode_ws\.zcode\workspace\Local Database Q&A System\Local Database Q&A System上传版
```

GitHub：

```text
https://github.com/wt7439216/local-database-qa-system
```

目标分支：

```text
main
```

当前权威发布 commit：

```text
见 docs/V3_FINAL_BASELINE.md（V3 FINAL SOURCE COMMIT）
```

标准发布流程：

```text
Active Workspace
→ local validation
→ publication sync
→ upload diff gate
→ commit
→ push
→ GitHub Actions
→ remote closure
```

状态：

- [x] 双工作区职责已明确
- [x] publication sync 已稳定使用
- [x] CI 已纳入正式闭环
- [x] remote closure 已纳入正式闭环
- [ ] 后续每阶段仍需确认 `HEAD == origin/main`

---

# 3. 项目核心产品目标

KB-V3 的核心目标：

> 构建一个本地、可控、可追踪、可引用、可多文档检索、可多轮追问的知识库问答系统，并保持本地数据安全、证据约束和可重复评测。

核心用户能力：

- [x] 导入本地文档
- [x] 文档持久化
- [x] 建立本地向量索引
- [x] 关键词/稀疏检索
- [x] 混合检索
- [x] 本地 LLM 问答
- [x] Scope 限定
- [x] 问题路由
- [x] 多轮追问
- [x] Locate
- [x] Compare
- [x] Multi-document QA
- [x] Citation
- [x] Citation Verification
- [x] Summary
- [x] Import Path Security
- [x] Offline/real eval infrastructure
- [x] Product Quality Contract
- [ ] Product Quality DoD 最终通过

---

# 4. 基础架构需求

## 4.1 SQLite

设计原则：

```text
SQLite = business source of truth
```

已实现：

- [x] 文档元数据持久化
- [x] chunk 持久化
- [x] summary 持久化
- [x] provenance 持久化
- [x] lifecycle
- [x] reimport
- [x] Qdrant 可从 SQLite 重建

## 4.2 Qdrant

职责：

```text
rebuildable dense index
```

当前正式 collection：

```text
general_documents
local_knowledge_chunks
```

已实现：

- [x] Dense Retrieval
- [x] SQLite ↔ Qdrant identity
- [x] 多文档 retrieval
- [x] eval library 使用

当前限制：

- [ ] Qdrant E2E 偶发 flakiness
- [ ] 不作为当前 Answer/Citation remediation 的优先修改对象

## 4.3 FTS

已实现：

- [x] SQLite FTS
- [x] sparse search
- [x] keyword retrieval
- [x] Hybrid integration

## 4.4 Hybrid Retrieval

已实现：

- [x] Dense + FTS
- [x] RRF
- [x] scope-aware retrieval
- [x] multi-document retrieval

当前结论：

> 当前 Answer Quality failure attribution 不支持优先大改 Retriever。

---

# 5. Reranker

使用模型：

```text
BAAI/bge-reranker-v2-m3
```

历史结果：

```text
RRF-only:
MRR    = 0.956
nDCG@5 = 0.651

Reranker K=16:
nDCG@5 = 0.660

gain = +0.008
required = >= +0.02
```

结论：

```text
FAIL / NOT ADOPTED AS DEFAULT
```

状态：

- [x] 实现/接线已验证
- [x] CPU / CUDA 性能已测
- [x] 收益不足时未强行上线
- [x] 默认关闭
- [ ] 当前不重开

---

# 6. 文档导入能力

已实现：

- [x] 基本文档导入
- [x] 多格式 ingest 主链
- [x] chunking
- [x] metadata
- [x] SQLite 写入
- [x] Dense Index
- [x] reimport lifecycle
- [x] general ingestion regression

---

# 7. Import Path Security

历史问题：

```text
payload["path"]
```

曾可直接传入任意服务进程可读路径。

已实现：

- [x] `ImportPathPolicy`
- [x] canonical path
- [x] `normcase`
- [x] `commonpath`
- [x] allowed import roots
- [x] web/server 接线
- [x] UI 安全显示字段
- [x] 输出脱敏
- [x] security tests

已知环境差异：

- [x] Windows junction / CodeBuddy shim 环境曾触发 WinError 448
- [x] GitHub CI 对应测试成功
- [ ] 保留 environment-specific validation gap 记录

---

# 8. Router 总体能力

当前正式 route：

```text
qa
compare
locate
locate_chapter
book_toc
book_overview
chapter_overview
unsupported
```

不存在：

```text
metadata
multi_document
```

其中 multi-document QA 通过现有 route + scope/document retrieval 完成。

---

# 9. Phase E Router Truth

冻结结果：

```text
route             = 108/108
follow-up         = 66/66
ambiguous         = 0/8 false-resolution
scope conflict    = 10/10
engine leakage    = 0
```

状态：

```text
Phase E = FINAL PASS
```

Q4.2 后仍：

```text
108/108 PASS
```

---

# 10. Scope Gate

需求：

> 明确知识库外 query 应拒答，不允许 RAG 对明显无关内容生成伪答案。

已实现：

- [x] pure OOS rejection
- [x] scope conflict
- [x] scope leakage protection
- [x] router/scope 分工
- [x] telemetry

正式 Gate：

```text
false_refusal_rate <= 0.03
```

当前：

```text
0.0278
```

状态：

```text
PASS
```

---

# 11. Metadata 能力

## 11.1 Book-level Metadata-like Query

已实现：

- [x] book TOC
- [x] chapter list
- [x] chapter count
- [x] book overview
- [x] chapter overview

## 11.2 Document / Library Metadata Query

例如：

```text
有哪些文档？
有多少文档？
某文档是否已导入？
当前有哪些知识库？
chunk 数量是多少？
```

当前：

```text
DEFERRED
```

F.4.1 已实现安全 guard：

- [x] `is_deferred_metadata_query`
- [x] deferred metadata -> `unsupported`
- [x] contexts = 0
- [x] 不进入 RAG
- [x] book route 不误伤

说明：

> 正确拒答 ≠ metadata 功能已实现。

因此：

- [ ] 文档级 metadata 查询仍未实现
- [x] Scope Amendment 已正式记录
- [x] 当前为 deferred 非 blocking

---

# 12. Summary 系统

## 12.1 Section Summary

已实现：

- [x] chunk-derived section summary
- [x] provenance
- [x] dependency hash
- [x] invalidation

## 12.2 Document Summary

已实现：

- [x] hierarchical document summary
- [x] aggregate section summaries
- [x] SQLite truth source
- [x] lifecycle
- [x] reimport invalidation
- [x] compatibility mirror

Summary provenance：

```text
scope_id
source_ids
dependency_hash
generator_type
model
prompt_version
generated_at
summary_version
```

## 12.3 KB Summary

```text
NOT IMPLEMENTED
DEFERRED
```

- [ ] 整库摘要未实现
- [x] DoD Scope Amendment 已明确
- [x] 非当前 Product Quality Gate

## 12.4 Multi-document Summary

```text
NOT IMPLEMENTED
DEFERRED
```

注意：

```text
Multi-document QA != Multi-document Summary
```

当前：

- [x] Multi-document QA
- [ ] Multi-document Summary

---

# 13. Multi-document QA

已实现：

- [x] 多文档检索
- [x] 多文档 answer synthesis
- [x] multi-doc evidence
- [x] citations
- [x] Golden cases

当前仍存在：

- [ ] 部分 multi-doc completeness
- [ ] 文档身份/metadata 与 chunk text 分离导致的边界问题
- [ ] Citation Coverage 偏低

---

# 14. Multi-turn QA

已实现：

- [x] history 输入
- [x] follow-up
- [x] Phase E 66/66 follow-up
- [x] topic-switch safety

当前待处理：

- [ ] `mt-003`
- [ ] `mt-006`
- [ ] 指代/实体继承
- [ ] history resolution

推荐下一阶段：

```text
Q4.3a Multi-turn History Resolution
```

状态：

```text
NOT STARTED
```

---

# 15. Locate

已实现：

- [x] locate
- [x] locate_chapter
- [x] section/chapter location
- [x] Q4.2 `"第几节"/"哪一节"/"哪些节"` route support

Q4.2 修复：

```text
loc-016: qa -> locate
loc-017: qa -> locate
```

状态：

```text
TRUE_ROUTE_DEFECTS_FIXED
```

当前评测问题：

- [ ] Locate Golden 对“重复术语”要求偏严
- [ ] `1.` vs `第1`
- [ ] 定位模板与 expected_fact 语义不完全一致

---

# 16. Compare

已实现：

- [x] compare route
- [x] compare synthesis
- [x] compare evidence
- [x] compare Golden

Q4.2 修复：

```text
cmp-015:
qa -> compare
```

泛化规则：

```text
一致吗
是否一致
一致否
一致不
一不一致
```

避免裸 `"一致"` 导致 over-route。

Targeted answer validation：

```text
cmp-015:
3/3 facts recovered
```

---

# 17. Citation 架构

Citation Quality 必须拆为：

1. Validity
2. Scope Safety
3. Coverage
4. Support

不得使用一个模糊 `Citation Quality PASS` 替代四项。

---

# 18. Citation Validity

当前：

```text
invalid citation = 0
```

状态：

```text
PASS
```

已实现：

- [x] ID validity
- [x] normalize
- [x] renumber
- [x] invalid blocking
- [x] pre-renumber verification fix

---

# 19. Citation Scope Safety

当前：

```text
scope violation = 0
```

状态：

```text
PASS
```

---

# 20. Citation Coverage

正式 Product Gate 口径：

```text
case-level average citation coverage
```

正式 baseline：

```text
0.5524
```

Gate：

```text
>= 0.80
```

状态：

```text
FAIL
```

诊断 micro：

```text
claim-level ≈ 0.4577
```

不得用 claim-level 替代正式 Gate。

---

# 21. Q2 Prompt-only Citation Remediation

状态：

```text
Q2 = FAIL
Q2_PROMPT_ONLY_INSUFFICIENT
```

Full 144：

```text
coverage:
0.5524 -> 0.5542

claim-level:
0.4577 -> 0.4381

case_exact:
0.7014 -> 0.6667

fact_recall:
0.8248 -> 0.8057

factual claims:
555 -> 630

citation markers:
310 -> 306
```

结论：

- [x] Prompt-only 已实证不足
- [x] 失败 Prompt 已 rollback
- [x] 未发布失败 production behavior
- [ ] 不建议继续无证据 Prompt 堆叠

---

# 22. Citation Verifier — F.2 / Q3

当前 verifier：

```text
f2-v4
```

## 22.1 F.2

已实现：

- [x] claim segmentation
- [x] CJK
- [x] Latin
- [x] numeric
- [x] units
- [x] multi-citation
- [x] deterministic L1
- [x] reason codes
- [x] telemetry
- [x] offline eval

当前 F.2 offline：

```text
37/37 PASS
```

## 22.2 Q3

Q3 前：

```text
high_confidence_unsupported_rate = 0.0829
number_mismatch = 36
missing_key_term = 10
```

Q3 后：

```text
high_confidence_unsupported_rate = 0.0161
number_mismatch = 4
missing_key_term = 5
```

正式 Gate：

```text
<= 0.05
```

状态：

```text
PASS
```

---

# 23. Q3.1 Verifier Edge Closure

状态：

```text
PASS
```

已完成：

- [x] E/N0
- [x] SNR symbol handling
- [x] pure citation fragment
- [x] generic full-name Latin terms
- [x] slash token handling
- [x] selector simulation

最终：

```text
DETERMINISTIC_CITATION_COMPLETION_READINESS =
SAFE_CANDIDATE
```

---

# 24. Q2.2 Deterministic Citation Completion

状态：

```text
Q2.2 = INSUFFICIENT
PRODUCT_CITATION_GATE = FAIL
```

已实现实验模块：

```text
core/citation_completion.py
```

生产 engine：

```text
NOT ENABLED
```

离线 replay：

```text
uncited factual claims = 301
unique supported       = 29
ambiguous              = 70
uncertain              = 216
unsupported            = 16
```

Projected：

```text
case-level coverage:
0.5558 -> 0.5972

gain = +0.0414
```

因此：

- [x] unique-supported selector 设计完成
- [x] safety tests 完成
- [x] 模块保留
- [x] engine 接入 rollback
- [ ] production Citation Completion 未启用
- [ ] Citation Gate 仍 FAIL

核心原因：

> 大部分 uncited claim 属 deterministic L1 `UNCERTAIN`，主要是 CJK 语义同义/表达变化。

---

# 25. L2 Semantic Verifier

Phase F.3：

```text
Decision = DEFER_L2
```

历史结果：

```text
L1 accuracy      = 0.28
L2 accuracy      = 0.74
L1 false-support = 0.10
L2 false-support = 0.04
L1 uncertain     = 0.54
L2 uncertain     = 0.00
L2 p50           ≈ 2.74s
```

当前：

```text
DEFER_L2
```

---

# 26. Answer Quality 指标

正式 Gate：

```text
case_exact_fact_match_rate >= 0.80
fact_recall                >= 0.90
```

当前正式 baseline：

```text
case_exact = 0.7014
fact_recall = 0.8248
```

状态：

```text
FAIL
FAIL
```

---

# 27. Q1 — Evaluator Refusal Precision

Q1 已修复：

- [x] structured refusal priority
- [x] anchored refusal templates
- [x] factual negation 不误判
- [x] limitation answer 不误判
- [x] EMPTY 独立

结果：

```text
refusal count:
29 -> 4

all-facts-present-but-refused:
13 -> 0

case_exact:
0.6111 -> 0.7014
```

状态：

```text
Q1 = PASS
```

---

# 28. Q1.1 Corrected Evaluation Baseline

冻结：

```text
q1-corrected-v1
```

正式值：

```text
case_exact_fact_match_rate = 0.7014
fact_recall                = 0.8248
missing_fact_rate          = 0.1752
false_refusal_rate         = 0.0278
citation_coverage          = 0.5524
```

---

# 29. Q4.0 Answer Completeness Attribution

基线：

```text
55 missing facts
43 non-exact cases
```

初始归因：

```text
B Evidence-present omission = 21
D Golden mismatch           = 15
E Wrong refusal / empty     = 10
A Retrieval miss            = 6
C Paraphrase FN             = 3
```

但 Q4.1 进一步证明：

> 初始 B 类明显高估 synthesis omission。

---

# 30. Q4.1 Targeted Answer Completeness

状态：

```text
Q4.1 = Q4.1_SYNTHESIS_ONLY_INSUFFICIENT
```

Target：

```text
21 B facts
20 cases
```

Canary：

```text
B recovered = 1/21
```

因此：

- [x] route-aware synthesis contract 已实验
- [x] 仅恢复 1 fact
- [x] Prompt 已 rollback
- [x] 未 full 144
- [x] 未 publication
- [ ] 不再将 Answer Quality 主因归为 synthesis omission

---

# 31. Q4.2 Deterministic Route Fix

状态：

```text
Q4.2 = PASS
```

重新归因 target：

```text
cmp-015 = TRUE_ROUTE_DEFECT
loc-016 = TRUE_ROUTE_DEFECT
loc-017 = TRUE_ROUTE_DEFECT
md-014  = NOT_A_ROUTER_DEFECT
```

修复：

```text
cmp-015: qa -> compare
loc-016: qa -> locate
loc-017: qa -> locate
```

结果：

```text
TRUE_ROUTE_DEFECTS_FIXED = 3/3
```

Targeted answer：

```text
cmp-015:
3/3 facts recovered
```

Phase E：

```text
108/108 PASS
```

Tests：

```text
511 OK
```

---

# 32. Q4.2 后剩余真实 Answer Defects

## 32.1 History Resolution

已知：

```text
mt-003
mt-006
```

问题：

```text
follow-up reference / entity inheritance
```

状态：

```text
NOT FIXED
```

推荐：

```text
Q4.3a
```

## 32.2 True Retrieval Miss

已知包括：

```text
qa-030
cmp-001
loc-018
```

状态：

```text
NOT FIXED
```

推荐：

```text
Q4.3b
```

## 32.3 Multi-document Document Identity

已知：

```text
md-014
```

问题：

```text
document identity/title metadata
not necessarily in chunk text
```

状态：

```text
NOT FIXED
```

推荐：

```text
Q4.3c
```

---

# 33. Evaluator Fact Matcher

当前 evaluator：

```text
exact substring
```

即：

```python
f in answer
```

已知 paraphrase false-negative：

- 信噪比 vs 信号功率与噪声功率谱密度之比
- 错误 vs 差错
- 多址 / OFDMA 等表达边界

当前：

```text
EVALUATOR MATCHER REVIEW = NOT STARTED
```

原则：

> 先修真实 production defects，再单独调整评分尺子。

---

# 34. Golden Contract Mismatch

已知约：

```text
15 missing facts
```

涉及：

- Locate 不必要重复 query 术语
- `1.` vs `第1`
- document identity
- abbreviation/full-name
- citation_negative 表达语义

当前：

```text
GOLDEN CONTRACT REVIEW = NOT STARTED
```

禁止当前直接修改 Golden 提升指标。

---

# 35. Product Quality Acceptance Contract

```text
version = v1.0
status  = FROZEN
```

正式 Gate：

| Metric | Threshold |
|---|---:|
| `case_exact_fact_match_rate` | `>= 0.80` |
| `fact_recall` | `>= 0.90` |
| `false_refusal_rate` | `<= 0.03` |
| `citation_coverage` | `>= 0.80` |
| `high_confidence_unsupported_rate` | `<= 0.05` |

---

# 36. 当前 Product Gate 状态

| Gate | Current | Target | Status |
|---|---:|---:|---|
| case exact | 0.7014 | >=0.80 | FAIL |
| fact recall | 0.8248 | >=0.90 | FAIL |
| false refusal | 0.0278 | <=0.03 | PASS |
| citation coverage | 0.5524 | >=0.80 | FAIL |
| high-conf unsupported | 0.0161 | <=0.05 | PASS |

当前：

```text
2 / 5 PASS
3 / 5 FAIL
```

因此：

```text
Product Quality DoD = NOT_YET_PASS
```

---

# 37. Performance

当前：

```text
MODEL TTFT:
p50 = 2.14s
p95 = 2.22s

E2E:
p50 = 19.77s
p95 = 50.89s
```

状态：

- [x] 已测
- [x] TTFT / E2E 区分
- [ ] 尚未冻结 Performance SLA
- [ ] E2E p95 有明显体验风险

---

# 38. Golden Set

```text
Final Golden = 185 cases
Answer eligible = 144
Expected refusal/non-answer = 41
```

类别：

```text
single_fact_qa
locate
compare
multi_turn
multi_document
oos_hard_negative
metadata_library
citation_negative
```

---

# 39. CI

当前 CI 覆盖：

- [x] unit tests
- [x] ruff
- [x] compileall
- [x] node
- [x] Phase E
- [x] F.2
- [x] quality contract validation
- [x] router/verifier regression

不覆盖：

- [ ] full 144 Ollama answer quality
- [ ] full E2E performance
- [ ] L2 semantic challenge
- [ ] complete Product Quality

原则：

```text
CI success != Product Quality PASS
```

---

# 40. 当前 Phase / Workstream 总览

| 阶段 | 状态 |
|---|---|
| Phase A | PASS |
| Phase B Reranker | FAIL / NOT ADOPTED |
| Phase C | PASS |
| Phase D | PASS |
| Phase E | FINAL PASS |
| Phase F.0 | PASS |
| Phase F.1 | PASS |
| Phase F.2 | PASS |
| Phase F.3 | PASS / DEFER_L2 |
| Phase F.4 | Engineering/Evaluation Closure PASS |
| Phase F.4.1 | PASS |
| Final Truthfulness Audit | FINDS_OVERCLAIM |
| Truthfulness Remediation | PASS |
| Quality Contract Freeze | PASS |
| Q1 | PASS |
| Q1.1 | PASS |
| Q2 | FAIL / ROLLED BACK |
| Q3 | PASS |
| Q3.1 | PASS |
| Q2.2 | INSUFFICIENT |
| Q4.0 | PASS |
| Q4.1 | SYNTHESIS_ONLY_INSUFFICIENT |
| Q4.2 | PASS |
| Q4.3a | NOT STARTED |
| Q4.3b | NOT STARTED |
| Q4.3c | NOT STARTED |
| Evaluator Matcher Review | NOT STARTED |
| Golden Contract Review | NOT STARTED |
| Final Product Quality Closure | NOT STARTED |

---

# 41. 已实现能力总清单

## Storage / Index

- [x] SQLite
- [x] Qdrant
- [x] FTS
- [x] Hybrid Retrieval
- [x] RRF

## Ingestion

- [x] document import
- [x] chunking
- [x] indexing
- [x] reimport
- [x] lifecycle

## Security

- [x] ImportPathPolicy
- [x] canonicalization
- [x] allowed roots
- [x] output sanitization

## Query

- [x] QA
- [x] Compare
- [x] Locate
- [x] Locate Chapter
- [x] Book TOC
- [x] Book Overview
- [x] Chapter Overview
- [x] Unsupported
- [x] Scope Gate
- [x] Multi-turn basic support

## Multi-document

- [x] cross-document retrieval
- [x] multi-document QA

## Summary

- [x] Section Summary
- [x] Document Summary
- [x] provenance
- [x] invalidation

## Citation

- [x] normalization
- [x] renumber
- [x] validity
- [x] scope
- [x] deterministic support
- [x] number/unit verification
- [x] CJK/Latin verification
- [x] reason codes
- [x] telemetry
- [x] high-confidence Gate PASS

## Evaluation

- [x] Phase E router Golden
- [x] F.2 citation Golden
- [x] F.3 semantic challenge
- [x] Final Golden 185
- [x] Answer eval 144
- [x] evaluator versioning
- [x] corrected baseline
- [x] Product Quality Contract

---

# 42. 已验证但未采用 / 未启用

- [x] Reranker：收益不足，默认关闭
- [x] Q2 Prompt Citation：失败，rollback
- [x] Q2.2 Citation Completion：模块保留，engine 未启用
- [x] L2 verifier：已评测，DEFER

---

# 43. Deferred 能力

- [ ] KB Summary
- [ ] Multi-document Summary
- [ ] Document/library metadata query
- [ ] Production L2 citation verifier
- [ ] Production deterministic citation completion
- [ ] richer citation coverage UI
- [ ] Performance SLA

---

# 44. 当前 P0 待办

## P0.1 — Q4.3a History Resolution

- [ ] `mt-003`
- [ ] `mt-006`
- [ ] pronoun resolution
- [ ] entity inheritance
- [ ] elliptical follow-up
- [ ] ambiguity fail-closed
- [ ] Phase E 66/66 保持
- [ ] Router 不扩大

## P0.2 — Q4.3b True Retrieval Miss

目标：

```text
qa-030
cmp-001
loc-018
```

检查：

- [ ] document retrieved
- [ ] section retrieved
- [ ] chunk retrieved
- [ ] top-k truncation
- [ ] sparse/dense miss
- [ ] scope filter
- [ ] query formulation

## P0.3 — Q4.3c Multi-document Document Identity

目标：

```text
md-014
```

需要：

- [ ] 定义 document metadata 是否作为 evidence
- [ ] document identity-aware QA
- [ ] 不伪造 chunk 内容

## P0.4 — Evaluator Fact Matcher Audit

- [ ] normalized lexical match
- [ ] abbreviation handling
- [ ] CJK surface-equivalence boundary
- [ ] false-positive safety
- [ ] 不与 Golden Review 混改

## P0.5 — Golden Contract Review

- [ ] Locate semantics
- [ ] `1.` vs `第1`
- [ ] query term repetition
- [ ] document identity
- [ ] abbreviation/full-name
- [ ] citation_negative semantics

---

# 45. Citation Coverage 后续路线

当前：

```text
0.5524 < 0.80
```

已经证明：

```text
Prompt-only = FAIL
unique-supported deterministic completion = INSUFFICIENT
```

后续潜在路线：

- [ ] L2-assisted Citation Decision
- [ ] multi-evidence semantic completion
- [ ] stronger answer model

当前建议：

```text
CITATION MAINLINE PAUSED
```

先关闭 Answer production defects。

---

# 46. Answer Quality 后续路线

推荐：

```text
Q4.3a History
→ Q4.3b Retrieval
→ Q4.3c Document Identity
→ Evaluator Matcher Audit
→ Golden Contract Review
→ Unified Full 144
```

---

# 47. 当前不建议做的事情

- [ ] 不继续加 Router 关键词
- [ ] 不先大改 Retriever
- [ ] 不恢复 Q4.1 completeness Prompt
- [ ] 不恢复 Q2 citation Prompt
- [ ] 不启用 Q2.2 Citation Completion
- [ ] 不降低 Product Quality Gate
- [ ] 不修改 Golden 迎合当前答案
- [ ] 不直接上宽松 fuzzy matcher
- [ ] 不直接实施 L2
- [ ] 不重开 reranker
- [ ] 不进入 Phase G

---

# 48. Product Quality 最终 DoD

只有以下五项全部通过：

```text
case_exact_fact_match_rate          >= 0.80
fact_recall                         >= 0.90
false_refusal_rate                  <= 0.03
citation_coverage                   >= 0.80
high_confidence_unsupported_rate    <= 0.05
```

才能：

```text
Product Quality DoD = PASS
```

当前：

```text
case_exact          FAIL
fact_recall         FAIL
false_refusal       PASS
citation_coverage   FAIL
high_conf           PASS
```

即：

```text
2 / 5 PASS
```

---

# 49. 当前项目最终状态

```text
Engineering Closure       = PASS
Evaluation Infrastructure = PASS
Quality Contract          = FROZEN v1.0
Quality Baseline          = FROZEN

Q1                        = PASS
Q1.1                      = PASS
Q2                        = FAIL / ROLLED BACK
Q3                        = PASS
Q3.1                      = PASS
Q2.2                      = INSUFFICIENT
Q4.0                      = PASS
Q4.1                      = SYNTHESIS_ONLY_INSUFFICIENT
Q4.2                      = PASS

Q4.3a                     = NOT STARTED
Q4.3b                     = NOT STARTED
Q4.3c                     = NOT STARTED

Product Quality DoD       = NOT_YET_PASS
V3 Release Readiness      = CONDITIONALLY_READY
```

---

# 50. 当前推荐下一授权

推荐下一步：

```text
Q4.3a — Multi-turn History / Reference Resolution
```

之后：

```text
Q4.3b — Retrieval
Q4.3c — Document Identity
Evaluator Fact Matcher Audit
Golden Contract Review
Final Unified 144-case Quality Evaluation
```

---

# 51. 最终原则

后续任何阶段必须坚持：

1. 每个 Workstream 单独授权；
2. 先 Preflight；
3. 不自动进入下一阶段；
4. production defect 与 evaluator defect 分开；
5. Golden defect 与 product defect 分开；
6. Prompt / Router / Retriever 不混改；
7. Citation 与 Answer Quality 不混改；
8. rollback 必须独立；
9. CI success 不代表 Product Quality PASS；
10. 不通过降低 Gate 宣布完成；
11. 不通过修改 Golden 宣布完成；
12. 只有完整 Product Contract 5/5 PASS 后，才允许：

```text
Product Quality DoD = PASS
V3 Release Readiness = READY
```
