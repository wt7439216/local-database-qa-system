# 本地教材问答架构

> 本文只描述**当前真实架构**。不包含 roadmap、阶段计划或未来子系统。
> 当前产品状态、路线与 Gate 见 `docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md`。

## 1. System Overview

系统优先保证三件事：答案可追溯、离题时不猜、知识库重建失败时不破坏可用版本。运行时保持完全本地，只依赖 Python 标准库和本机 Ollama。

当前生产模型架构：

```text
query → bge-m3 (1024) → FTS5 + 向量混合检索 →（可选 reranker，默认关闭）→ qwen2.5:7b
      → 结构化引用 → 引用核验 → 浏览器工作台
```

```text
ANSWER_MODEL      = qwen2.5:7b
EMBEDDING_MODEL   = bge-m3（dimension = 1024）
VECTOR_BACKEND    = sqlite（默认）
RERANKER_ENABLED  = false（默认）
```

## 2. Workspace / Runtime Boundary

- 运行时仅依赖 Python 标准库 + 本机 Ollama；建库环境另需 `requirements-ingest.txt`。
- 运行时根目录由 `core/config.py::_runtime_root()` 从程序自身位置推导（PyInstaller 用 `sys._MEIPASS`）→ **可移植**，不依赖任何旧绝对工作区路径。
- 仓库只保存程序、测试和文档；教材 PDF、OCR 文本、SQLite 知识库、Windows 产物与运行缓存均由 `.gitignore` 排除。

## 3. Query Flow

```text
来源（PDF / DOCX / PPTX / TXT / Markdown）
    → ParserRegistry → NormalizedDocument → Section Builder → Chunk Builder
    → SQLite 知识库（FTS5 正文/标题双列 + 向量）
    → Router（确定性 rules-first）
    → Scope / OOS 判定
    → FTS5 + 向量召回 → RRF 融合与质量加权
    →（可选 reranker）
    → qwen2.5:7b 流式回答 → 结构化引用 → 引用核验 → 浏览器工作台
```

`scripts/build_library.py` 先写临时数据库，校验完整性、片段数和向量数后才原子替换正式文件；旧库在任何中途失败时都保持不变。

## 4. Router

- `core/query_router.py`：确定性 rules-first 路由，覆盖全书目录 / 全书介绍 / 单章概括 / 页码与章节定位 / 比较 / 普通问答。书籍级问题不调用模型。
- Phase E 起为 conversation-aware：追问、代词、省略解析与最小 Query Rewrite；模糊指代宁可澄清、不猜错；Router **只解释语义，不扩大 QueryScope**。
- locate 过触发修复（V4.5）：`LOCATION_WORDS` 只表示词法出现，进入 `locate` 需要**位置意图**（`is_location_intent()`）；「`在哪` + 文档/集合容器」与「`出处`/`来源`」不再误入 `locate`。
- Route precedence：`book_toc > deferred_metadata > compare > chapter_overview > book_overview > locate_chapter > locate > qa`。

## 5. Scope / OOS

- `core/query_scope.py`：QueryScope（knowledge_base_ids / document_ids / document_types / tags / section_ids 预留）。None 与空 Scope = 默认可检索范围（READY + enabled）；`restrict_nothing()` = 显式空结果。
- 离题拒答：`core/hybrid_retriever.py` 在检索尾部综合**词法强度**与**稠密密度门限**判定 `out_of_scope`；V4.4 新增唯一的"密度主导"放行分支（`dense_only = 0.50`，按嵌入模型查表 `DEFAULT_DENSE_GATES` / `MODEL_DENSE_GATES`）。
- Scope 贯穿：UI → `/api/v2/jobs` scope 字段（缓存键含 scope）→ Engine → HybridRetriever（FTS pushdown + VectorScope）→ Qdrant filter → Citation 门卫（越界引用抛 `CitationScopeViolationError`）→ telemetry。
- Scope leakage Gate = 0（`scripts/eval_scope.py`，34 cases 双后端）。

## 6. Retrieval

- `core/library_store.py`：SQLite 真相源的只读加载；FTS5 关键词检索（正文 + 标题双列，bm25 列加权）、片段回查、目录/摘要访问。
- `core/hybrid_retriever.py`：FTS5 + 稠密候选的 RRF 融合（语义 1.25 / 词法 1.0）、OCR 质量折扣、标题加分、近重复过滤、同小节限额、front_matter 回填与离题门限。
- 嵌入输入携带章节/小节路径（上下文嵌入）。
- 可选二阶段重排：候选池（`RERANK_CANDIDATE_K`，默认 16）经 cross-encoder 重排后取 final `top_k`；`SearchHit.rerank_score` 单独记录，融合分含义不变；Scope/OOS 门限仍只使用**重排前**的检索信号——重排器无法改变拒答判定。
- `RERANKER_ENABLED=false`（默认）时管线与向量后端解耦前完全一致。

## 7. Embedding Identity

- 生产目标：`Embedding = bge-m3`（1024 维）+ `Answer = qwen2.5:7b`。
- 模型身份与期望维度由 `core/library_store.EMBEDDING_PROFILES`（单一真相表）声明。
- `core/library_store.validate_embedding_identity(...)` 在 `StructuredQAEngine.__init__`（`LibraryStore` 之后、创建 Ollama 客户端之前）**一次**执行 **fail-closed** 校验：

```text
configured_model（QA_EMBEDDING_MODEL） == stored_model（embeddings 表 / metadata / Qdrant payload / manifest）
stored_dimension == 该模型注册的期望维度（bge-m3 → 1024 / nomic-embed-text → 768）
```

- 任一不一致都会抛 `EmbeddingIdentityError` 并**拒绝启动**，而不是静默检索无意义近邻。
- 不变量：**no auto re-embed / no silent model switching / no automatic SQLite rebuild / no automatic Qdrant rebuild**。
- `nomic-embed-text`（768 维）仅作兼容/回滚，不是生产默认。
- `BAAI/bge-reranker-v2-m3` 是独立 reranker，受 `RERANKER_ENABLED`（默认 false）管理，不因嵌入身份修正而启用。

## 8. SQLite Backend

- `core/sqlite_vector_store.py`：默认稠密后端——进程内全量向量 + O(N) 暴力点积扫描（任一向量缺失即整体禁用稠密路径）。
- SQLite `embeddings` 表既是旧内置稠密后端的数据源，也是 Qdrant 重建的向量来源；SQLite **始终是 Source of Truth**。
- 受管知识库 `data/library/documents.sqlite3`（managed schema 5）是运行时真相源；legacy 教材库（schema 4）迁移合并后保留不删除。
- `core/runtime_library.py` 静态决定整机唯一库身份：managed 存在则优先并就地升级；否则就地接管 legacy；两者同时含数据且缺迁移证据时**显式报错**，绝不静默换库。
- Windows 运行包由 `windows_desktop.spec` 打包 `data/library/textbooks.sqlite3` 作为随包知识库快照（因此它是当前 **必需的 build input**，不是 V3 遗留检查）。
- 建库原子替换：临时库通过完整性校验后才替换，失败不破坏旧库；增量重建复用未变片段向量。

## 9. Qdrant Backend

- `core/qdrant_store.py`：可选/服务型后端，纯 Python 标准库 `urllib` 直连 REST（显式绕过系统代理），主查询走 `/points/query`。
- 支持 collection 创建/校验、批量 upsert、按文档过滤删除、count/scroll 与索引一致性校验。
- Qdrant 仅是可完全重建的稠密索引，**不是**业务真相源；不可用时检索显式报错，不会静默回退，也不会破坏 SQLite。
- `VECTOR_BACKEND=sqlite|qdrant`（默认 `sqlite`）。选择 `qdrant` 时需先 `scripts/rebuild_vector_index.py` 建索引、`scripts/verify_vector_index.py` 校验。

## 10. Generation

- `core/engine_v2.py`：区分全书目录、全书介绍、单章概括、定位、比较和普通问答；书籍级问题绕过离题阈值。
- 材料按上下文窗口预算裁剪；限制模型只能使用检索材料；追问答仍只依据本轮材料。
- `desktop/web_server.py`：静态页面、v2 API、单工作队列、流式事件（含心跳）与取消；LRU 答案缓存按库指纹失效（追问不缓存）；配对限速、Host 校验与安全响应头。

## 11. Citation

- `core/citation_verifier.py`：确定性 Citation 质量闭环（纯标准库，无 LLM/NLI/embedding/外部 IO），`CITATION_VERIFIER_VERSION = "f2-v4"`。
- 四层概念严格区分：**Validity**（引用是否真实对应 Evidence）/ **Scope Safety**（引用是否在当前 QueryScope，后端强制，不可降级为 UI warning）/ **Coverage**（`cited factual claims / factual claims`）/ **Support**（claim 与 cited Evidence 的支持关系）。
- Support 四值：`SUPPORTED` / `UNSUPPORTED` / `UNCERTAIN` / `NOT_APPLICABLE`。
- Engine 集成：在 `renumber_citations` **之前**用 pre-renumber 编号对真实 sent contexts + 确定性章节引用做 verify；`AnswerResultV2.citation_report` 加性暴露；telemetry 增加 citation 计数与 `citation_verifier_version`。
- 边界：这是 deterministic Layer-1，非 semantic entailment / NLI / complete factual verification。越界引用属严重失败。

## 12. History Rewrite

- 多轮追问与上一问合并用于路由和检索，最近 3 轮对话进入模型消息；回答仍只依据本轮材料。
- Query Rewrite 为最小改写；模糊指代宁可澄清。带追问上下文的请求不使用答案缓存。
- 已知残余（History 子系统）属未完成产品工作，记录于总控，不在本文展开。

## 13. Evaluation Architecture

- Canonical evaluator：`scripts/eval_v4_baseline.py`（`EVALUATOR_VERSION = "v4-baseline-v1"`），单一 canonical Golden `eval/v3_final_golden.json`（185 例，其中 144 answer-eligible）。
- 生成层为随机（本地 Ollama，无固定 seed），测量层为确定（`compute_metrics` 对冻结 answer artifact 计算，Run1 == Run2）。
- 指标（quality gate）：`case_exact_fact_match_rate` / `fact_recall` / `false_refusal_rate` / `citation_coverage`（case-level）/ `high_confidence_unsupported_rate`；硬安全：`invalid_citation_count` / `citation_scope_violation`。
- 分层评测与回归脚本：`scripts/eval_phase_e_router.py`（Phase E Router Golden 108 例）、`scripts/eval_phase_f_citation.py`（F.2 citation 37 例）、`scripts/eval_recall.py`、`scripts/eval_scope.py`、`scripts/eval_general_ingestion.py`。
- answer cache 与 `production_source_hash` / evaluator / Golden 绑定；生产代码变更会自动使答案缓存失效。

## 14. Baseline / Production Hash Governance

- `production_source_hash()`：对生产树 `core / desktop / web` 的**相对路径 + 内容哈希**取摘要，不依赖绝对工作区路径。`scripts/` 不在生产树内，修改脚本不改变该哈希。
- Baseline lineage 不可变：历史 stage baseline 一旦形成即 immutable；production remediation 只能**追加**新的 child baseline，绝不改写旧 stage baseline。current pointer 只存在于 `eval/v4_baseline_lineage.json → current_baseline_id`。
- **Live production drift guard**（`tests/test_live_production_hash_guard.py`）：

```text
lineage current_baseline_id → current baseline artifact → recorded production_source_hash
        == recomputed live production_source_hash（canonical algorithm，无手工常量）
```

- 任何未登记的 production 修改会立即导致守卫失败。current baseline 记录值与 source-of-truth 数值见总控文档，不在此手写。

## 15. Deferred Components

以下为已实现但**默认不启用**，或仍属 out-of-scope 的组件：

- **Reranker**（`BAAI/bge-reranker-v2-m3`，sidecar）：默认关闭；单教材饱和基线下排名增益有限，待多文档语料重新评估。
- **Qdrant 后端**：可选服务型后端，默认不启用（SQLite 为默认）。
- **L2 semantic verifier / NLI / LLM judge**：决策 DEFER_L2（L1 为当前引用核验层）。
- **KB Summary / Multi-document Summary 产品化扩展、通用文档/库元数据查询、Rich Citation UX、Performance SLA**：deferred 非阻断项，不进入当前主质量 Gate。
