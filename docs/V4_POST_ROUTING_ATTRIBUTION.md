# V4.6 — Post-Routing Residual Attribution & Priority Revalidation

> 模式：`READ-ONLY PRODUCT DIAGNOSIS`。本阶段**不修改任何 production / evaluator / Golden / Contract**。
> 目标：基于 post-V4.5 当前产品状态重新机械导出真实 residual failure set，解决
> Routing / Document Identity / Retrieval / History / Generation 的优先级关系，并**只推荐一个**下一实施 subsystem。

Parent baseline：`V4_5_ROUTING_BASELINE`（production `c36d61a1…`，`eval/v4_5_routing_baseline.json`）

---

## A. Workspace / Current Baseline

- V4 工作区无 `.git`；本阶段仅新增 attribution 脚本 / JSON / docs / tests。
- `eval/v4_initial_baseline.json`、`eval/v4_4_scope_remediation_baseline.json`、`eval/v4_5_routing_baseline.json`
  均未改动；`v4_baseline_lineage.json → current_baseline_id = V4_5_ROUTING_BASELINE`（V4.6 不改 product state）。
- 当前 canonical metrics（来自 `eval/v4_5_routing_baseline.json`）：
  `case_exact 0.7292 (105/144) · recall 0.8535 (268/314) · false_refusal 0.0000 · coverage 0.4783 · high_conf 0.0112 · invalid 0 · scope 0`。
- V3 / Publish 未触碰（Publish 工作树干净，`HEAD=117ebfa… tag v3-final`）。

## B. Post-V4.5 Failure Set（机械导出）

来源：`eval/v4_6_post_routing_evidence.json`（由 `V4_5_ROUTING_BASELINE` 的 production-hash-bound 答案缓存导出，
**不复用** V4.3 归因作为当前事实）。

```text
eligible_cases = 144
non_exact      = 39
failed_facts   = 46
by_category    = single_fact_qa 11 · locate 11 · compare 5 · multi_turn 5 · multi_document 4 ·
                 metadata_library 1 · citation_negative 2
```

## C. Current Routing Mismatches（全 185 例扫描）

```text
ROUTING_MISMATCH_TOTAL = 20
  UNDER_TRIGGER       = 2   (loc-009, loc-010)
  PRECEDENCE_CONFLICT = 18  (12 条 deferred-metadata 为设计内；其余为粒度/优先级)
```

**关键结论**：20 条 mismatch **没有任何 fact-loss 影响**——

- 12 条 `meta-*` 是冻结的 deferred-metadata（Phase F.4.1）→ route=unsupported，**全部 PASS**；
- 2 条 under-trigger（loc-009/010）当前 **均 PASS**，且若强行改路由会**丢 fact**（见 D）；
- 6 条 precedence/粒度（`loc-007/011/020`、`qa-015`、`cmp-013`、`md-003`、`oos-013`）答案仍正确。

→ **Routing 已收口，可离开；不是下一优先级。**

## D. loc-009 Deep Audit

```text
query           香农公式在书里的哪个部分？
expected_route  locate          current_route = qa（UNDER_TRIGGER）
current answer  材料1中提到了香农公式，具体位置如下[1]。   → 1/1 exact
expected_chapters [1,3]
```

- **Q1 TRUE ROUTING FAILURE?** 否（作为产品失败而言）。是 route mismatch，但当前 qa 答案 fact-complete（1/1），零 fact 损失。
- **Q2 route 正确性与 answer 完整性冲突?** **是**。分析型模拟（`forced_route=locate`，不改 production）：
  hypothetical locate answer = 位置清单（`3.3.1 扩频技术概述` 等），`hypothetical_facts_present=[]` → 丢 `香农`。
- **Q3 root cause?** `GOLDEN_CONTRACT_ISSUE`（primary）+ locate 确定性模板限制：golden 声明 `expected_route=locate`
  却要求内容 token `香农`，而位置模板结构性无法产出。router under-trigger 只是症状。

→ **归入 Measurement/Golden track，不是产品 routing 修复目标。**

## E. loc-010 Deep Audit

```text
query           均衡技术的相关章节是哪些？
expected_route  locate_chapter   current_route = qa（UNDER_TRIGGER）
current answer  材料1、2、3均提到了均衡技术…        → 1/1 exact
expected_chapters [1,2,3,4,5,7]
```

- 模拟 `forced_route=locate_chapter` → 返回**错误的文档**（`移动通信测试文档 / 2. 抗衰落技术`）且丢 `均衡`。
- **与 loc-009 机制不同**：loc-009 纯 golden/locate-模板契约；loc-010 额外有 document-identity/ranking 交互
  （top hit 是测试文档而非教材第 1–7 章）。→ **不捆绑**。

## F. md-004 Deep Audit（post-routing）

```text
route = qa（已修正）    facts = 1/3（缺 教材 / 测试文档）
answer = "分集接收在材料1、材料2和材料3中被提及"
```

- 两份文档均在 final context（测试文档 ctx[1..3]、`移动通信 (李兆玉)` ctx[4..5]）→ 不是 retrieval miss；
- 失败 fact 是**两个文档名**；答案用 `材料N` 索引而非标题。
- **primary = DOCUMENT_IDENTITY_FAILURE**（证据 framing 未给出真实标题），secondary = GENERATION。

## G. md-019 Deep Audit（post-routing）

```text
route = qa（已修正）    facts = 0/3
answer = "这个结论可以在多个文档中找到：材料1[1] 材料2[2] 材料3[3] 材料5[4]"
```

- `GSM / WCDMA / 多径` 三个 fact **全部 EVIDENCE_DELIVERED**，但答案只输出指针清单、不复述结论。
- **primary = GENERATION_SYNTHESIS_FAILURE**（证据已送达但答案省略），secondary = DOCUMENT_IDENTITY（材料N）。

## H. cit-001 Deep Audit（post-routing）

```text
route = qa（已修正）    facts = 0/1（缺 GMSK）
answer = "[材料1]"     （退化为裸引用标记）
```

- `GMSK EVIDENCE_DELIVERED`（在 final context），非 paraphrase 拒绝。
- **primary = GENERATION_SYNTHESIS_FAILURE**，secondary = CITATION（`请指出出处` 的引用诉求疑似诱导模型只输出引用）。

## I. mt-006 Deep Audit

```text
route = qa · referent=OFDM · rewrite="OFDM" · out_of_scope=False
retrieval = OFDM EVIDENCE_DELIVERED（final context #1 第6章 LTE基本传输方案）
answer = "材料不足，无法确定您指的是哪个概念或内容"（ANSWER_WITH_LIMITATION）
```

- **V4.4 的 "History residual" 标签不再成立**：rewrite 已正确解析为 OFDM 且证据已送达。
- **primary = GENERATION**（证据送达却拒绝作答），secondary = HISTORY（bare-term rewrite + referent 未注入 prompt 放大问题）。

## J. Product vs Measurement Separation

```text
MEASUREMENT_FAILURE = 17  （EVALUATOR 9 + GOLDEN_CONTRACT 8：locate 概念词复述契约 / 序数表达 / 释义边界）
PRODUCT_FAILURE     = 7   （DOCUMENT_IDENTITY 3 + GENERATION 3 + HISTORY 1）
MULTI_CAUSE         = 15  （RETRIEVAL 7 + GENERATION 8，各带 secondary）
```

17 条 measurement 是最单一大桶，但改的是**尺子**不是产品，且 V4.3 已证明大量 locate 低分是 Golden/evaluator 表达问题。

## K. Updated Dependency Graph

```text
document_identity ─▶ scope_resolution ─▶ routing ─▶ retrieval_ranking ─▶ generation_synthesis ─▶ citation_alignment
        │                    ▲                     ▲                        ▲
        └──▶ retrieval ◀─────┘                     └── history_rewrite ──────┘
golden_contract ─▶ evaluator_matcher   （尺子，产品链之外）
```

- routing：V4.5 已收口，剩余 mismatch 零 fact 影响 → 离开。
- document identity：retrieval/generation 的上游；给出真实标题即消除 `材料N` 家族并改善下游 context。

## L. Candidate Next-phase Comparison

| 候选 | 受影响 case/facts | 置信度 | 上游位置 | 隔离性 | 回归风险 | 裁定 |
|---|---|---|---|---|---|---|
| A Routing under-trigger | 0 facts | 高(确认) | 顶 | 高 | **高（强行改会丢 fact）** | 不推荐（fact-negative，归 measurement） |
| **B Document Identity** | 3 case / 5 facts | **高**（单一机制） | retrieval 前 | 高 | 低-中 | **推荐 Priority 1** |
| C Retrieval | 7 case / 8 facts | 中 | identity 后 | 中（retriever 冻结） | 中 | 待 identity 后 |
| D History | 1 case / 1 fact | 高 | retrieval 前 | 高 | 低 | Priority 2 |
| E Generation | 11 case / 12 facts | 中 | 末 | 低 | 中 | 上游修后重测 |
| F Golden/Evaluator | 17 case / 17 facts | 高 | 尺子 | 高 | 产品低（禁止注水） | 独立 measurement track |

## M. Re-prioritized Roadmap

```text
Priority 1       DOCUMENT_IDENTITY Remediation   （md-004 / md-009 / md-015，5 facts）
Priority 2       HISTORY Resolution             （mt-011，malformed rewrite）
Priority 3       RETRIEVAL（RRF ranking）        （cit-013/qa-020/qa-030/cmp-001/loc-008/013/015，8 facts）
Subsequent       GENERATION Completeness          （12 facts，上游修后重测）
Measurement-only GOLDEN_CONTRACT / EVALUATOR      （17 cases，独立尺子轨道，绝不注水）
Deferred         CITATION_ALIGNMENT
```

```text
RECOMMENDED_NEXT_PHASE = V4.7 — Document Identity Remediation
```

**为何是单一 subsystem**：`材料N→标题` 是跨 md-004/009/015 的**同一机制**（证据 framing 未给出真实文档标题），
3 case / 5 facts、上游、高置信、单点可隔离；不捆绑 Retrieval 或 Generation。

## N. Artifacts / Tests

```text
scripts/analyze_v4_6_post_routing_attribution.py   READ-ONLY 证据收集器（144 例 prepare + 185 例 route 扫描 + 文档清单）
scripts/build_v4_6_post_routing_attribution.py     归因构建器（含 loc-009/010 analysis-only 路由模拟）
eval/v4_6_post_routing_evidence.json               机械证据（parent/cases/route_scan/library_identity）
eval/v4_6_post_routing_attribution.json            最终归因（failure set + deep audits + priority + gates）
docs/V4_POST_ROUTING_ATTRIBUTION.md                本阶段文档
tests/test_v4_6_post_routing_attribution.py        归因完整性测试
```

## O. Gate Results

```text
G1  post-V4.5 failure set reproduced        PASS (39)
G2  routing mismatches enumerated           PASS (20)
G3  loc-009 route-vs-answer conflict resolved PASS
G4  loc-010 independently attributed        PASS
G5  md-004 independently attributed         PASS
G6  md-019 independently attributed         PASS
G7  cit-001 independently attributed        PASS
G8  mt-006 independently attributed         PASS
G9  product vs measurement separated        PASS (17 measurement / 7 product / 15 multi)
G10 dependency graph updated                PASS
G11 one unambiguous next subsystem          PASS
G12 no independent subsystems bundled       PASS
G13 production behavior unchanged           PASS
G14 Golden/evaluator/Contract unchanged     PASS
G15 historical baseline artifacts unchanged PASS
G16 V3/Publish untouched                    PASS
```

## P. Decision

```text
V4_6_POST_ROUTING_ATTRIBUTION = PASS
READY_FOR_NEXT_V4_REMEDIATION_AUTHORIZATION
RECOMMENDED_NEXT_PHASE = V4.7 — Document Identity Remediation
```

本阶段到此停止；未开始任何 Routing / Document Identity / Retrieval / History / Generation / Citation / Golden 修复，
未对 Publish 做 sync / commit / tag / push。
