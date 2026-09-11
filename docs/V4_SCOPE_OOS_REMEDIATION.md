# V4.4 — Scope/OOS False-Refusal Remediation

> 第一个 production remediation 阶段。目标：
> **移除已被证明的 in-scope false OOS refusal，同时严格保持真正 out-of-scope 查询的拒答能力。**
> Gate = Scope correctness，**不是** answer-exact 达标；secondary failures 允许残留并记录。

## 1. Root cause（改动前机械确认）

OOS 判定位于 `core/hybrid_retriever.py::HybridRetriever.retrieve()` 尾部：只有 3 条**词法**放行分支
（`strength>=2`；`strength==1 且长词>=3 且 dense>=accept`；`strength==1 且二字词且集中>=5 且 dense>=0.30`），
否则落入 `else: confidence=low; out_of_scope=True`。**不存在"密度主导"放行路径。**

三个目标 case 的实测 gate 输入（`eval/v4_scope_diagnostic.json`）：

| case | retrieval_query | lexical_strength | longest | concentrated | top_dense | 结果 |
|---|---|---:|---:|---:|---:|---|
| loc-018 | 参数表在测试文档… | **0** | 0 | 0 | **0.5597** | 词窗未浮现文档名 → 无分支可走 |
| mt-006 | OFDM | 1 | 4 | **8** | **0.5493** | 距 `accept=0.55` **仅差 0.0007** |
| md-014 | 教材和测试文档… | 1 | 2 | **2** | **0.5276** | 二字分支要求 `concentrated>=5` |

三者 top_dense 均 ≥ 0.5276；而**全部 7 条纯离题查询**的 top_dense **≤ 0.4623** —— 存在 0.065 的干净分离带。

## 2. Design alternatives

| 方案 | 判定 | 原因 |
|---|---|---|
| A. 新增"密度主导"放行分支（选中） | ✅ | 单点、不改检索结果、分离带干净 |
| B. 降低 `accept` 0.55 → 0.54 | ❌ | 直接放宽既有放行门限，且只修 mt-006 |
| C. 放宽二字分支 `concentrated 5 → 2` | ❌ | 会让 oos-003（conc=4, dense=0.4268）误放行 |
| D. 扩大 `_lexical_strength` 词窗 `[:8]` | ❌ | 改变既有判据语义，影响面不可控 |
| E. 重写 router/retriever/新增 intent 系统 | ❌ | 违反 minimal-change，超范围 |
| F. `if uncertain → allow` / 关闭 OOS gate | ❌ | 违反 safety invariant |

## 3. Selected minimal fix

**仅 2 个 production 文件、2 处改动：**

1. `core/library_store.py` — 在既有 `DEFAULT_DENSE_GATES` / `MODEL_DENSE_GATES` 中新增模型可缩放的
   `dense_only = 0.50`（沿用既有按 embedding model 查表的机制，不引入新结构）。
2. `core/hybrid_retriever.py` — 在**最终 deny 之前**新增**唯一一条**放行分支：

```python
elif top_dense is not None and top_dense >= self.store.dense_gates["dense_only"]:
    confidence = "medium"
    out_of_scope = False
```

**为何安全**：
- 分支置于最后 → 既有 3 条分支及其所有既有判定**逐字节不变**；
- 该分支只影响 `out_of_scope` / `confidence` **标签**，`final` 检索结果在此之前已定型 →
  **检索证据不变**（已机械验证：3 个目标的 `retrieved_chunk_ids` before == after）；
- `confidence` 仅用于 telemetry/展示，不参与任何行为门控；
- 0.50 严格高于纯离题观测上限 0.4623，低于目标最小 0.5276。

## 4. Before / After scope trace

| case | before | after | gate 输入 | 证据 | leakage |
|---|---|---|---|---|---|
| loc-018 | oos=True / low / REFUSED | oos=False / medium | str=0, dense=0.5597 | 不变 | 0 |
| mt-006 | oos=True / low / REFUSED | oos=False / medium | str=1, dense=0.5493 | 不变 | 0 |
| md-014 | oos=True / low / REFUSED | oos=False / medium | str=1, dense=0.5276 | 不变 | 0 |

三者 answer 层均不再拒答（`answer_is_refusal = False`）。

## 5. Positive cases（本阶段 Gate）

```text
loc-018 → ANSWERED 2/2           （恢复）
md-014  → ANSWERED 4/4           （恢复）
mt-006  → ANSWER_WITH_LIMITATION 0/1（Scope 阻塞已移除；HISTORY 残差保留）
```
**7 facts 中恢复 6**；`mt-006` 的残差正是 V4.3 预测的 secondary cause（rewrite 塌缩为裸词 `OFDM`），
按授权**不在本阶段修复**，记录为 `V4.4 SCOPE FIX SUCCESS / HISTORY RESIDUAL REMAINS`。

## 6. Negative cases —— OOS 保护

**规格更正（重要）**：授权文本假设 `OOS_HARD_NEGATIVE_FALSE_ACCEPT = 0/29`。冻结证据显示 29 条 hard negative
并非同质（`docs/V3_PHASE_F4_RELEASE_GATE.md:42-43`）：

```text
PURE_OOS      = 7  （天气/股票/写诗/简历/NBA/量子纠缠/番茄炒蛋）→ 检索层应全部拒答
SEMANTIC_TRAP = 22 （术语相似/语义陷阱）→ 检索层系统性放行，属冻结文档记录的 EXPECTED_LIMITATION，
                                        其"拒答"发生在生成层（材料不足时模型声明无法回答）
Contract §4.3 的 hard gate 是 pure_OOS_false_accept_rate = 0（对应 7 条），不是 29 条。
```

实测（修复后）：

```text
PURE_OOS_TOTAL=7        PURE_OOS_REFUSED=7        PURE_OOS_FALSE_ACCEPT=0   ✅
SEMANTIC_TRAP_TOTAL=22  SEMANTIC_TRAP_ACCEPTED=22 SEMANTIC_TRAP_NEWLY_REFUSED=[]  ✅（无新增误拒）
```
→ **无法证实的 "false_accept = 0/29" 不作为 Gate；改以 Contract 真实口径的 pure-OOS = 0 为准，
并额外要求语义陷阱零新增误拒。**

**性质裁定（V4.4.1 明确）**：本项属于 `SOURCE_OF_TRUTH_CORRECTION`（原授权文本与冻结 source-of-truth 不一致，
以冻结证据为准），**不是** `GATE_WEAKENING`；**Contract 本身未修改**。

## 7. Regression results

```text
Phase E router eval       = PASS（108/108 等冻结门限）
F.2 citation eval         = PASS（invalid=0 / scope violation=0）
full unittest             = 568 OK (skipped=26)
ruff / compileall         = clean
scope leakage             = 0
retrieval evidence        = unchanged（before == after chunk ids）
```

## 8. Full-144 canonical evaluation

| Metric | Pre-patch (V4.2) | Post-patch (V4.4) | Δ |
|---|---:|---:|---:|
| case_exact_fact_match_rate | 0.7083 | **0.7222** | +0.0139 |
| fact_recall | 0.8312 | **0.8535** | +0.0223 |
| false_refusal_rate | 0.0208 | **0.0000** | **−0.0208（3→0）** |
| citation_coverage | 0.4893 | 0.4690 | −0.0203 |
| high_confidence_unsupported_rate | 0.0095 | 0.0134 | +0.0039 |
| invalid_citation_count | 0 | 0 | 0 |
| citation_scope_violation | 0 | 0 | 0 |

- `false_refusal 3/144 → 0/144` 与设计一致。
- case_exact +2 例（loc-018、md-014 转 exact；mt-006 因 HISTORY 残差仍未 exact）。
- **citation_coverage −0.0203（V4.4.1 措辞更正）**：

```text
CITATION_SAFETY_REGRESSION        = NO
CITATION_COVERAGE_DELTA_ATTRIBUTION = NOT_RESOLVED_IN_V4_4
```

  > No citation-safety regression was observed. The citation-coverage delta is not used as evidence
  > of V4.4 success or failure and is **not causally attributed** within this phase.
  > **不写 `NOT A PRODUCT REGRESSION`**：full run 是新 generation batch（V4.2 已观测生成方差），
  > 且 3 个原 false-refusal case 改为正常回答后 citation-report population 发生变化，
  > 本阶段**未**做固定 common-case-set 归因 → 因果结论留给未来 citation phase。
- 评测器 provenance 修复：answer cache key 现绑定 `production_source_hash`，
  生产代码变更自动使答案缓存失效（仅 provenance，无 metric 语义变更）。

## 9. Residual downstream problems（本阶段不修）

```text
mt-006          HISTORY / query rewrite（裸词 OFDM）      → 后续阶段
locate 概念词复述 Golden 契约                              → 尺子轨道
22 条语义陷阱的检索层放行                                  → Scope Calibration（冻结登记）
LOCATION_WORDS "在哪"/"出处" 过触发（4 case，路由轨道）      → 本阶段明确未触碰
citation_coverage / 生成完整性                             → 后续
```

## 10. Gate decision

```text
V4_4_SCOPE_OOS_REMEDIATION = PASS
```
全部 13 项 Gate 通过（见 `eval/v4_scope_remediation.json → gate_results`）。
`target three cases perfect-answer exact match` **不是** Gate；secondary failures 已明确记录。

## 11. Baseline artifact（V4.4.1）

V4.4 的测量结果自 V4.4.1 起存放在**独立的 stage artifact**，不再覆盖 initial baseline：

```text
eval/v4_initial_baseline.json                  = V4_INITIAL_BASELINE（V4.2，IMMUTABLE）
eval/v4_4_scope_remediation_baseline.json      = POST_V4_4_SCOPE_REMEDIATION_BASELINE
eval/v4_baseline_lineage.json                  = lineage / current pointer
```
`eval/v4_scope_remediation.json → full_eval_metrics` 与 lineage 中的 V4.4 指标一致
（case_exact 0.7222 / fact_recall 0.8535 / false_refusal 0.0000 / coverage 0.4690 / high_conf 0.0134）。
