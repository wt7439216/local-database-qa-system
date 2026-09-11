# V4.5 — Routing Over-trigger Remediation

> 目标：**移除已被证明的 locate routing over-trigger**，使真实 QA / document / citation 语义的问题不再因为表面出现
> 「在哪」「出处」而错误进入 deterministic `locate` route；同时严格保持真正 locate / locate_chapter 查询不退化。
> Gate = **routing error removed**，**不是** answer-exact / 全量指标达标。

Parent baseline：`V4_4_SCOPE_REMEDIATION_BASELINE`（production `dc35c6eb…`）
Stage baseline：`V4_5_ROUTING_BASELINE`（production `c36d61a1…`，`eval/v4_5_routing_baseline.json`）

---

## 1. Root cause（改动前机械确认）

`core/query_router.py::classify_route()` 对 `LOCATION_WORDS` 做**无条件子串命中**：

```python
if any(word in normalized for word in LOCATION_WORDS):
    return "locate"
```

`LOCATION_WORDS` 同时含 `"在哪"` 与 `"出处"`，而 `"在哪"` 是 `"在哪些文档"` / `"在哪个文档"` 的子串。
冻结的 V4.3 attribution evidence（pre-patch `actual_route`）实测：

| case | query | 命中词 | pre-patch route | golden expected_route | route_matches |
|---|---|---|---|---|---|
| md-004 | 分集接收在哪些文档中被提到？ | `在哪`（← `在哪些文档`） | `locate` | `qa` | False |
| md-019 | GSM 和 WCDMA 需要对抗多径衰落，这一结论在哪个文档中？ | `在哪`（← `在哪个文档`） | `locate` | `qa` | False |
| cit-001 | GSM 使用 GMSK 调制，请指出出处。 | `出处` | `locate` | `qa` | False |
| cit-007 | 循环前缀的作用？请引用出处。 | `出处` | `locate` | `qa` | False |

`route_precedence`：`book_toc > deferred_metadata > compare > chapter_overview > book_overview > locate_chapter > locate > qa`。
四例均无任何上游分支命中，因此全部由 `LOCATE_PATTERN` 决定；locate 模板只输出位置清单
（`engine_v2.answer()` 的 `route == "locate"` 分支），**无法完成**原本的 document-identity / provenance 任务。

归因结论：`ROUTING`（非 Scope / Retrieval / Document Identity / Generation / Citation / Golden / Evaluator）。

---

## 2. Design alternatives

| 方案 | 判定 | 原因 |
|---|---|---|
| A. 对 `LOCATION_WORDS` 命中增加**意图语义判定**（选中） | ✅ | 单点、只改 routing 决策、可泛化 |
| B. 直接从 `LOCATION_WORDS` 删除 `"在哪"` / `"出处"` | ❌ | `LOCATION_WORDS` 同时被 `clean_location_query()` 消费（locate 答案脚手架），会改动 retrieve 查询构造 |
| C. 删除词条中的全部位置词 | ❌ | 会伤及真实 locate（`多径衰落在哪一页` / `哪里` / `第几节`） |
| D. 对命中处加入 `if case_id == …` / `if query == golden` | ❌ | 违反最小改动与泛化要求 |
| E. 重写 router / 引入 LLM 意图分类 | ❌ | 超范围，破坏确定性 |

---

## 3. Selected minimal fix

**仅 1 个 production 文件、1 处语义决策：`core/query_router.py`。**

1. `LOCATION_WORDS` / `CHAPTER_LOCATION_WORDS` **词表本身不变** → `engine_v2.clean_location_query()` 的行为逐字节不变。
2. 新增 `is_location_intent()`，并在 `classify_route()` 中用其替换原来的无条件子串命中：

```python
_PROVENANCE_WORDS = ("出处", "来源")
_LOCATION_NON_POSITION_WORDS = ("在哪",) + _PROVENANCE_WORDS
_QUANTIFIERS = "些个本几一份种册套"
_POSITION_CONTEXT = re.compile(rf"哪[{_QUANTIFIERS}]{{0,3}}(?:页|章|节|位置|地方|里)")
_CONTAINER_CONTEXT = re.compile(rf"在哪[{_QUANTIFIERS}]{{0,2}}(?:文档|文件|书|教材|资料|文献|知识库|图书|书籍)")

def is_location_intent(question: str) -> bool:
    value = normalize_query(question)
    if _POSITION_CONTEXT.search(value):          # 在哪一页 / 哪个位置 / 哪里
        return True
    if any(w in value for w in LOCATION_WORDS if w not in _LOCATION_NON_POSITION_WORDS):
        return True                              # 第几节 / 找一下 / 什么地方 …
    if _CONTAINER_CONTEXT.search(value):         # 在哪些文档 / 在哪个文档 / 在哪本书
        return False
    if any(w in value for w in _PROVENANCE_WORDS):  # 出处 / 来源
        return False
    return "在哪" in value                       # 裸 "在哪" 仍是位置意图
```

语义：`LOCATION_WORDS` 只表示**词法出现**；进入 `locate` 需要**位置意图**。
「`在哪` + 文档/集合容器」= 问*哪一份文档*（document identity，`qa`）；「`出处` / `来源`」= 问*出处/引用*
（citation 子系统在 `qa` 轨道回答）；二者都不是位置请求。

**为何安全**：
- 位置单元集合刻意只收 §12 授权的真实表达（页 / 章 / 节 / 位置 / 地方 / 里），因此
  「香农公式在书里的哪个部分？」（`loc-009`，pre-patch 本来就 **under-trigger 到 qa**，属授权外的另一种缺陷）
  **保持不变**，diff 严格限定在 over-trigger 移除。
- 上游分支（`book_toc` / `deferred_metadata` / `compare` / `chapter_overview` / `book_overview` / `locate_chapter`）
  未被触碰 → 由上游分支决定的问题 before == after（机械论证）。
- `locate` 的**检索参数**（`top_k` / `include_front_matter` / exact-term 重排）由 route 选择，未改动任何 retrieval 代码。

---

## 4. Production diff

| file | symbol | before | after |
|---|---|---|---|
| `core/query_router.py` | `is_location_intent()`（新增）/ `classify_route()` | `any(word in normalized for word in LOCATION_WORDS)` → `locate` | `is_location_intent(normalized)` → `locate` |

- `production_source_sha256`：`dc35c6eb…`（V4.4） → `c36d61a1…`（V4.5）
- 非 production 新增：`scripts/eval_v4_routing_remediation.py`、`tests/test_v4_routing_remediation.py`、
  `docs/V4_ROUTING_REMEDIATION.md`、`eval/v4_5_routing_baseline.json`、`eval/v4_routing_remediation.json`
- `diff_scope = ROUTING_ONLY`
- 机械证据：全量 185 golden 的 route 表中**只有 4 个 case 发生变化**（即四个 target），其余 0 变化。

---

## 5. 四个 target before / after

| case | route before → after | answer_state | facts before | facts after | residual |
|---|---|---|---|---|---|
| md-004 | `locate` → `qa` | ANSWERED | 1/3 | 1/3 | DOCUMENT_IDENTITY/COVERAGE（未同时点名两份文档） |
| md-019 | `locate` → `qa` | ANSWERED | 1/3 | 0/3 | RETRIEVAL/GENERATION |
| cit-001 | `locate` → `qa` | ANSWERED | 0/1 | 0/1 | GENERATION（未复述 GMSK） |
| cit-007 | `locate` → `qa` | ANSWERED | 0/1 | **1/1（exact）** | 无 |

```text
routing_error_removed = 4/4
```

四个 target **不要求** exact answer；暴露的下游残差按授权**只记录、不继续修**。

---

## 6. Genuine locate regression

`eval/v4_routing_remediation.json → genuine_locate_controls`：

```text
expected_locate_total (golden expected_route ∈ {locate, locate_chapter}) = 20
correct_route_before = 18
correct_route_after  = 18
NEW_GENUINE_LOCATE_MISROUTES = 0            ✅
```

外加 16 条真实表达控制（`多径衰落在哪一页` / `哪里` / `第几节` / `哪个位置` / `多径衰落在什么地方` /
`OFDM在哪一章` / `扩频技术在哪个章节` …）全部仍为 `locate` / `locate_chapter`。
未变动的 pre-existing 差异（`loc-007` / `loc-011` / `loc-020` 的 `locate` vs `locate_chapter` 细分、
`loc-010` 的 under-trigger）均为 **pre-existing**，未因本阶段恶化。

---

## 7. Ambiguous / adversarial routing

| query | 期望 primary intent | route after | 说明 |
|---|---|---|---|
| OFDM在哪本书里有介绍？ | qa（哪一份文档介绍） | `book_overview` | 由上游 `book_overview` 分支决定（`本书`+`介绍`），V4.5 前后一致；属**既有** book_overview over-trigger，本次未改 |
| 这个结论的出处是什么？ | qa（provenance） | `qa` | ✅ |
| 书中在哪解释了这个公式为什么成立？ | locate（位置） | `locate` | ✅ 未被 QA 吞掉 |
| 在哪里可以看到它的定义？ | locate（位置） | `locate` | ✅ |
| 分集接收在哪些文档中被提到？ | qa（document coverage） | `qa` | ✅ |
| 这一结论在哪个文档中？ | qa（document identity） | `qa` | ✅ |

`ambiguous-query behavior = no regression`（Phase E ambiguous 8 例仍 0 例被误解析）。

---

## 8. V4.4 Scope/OOS regression

```text
PURE_OOS_TOTAL=7        PURE_OOS_REFUSED=7        PURE_OOS_FALSE_ACCEPT=0     ✅
SEMANTIC_TRAP_TOTAL=22  SEMANTIC_TRAP_ACCEPTED=22 SEMANTIC_TRAP_NEWLY_REFUSED=[] ✅
loc-018 out_of_scope=False  ✅   mt-006 out_of_scope=False  ✅   md-014 out_of_scope=False ✅
scope_leakage = 0                                                                ✅
```

V4.5 **未修改** Scope/OOS production 行为（`dense_only`、阈值、分支语义均未触碰）。

## 9. Phase E regression

```text
cases=108  route accuracy=1.0000  follow-up=1.0000 (n=66)
ambiguous false-resolution=0.0000 (n=8)  scope conflict=10/10  engine scope leakage=0
Phase E eval gate: PASS
```

## 10. Citation safety

```text
Phase F.2 citation eval: 37/37 PASS（invalid=0 / scope violation=0）
```

---

## 11. Full test results

```text
targeted V4.5 routing tests        OK
tests/test_query_router.py         OK
tests/test_query_rewrite.py        OK
Phase E evaluator                  PASS
V4.4 Scope/OOS unit regression     OK
V4.4.1 lineage / attribution tests OK
full unittest                      615 OK (skipped=26)
ruff                               All checks passed!
compileall                         clean
```

> `tests/test_v4_baseline_lineage.py` 的 current-pointer 断言由硬编码 `V4_4_SCOPE_REMEDIATION_BASELINE`
> 改为**结构性**断言（`current_baseline_id == baselines[-1].baseline_id`）。这是 governance pointer 前移所需的
> 测试口径更新，**不是** Gate 下调 / Golden 修改 / evaluator 修改；其不可变性断言（initial baseline immutable、
> status、hash 一致）全部保留。

---

## 12. Full-144 canonical evaluation

| Metric | V4.4 (parent) | V4.5 (stage) | Δ |
|---|---:|---:|---:|
| case_exact_fact_match_rate | 0.7222 (104/144) | **0.7292 (105/144)** | +0.0070 |
| fact_recall | 0.8535 (268/314) | 0.8535 (268/314) | 0.0000 |
| false_refusal_rate | 0.0000 | 0.0000 | 0 |
| citation_coverage | 0.4690 | 0.4783 | +0.0093 |
| high_confidence_unsupported_rate | 0.0134 (7) | 0.0112 (6) | −0.0022 |
| invalid_citation_count | 0 | 0 | 0 |
| citation_scope_violation | 0 | 0 | 0 |

```text
overall metric improvement   = NOT A V4.5 PASS CONDITION
case_exact +1                = cit-007 由 0/1 转为 1/1（route 修正后 exact）
fact_recall paired delta     = md-019 −1 / cit-007 +1 → net 0
                               （paired_fact_delta：142 个非 target case 的 fact_present 逐案完全一致）
citation_coverage delta      = NOT_CAUSALLY_ATTRIBUTED_WITHIN_V4_5（未做严格 paired citation 归因）
CITATION_SAFETY              = PASS（invalid=0 / scope=0）
```

---

## 13. Residual failures（本阶段只记录，不修）

```text
md-004   DOCUMENT_IDENTITY / multi-document coverage residual（未同时点名两份文档）
md-019   RETRIEVAL / GENERATION residual（expected facts 未被复述）
cit-001  GENERATION residual（未复述 GMSK）
loc-009  PRE_EXISTING locate UNDER-trigger（「哪个部分」；授权外，刻意保持不变）
loc-010  PRE_EXISTING routing residual（未变化）
OFDM在哪本书里有介绍？  PRE_EXISTING book_overview over-trigger（未变化）
```

---

## 14. Baseline lineage

```text
V4_INITIAL_BASELINE                  eval/v4_initial_baseline.json                IMMUTABLE_HISTORICAL
        ↓
V4_4_SCOPE_REMEDIATION_BASELINE       eval/v4_4_scope_remediation_baseline.json   IMMUTABLE_STAGE
        ↓
V4_5_ROUTING_BASELINE                 eval/v4_5_routing_baseline.json             CURRENT_PRODUCT_STATE
```

- `eval/v4_baseline_lineage.json → current_baseline_id = V4_5_ROUTING_BASELINE`
- `eval/v4_initial_baseline.json` 文件 sha256 = `371506a9…`（与 V4.4.1 记录一致，**未被改写**）
- `eval/v4_4_scope_remediation_baseline.json` **未被改写**（mtime 与 stage_identity 均未变）
- `eval/v3_final_golden.json` sha256 = `31a68507…`（未变）

---

## 15. Gate results

```text
G1  pre-patch root cause mechanically demonstrated      PASS
G2  md-004 route over-trigger removed                   PASS
G3  md-019 route over-trigger removed                   PASS
G4  cit-001 route over-trigger removed                  PASS
G5  cit-007 route over-trigger removed                  PASS
G6  no new genuine locate misroutes                     PASS (0)
G7  Phase E routing regression                          PASS
G8  ambiguous-query behavior no regression              PASS
G9  V4.4 Scope/OOS regression                           PASS
G10 pure-OOS false_accept remains 0/7                   PASS
G11 scope leakage remains 0                             PASS
G12 citation safety remains PASS                        PASS
G13 production diff limited to routing                  PASS
G14 Golden / evaluator / Contract / schema unchanged    PASS
G15 historical baseline artifacts unchanged             PASS
G16 V4.5 creates a new child baseline                   PASS
G17 V3 / Publish untouched                              PASS
```

机器可读证据：`eval/v4_routing_remediation.json → gate_results`。

---

## 16. Decision

```text
V4_5_ROUTING_REMEDIATION = PASS
```

## 17. Re-prioritized next phase（仅建议，等待单独授权）

V4.5 完成后重新导出 failure set（`eval/v4_routing_remediation.json` + 最新 144 行答案），
`Document Identity` 与 `Retrieval` 的证据强度高于 History / Generation：

```text
RECOMMENDED_NEXT_PHASE = V4.6 Document Identity / Retrieval Remediation（md-004 / md-019 已暴露该残差）
```

`md-004` 在 route 修正后暴露 document-identity/coverage 残差，`md-019` 暴露 retrieval/generation 残差 ——
二者必须先以 V4.5 后的新失败集重新做逐 case 归因，**不得**机械沿用旧 priority。
