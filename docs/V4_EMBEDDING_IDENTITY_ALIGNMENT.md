# V4.6.1 — Embedding Identity & Model Alignment（Formalization）

> 本阶段**不是**新的 product remediation，也**不是** V4.7 的替代。它把已经存在、已审计通过的
> `bge-m3 / Embedding Identity` production state 正式纳入 V4 baseline lineage，恢复
> **live production 与 canonical measurement state 的一致性**。
> Gate = `MEASUREMENT_INTEGRITY_RESTORED`，**不是** product quality 达标。

Parent baseline：`V4_5_ROUTING_BASELINE`（production `c36d61a1…`，`eval/v4_5_routing_baseline.json`）
Stage baseline：`V4_6_1_EMBEDDING_IDENTITY_BASELINE`（production `7216c885…`，`eval/v4_6_1_embedding_identity_baseline.json`）
Evidence：`eval/v4_6_1_embedding_identity_formalization.json`

---

## 1. 背景：为什么会有这一阶段

V4.5 之后，一组**未登记进 lineage** 的 production 改动（`core/config.py`、`core/library_store.py`、
`core/engine_v2.py` 及配套 `.env.example` / docs / build / tests）把 embedding 生产模型从
“配置默认 `nomic-embed-text`” 对齐到 “库中真实存在的 `bge-m3`”，并新增启动期 fail-closed 身份校验。

该 change-set 经 `KB-V4 — Out-of-Band Embedding Change Audit` 判定为：

```text
COHERENT_COMPLETE_CHANGESET / EXISTING_VECTOR_DATA_SAFE = YES /
SCOPE_SEMANTICS_CHANGED = NO / V4_5_ROUTING_TOUCHED = NO / LIKELY_INTENTIONAL
```

但 `production_source_hash` 已由 `c36d61a1…` 变为 `7216c885…`，而 lineage 的 current pointer 仍指向
`V4_5_ROUTING_BASELINE` → **measurement integrity 失效**。V4.6.1 负责正式收编。

## 2. 为什么 default 从 `nomic-embed-text` 改到 `bge-m3`

- 真实库（`data/library/documents.sqlite3`、`textbooks.sqlite3`）中的向量**一直都是 bge-m3 / 1024 维**。
- 查询期嵌入使用 **库记录模型**（`engine_v2.py`：`self.ollama.embed(query, model=self.library.embedding_model)`），
  因此检索路径早已是正确的；`config.EMBEDDING_MODEL` 只是未显式传 model 时的 fallback 与**摄入默认值**。
- 旧 default（`nomic-embed-text` / 768 维）属于误导性遗留：向既有 bge-m3 库导入会命中
  `core/importer.py` 的“知识库嵌入模型不匹配”报错；对新库则会建成 768 维。
- 修正后四层一致：`CONFIG DEFAULT = ENV EXAMPLE = INSTALLED MODEL = STORED MODEL = bge-m3`。

## 3. 模型架构

```text
query → bge-m3 (1024) → 向量/hybrid 检索 → （可选 reranker，默认关闭） → qwen2.5:7b → answer / citation verification
```

```text
ANSWER_MODEL        = qwen2.5:7b
EMBEDDING_MODEL     = bge-m3
VECTOR_BACKEND      = sqlite
RERANKER_ENABLED    = false
```

## 4. Existing DB 的真实 identity

| DB | documents | chunks | embeddings | model | dimension |
|---|---:|---:|---:|---|---:|
| `data/library/documents.sqlite3` | 6 | 637 | 637 | `bge-m3` | 1024 |
| `data/library/textbooks.sqlite3` | 1 | 617 | 617 | `bge-m3` | 1024 |

- `metadata.embedding_model = bge-m3`、`metadata.embedding_dimension = 1024`。
- `embeddings` 表 `(model, dimension)` 唯一 = `(bge-m3, 1024)`；向量 blob = 4096 B（= 1024 × 4 B）。
- **现有 embeddings 就是 bge-m3**（identity 相符，非仅维度相符）→ `EXISTING_VECTOR_DATA_SAFE = YES`。

## 5. Fail-closed 启动校验

`core/library_store.validate_embedding_identity(stored_model, stored_dimension, *, configured_model, has_vectors)`
在 `StructuredQAEngine.__init__`（`LibraryStore` 之后、创建 Ollama 客户端之前）**一次**执行：

```text
configured_model (QA_EMBEDDING_MODEL) 必须等于 stored_model
stored_dimension 必须等于 stored_model 注册的期望维度   （bge-m3 → 1024 / nomic-embed-text → 768）
```

- 违反 → 抛 `EmbeddingIdentityError`，**拒绝启动**（不再静默用别的模型的索引检索）。
- `has_vectors == false`（无稠密索引）→ 跳过。
- stored model 无注册 profile（未知/legacy/测试合成模型）→ **不判**，保持既有契约测试可用。

Empty / legacy 行为：

| 场景 | 行为 |
|---|---|
| 空库 / 新库 | `has_vectors=false` → 跳过；首次默认导入把库 pin 成 `bge-m3 / 1024` |
| legacy `nomic-embed-text` / 768 库 | 显式设置 `QA_EMBEDDING_MODEL=nomic-embed-text` 时通过；配置为 bge-m3 则拒绝启动 |
| 维度不符（如 bge-m3 库 768 维） | 拒绝启动 |

## 6. 不变量（无副作用）

```text
no auto re-embed
no silent model switching
no SQLite / Qdrant writes
no Qdrant rebuild
```

`LibraryStore` 与其 SQLite 向量后端以 `mode=ro` 打开；`LibraryStore`/`SQLiteVectorStore` 的写路径需显式
`read_only=False`。本阶段结束时 `documents.sqlite3` SHA256 前后一致、无 `-wal`/`-shm`。

## 7. Scope gates unchanged

```text
strong     = 0.48
accept     = 0.55
dense_only = 0.50
```

`DEFAULT_DENSE_GATES` 与 `MODEL_DENSE_GATES["bge-m3"]` 与 V4.4 冻结值逐项相同；V4.5 已冻结的
`core/query_router.py` 不在变更文件内。机械复核（本阶段）：

```text
SCOPE_SEMANTICS_CHANGED = NO
V4_5_ROUTING_TOUCHED    = NO
pure_OOS_false_accept   = 0 / 7
scope_leakage           = 0
SEMANTIC_TRAP_NEWLY_REFUSED = []
V4.5 routing targets still locate = []
```

## 8. SQLite / Qdrant compatibility

- SQLite：默认后端；既有 637 / 617 条 bge-m3/1024 向量可直接加载（引擎启动校验通过）。
- Qdrant：`general_documents (637 pts / 1024 / Cosine)`、`local_knowledge_chunks (617 pts / 1024 / Cosine)`，
  与 bge-m3/1024 兼容。
- 已知可选加固（**本阶段未实现，避免扩大 production change-set**）：启动校验以 SQLite metadata 为权威，
  未同时读取 Qdrant collection 的 vector size。

## 9. Full-144 canonical 评测（新 production hash）

在 `production_source_hash = 7216c885…` 上重跑 canonical full-144（旧 `…prodc36d61a1…` 答案缓存**不复用**）：

| Metric | V4.5 (`c36d61a1`) | V4.6.1 (`7216c885`) | Δ |
|---|---:|---:|---:|
| case_exact_fact_match_rate | 0.7292 | **0.7292** | 0.0000 |
| fact_recall | 0.8535 (268/314) | **0.8535** (268/314) | 0.0000 |
| false_refusal_rate | 0.0000 | **0.0000** | 0.0000 |
| citation_coverage | 0.4783 | **0.4657** | −0.0126 |
| high_confidence_unsupported_rate | 0.0112 | **0.0132** | +0.0020 |
| invalid_citation_count | 0 | **0** | 0 |
| citation_scope_violation | 0 | **0** | 0 |

```text
CITATION_COVERAGE_DELTA_ATTRIBUTION = NOT_RESOLVED_IN_V4_6_1
```

- 新 full-144 是**新的随机生成批次**（answer cache 因 production hash 变化而失效），
  case_exact / fact_recall / false_refusal 逐项复现，硬 gate 保持 0。
- `coverage` / `high_conf` 的小幅波动属生成方差，**不**作为 product regression 结论，且未做 paired attribution。
- Product Quality DoD = **NOT_YET_PASS**（仅 false_refusal 与 high_conf 达标）。

## 10. Tests

```text
tests/test_embedding_identity.py               production defaults / profile / validate / 引擎启动 / 真实库无副作用 / 新库 pin
tests/test_live_production_hash_guard.py       新增：live production hash 必须 == lineage current baseline 记录值
tests/test_v4_baseline_lineage.py               lineage 结构 / 不可变性
tests/test_v4_routing_remediation.py            V4.5 routing 回归 + lineage 链
tests/test_v4_6_post_routing_attribution.py     V4.6 只读不变量
tests/test_v4_scope_oos_remediation.py          V4.4 scope gate 冻结
```

`test_live_production_hash_guard.py` 是本次新增的**漂移侦测**：

```text
lineage current_baseline_id → current baseline artifact → recorded production_source_hash
        == recomputed live production_source_hash（canonical algorithm，无手工常量）
```

## 11. Baseline lineage

```text
V4_INITIAL_BASELINE                  eval/v4_initial_baseline.json                 IMMUTABLE_HISTORICAL
        ↓
V4_4_SCOPE_REMEDIATION_BASELINE       eval/v4_4_scope_remediation_baseline.json     IMMUTABLE_STAGE
        ↓
V4_5_ROUTING_BASELINE                 eval/v4_5_routing_baseline.json               IMMUTABLE_STAGE
        ↓
V4_6_1_EMBEDDING_IDENTITY_BASELINE    eval/v4_6_1_embedding_identity_baseline.json  CURRENT_PRODUCT_STATE
```

- `eval/v4_baseline_lineage.json → current_baseline_id = V4_6_1_EMBEDDING_IDENTITY_BASELINE`。
- 三个历史 artifact 的 SHA256 与 V4.2/V4.4.1 锚点一致，**未被改写**：
  `371506a9…` / `87ff7cff…` / `f69ffea2…`；`v3_final_golden.json = 31a68507…`。
- pointer 前移方式：把被取代阶段的 `status` 由 `CURRENT_PRODUCT_STATE` 改为 `IMMUTABLE_STAGE`；
  历史 entry 的 metrics / hashes / parent / metric_artifact / timestamp **均未改动**。

## 12. 与 relocation 的关系

`OUT_OF_BAND_EMBEDDING_CHANGE` 与 `WORKSPACE_RELOCATION` 是两个独立事件，不得混为一谈。
relocation 结论继续有效：database portable、baseline portable、ImportPathPolicy portable、
Qdrant named volume unaffected；`scripts/publication_scan.py` 的旧路径前缀仍为 `PENDING_TOOLING_FIX`。

## 13. 后续

```text
NEXT（本阶段之后，另行授权）= Workspace Relocation publication_scan Tooling Fix
再之后                     = V4.7 Document Identity Remediation（真正下一 product remediation）
```
