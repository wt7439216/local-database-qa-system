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
- Windows 运行包由 `windows_desktop.spec` 打包 **managed 库** `data/library/documents.sqlite3` 的字节快照（当前必需 build input）。`textbooks.sqlite3` 是 legacy 库，`windows_bundle.py` 明确拒绝它进入候选；`core/config.py` 中 `LIBRARY_DB` 已统一指向 managed 库，`LEGACY_LIBRARY_DB` 单独标记 legacy 路径。
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

## 14. 源码身份与历史治理（2026-11-07 起已解锁）

- `production_source_hash()`（`scripts/eval_v4_baseline.py`）仍对 `core / desktop / web` 求「相对路径 + 内容哈希」摘要，用作答案缓存失效锚点与打包清单。**任何源码改动都会改变它，但不再有守卫要求它等于某个冻结值**。`scripts/` 不在生产树内。
- 历史治理注册表、baseline lineage、WS-13 冻结身份、live production drift guard 及其逐字节绑定测试，已归档到 `Archive/20261107_refactor_unbind/`（附 `ARCHIVE_MANIFEST.json` 与 `RESTORE.ps1`，可完整回滚）。
- **P5 更新**：`engineering_revision.py` / `product_revision.py` / `publication_*.py` 等冻结治理与双副本同步脚本已归档到 `Archive/20261109_p5_convergence/`，不再是运行时的一部分；`publication_*` 所依赖的「`.github` 归上传版所有」规则随单仓库收敛一并废止。
- `scripts/build.py` 是新打包入口，不传 `-ExpectedProductionHash` / `-QualityEvidence`；`scripts/windows_bundle.py` 的 quality evidence 分支仅作历史兼容，库身份仍严格校验。
- 重构后若需重新打包 EXE，必须重新生成 `build_manifest.json`、`BUILD_RECORD.json` 与候选指针（用 `scripts/activate_candidate.py`）。`runtime/` 下的现有 EXE 仍绑定其自身历史记录，与当前源码解绑，启动链不做 live 源码校验。
- 当前验收以 **`make check`（`scripts/verify_all.py`）** 为准，见 `README.md` 的「测试与评测」。

## 15. HTTP 分层与契约（P1）

`desktop/web_server.py` 现在只是**组合根 + 兼容门面**（约 240 行），实现按职责拆分：

| 模块 | 职责 |
|---|---|
| `desktop/jobs.py` | `AnswerJob`、`sanitize_history`、scope/缓存键工具 |
| `desktop/auth.py` | 配对码/令牌鉴权、`HostPolicy`（DNS rebinding 防护） |
| `desktop/answer_cache.py` | LRU 答案缓存与库指纹 |
| `desktop/transport.py` | JSON / 静态文件 / NDJSON 传输辅助（`TransportMixin`） |
| `desktop/routes_v3.py` | v3 知识库路由表（**纯函数**，可直接单测） |
| `desktop/handler.py` | v2/v3 请求路由（`make_handler(owner)` 兼容入口） |
| `desktop/worker.py` | 单 worker 答案队列循环 |

`desktop/api_contract.py` 是 v2/v3 HTTP 契约的单一真源（OpenAPI 3.1 + JSON Schema 2020-12），导出为 `docs/openapi.json`；`scripts/capture_contract.py` 对真实服务逐路由发请求并校验响应 schema，`tests/test_api_contract.py` 把校验固化进测试套件。契约结果不含动态字段，可用于重构前后逐项比对。

`core/hashing.py` 与 `core/db.py` 分别统一了哈希与 SQLite 连接工厂；旧调用点通过兼容别名/等价参数保持行为不变。

## 16. 领域层与事务边界（P2）

代码按 `core/domain/`（纯业务逻辑）→ `core/application/`（用例编排）→ `core/persistence/` 与 `core/migrations/`（基础设施）分层；`core/engine_v2.py`、`core/library_service.py` 是**兼容门面**，保留全部历史导出名与可 patch 属性。

| 层 | 模块 | 内容 |
|---|---|---|
| domain | `prompts.py` / `responses.py` / `telemetry.py` / `citation_postprocess.py` / `routing_policy.py` | 版本化 prompt、结果 DTO 与模板文案、遥测记录构造、引用后处理、路由参数策略 |
| application | `ask_question.py` | `finalize_answer()`：引用归一 → 补全 → 重编号 → 确定性核验 → telemetry → warnings；`pre_renumber` 编号契约保持不变 |
| migrations | `registry.py` | 显式版本链 `MIGRATIONS`（4 → 5）、`migration_plan()`、`ensure_managed_schema` / `managed_schema_is_current` 兼容实现 |
| persistence | `unit_of_work.py` / `repositories.py` | `UnitOfWork`（显式 BEGIN，DDL 与写入同事务）、`IndexOutbox`、只读 SQL 仓库函数 |

- 检索/生成参数统一在 `core/retrieval_config.py::RetrievalSettings`（`config.RETRIEVAL`），默认值与旧常量逐一相同，可用 `QA_RETRIEVAL_*` 覆盖做离线标定。
- **事务性 outbox**：`index_outbox` 表惰性创建（稳态启动零写盘）。import / relink / tags 的 READY 事务、delete 的清内容事务在**同一事务内**登记 `DOCUMENT_UPSERTED` / `TAGS_CHANGED` / `DOCUMENT_DELETED`；`_dispatch_index_event()` 立即幂等消费，Qdrant 故障只留 PENDING 而不让已提交的导入「抛异常」；`LibraryService.replay_outbox()` 或 `scripts/replay_index_outbox.py --apply` 在重启后重放。这消除了「SQLite 已提交但索引未同步」的崩溃窗口。
- 回归证据：`tests/test_p2_regressions.py` 覆盖迁移前向/字节回滚演练、索引故障崩溃注入、UoW 回滚、配置注入、门面兼容与 hypothesis 属性不变式。

## 17. 接口与前端现代化（P3）

**默认运行时仍是标准库、零第三方依赖**（离线 / PyInstaller 底线）；P3 在此基础上完成：

| 领域 | 改动 |
|---|---|
| 并发 | `desktop/worker.py` 从单 worker + 全局 `_engine_lock` 改为 `QA_ANSWER_WORKERS`（默认 4）个独立 worker；缓存一致性改用 **epoch**（mutation 递增 epoch 并立即清缓存，worker 写缓存前校验 epoch），不再让一个慢回答阻塞全部请求 |
| 取消与超时 | `AnswerJob.is_cancelled()` 同时检查取消事件与 `QA_JOB_TIMEOUT_SECONDS` 截止时间；回调一路透传到 `core/http_client.py` 的流式读取，httpx 可用时由 watchdog 关闭响应中断底层请求，urllib 回退路径逐行协作检查 |
| 传输 | 保留 NDJSON 契约端点，新增标准 SSE `GET /api/v2/jobs/{id}/stream`（`text/event-stream`、`event:`/`data:` 帧）与轻量状态端点 `GET /api/v2/jobs/{id}`；OpenAPI 扩到 17 paths / 20 schemas |
| 前端 | `web/app.js` / `library.js` / `markdown.js` 改为 **ESM 模块**，共享工具集中到 `web/shared.js`（消除两页重复的 `$`/`toast`/`setStatus`/`escapeHtml`/`authHeaders`/`api` 定义与全局冲突）；HTML 用 `type="module"`，`web/package.json` 声明模块类型；`_static` 对 `.js` 强制 `text/javascript` |
| 可选现代栈 | `desktop/modern_app.py` 提供 FastAPI/uvicorn 实现（延迟导入，不装也不影响默认运行），`python -m desktop --modern` 启用；复用同一 `WebQAServer` 协作者，`scripts/capture_contract.py --backend modern` 用**同一套 23 个契约 case** 验证双栈一致 |
| 依赖边界 | fastapi / uvicorn / httpx 只用于可选栈、开发/CI 与可取消流式，不写入运行时 requirements；默认 EXE 仍零依赖 |

并发压测、超时/取消、ESM 结构、双栈契约均固化在 `tests/test_p3_regressions.py`。

## 18. 质量攻坚（P4）

P4 的原则：**所有新能力默认关闭、零第三方依赖、可离线验证**，因此默认运行时行为与 P3 完全一致。开关集中在 `core/config.py::Settings`：

| 开关（环境变量） | 默认 | 能力 |
|---|---|---|
| `QA_FTS_DICTIONARY` | 0 | 领域词典完整词项，写入/查询对称 |
| `QA_VECTOR_ANN` | 0 | SQLite 后端的内存 IVF 近似向量索引 |
| `QA_VECTOR_ANN_CLUSTERS` / `QA_VECTOR_ANN_NPROBE` | 64 / 32 | ANN 簇数与探针数 |
| `QA_STRUCTURED_ANSWERS` | 0 | 引导解码的 `claims[].citation_ids` → 引用标记文本 |
| `QA_CITATION_L15` | 0 | CJK 关键项 NFKC / 中文数字 / 单位归一 |

**中文分词升级**：`core/dictionary.py` 从 `chunks.text` 按「文档频率 + 左右邻字多样性 + 虚词字过滤 + 长词包含剪枝」挖掘领域词；`scripts/build_domain_dictionary.py` 生成 `data/library/domain_dictionary.txt`；开启 `QA_FTS_DICTIONARY=1` 后 `core/tokenizer.py::fts_terms` 在两侧同时加入完整词，需跑一次 `scripts/rebuild_fts_index.py --apply`。默认关闭时词项输出与 P0 逐字相同（有测试锁定）。

**ANN 索引**：`core/ann_index.py` 是纯标准库 IVF（球面 k-means + 倒排表，`math.sumprod`），`SQLiteVectorStore._load()` 后按需构建，`search()` 保持 `(score, position)` 降序以不扰动 RRF 名次；SQLite 仍是唯一真相源。`scripts/benchmark_ann.py` 给出随机/有簇两种合成语料的 recall@10 与加速曲线。**评估结论：暂不默认启用** —— 32 探针（覆盖约 50%）约 1.9× 加速、有簇数据 recall@10≈0.92、无结构数据≈0.88；全探针时与暴力扫描精确等价。需在真实 bge-m3 embedding 上标定后才可考虑切换。

**离线标定**：`scripts/calibrate_retrieval.py` 把主库复制到临时目录（**绝不写生产库**），用 Golden-185 的 144 个 in-scope / 41 个 OOS 问题，对 baseline 与 dictionary 两种索引 × 6 档查询词上限做网格搜索，输出 `P4_CALIBRATION.json`。实测 in-scope 词法召回 0.9792；最佳区分度出现在词典模式 + cap=8，但默认仍保持 baseline + cap=16（行为不变），该结果作为「未来启用词典时的推荐配置」记录。

**生成与引用契约**：`scripts/capture_prompt_contract.py` 冻结 `PROMPT_VERSION` / system / task hints / 固定样例 messages，基线为 `eval/prompt_contract_baseline.json`，并加入 `check_all.py` 作为第 10 项门禁。`core/domain/structured_answer.py` 解析结构化 claims（非法负载一律回退原文），`core/domain/citation_normalization.py` 提供 L1.5 确定性 CJK 归一（不改 `CITATION_VERIFIER_VERSION`，Phase F.2 黄金门禁不受影响）。

**架构债收敛**：`core/persistence/document_state.py` 集中 `DOCUMENT_STATUSES` / 转移表 / `can_relink` / `can_retry_delete` 等门禁策略，`LibraryService` 的 4 处内联状态判断改为委托，`library_model.py` re-export 保持导出面。

**验收状态（2026-11-09 勘误）**：此前「本机未启动 Ollama」的判断**是错误的**——实测服务一直运行（v0.40.15，`bge-m3:latest` + `qwen2.5:7b`，`127.0.0.1:11434`），只是没有去跑评测。`data/eval_cache` 为空只说明 `--report-only` 无从读数，不代表无法生成。Full-144 canonical 评测与 `QA_CITATION_COMPLETION` / `QA_STRUCTURED_ANSWERS` / `QA_CITATION_L15` 三组 A/B 已于 2026-11-09 补跑，实测指标与结论见 `Archive/20261109_p5_convergence/Full-144_补充评测与勘误报告.md`。P4 交付的离线证据链（0.9792 in-scope 词法召回、Phase F.2 门禁、prompt 契约）仍然有效，但不再用它替代生成层指标。

## 19. 工程收敛（P5）

- **依赖与工具配置单一真源**：`pyproject.toml`（PEP 621）声明元数据、`requires-python = ">=3.10,<3.14"`、5 个可选依赖组（`dev` / `modern` / `ingest` / `build` / `sidecar`）与 ruff / coverage / pytest 配置；`ruff.toml` 已删除（target-version 从 `py311` 对齐到 `py312`）。`requirements*.txt` 保留为构建脚本使用的冻结镜像，运行时仍零第三方依赖。
- **单一验收入口**：`Makefile` 的 `make check`（Windows 无 make 时 `scripts/check.ps1`）→ `scripts/verify_all.py`：执行 `check_all.py` 的 10 项门禁、双栈 HTTP 契约逐项一致性、已激活候选 `-ValidateOnly`、git 工作区干净；`--full` 另加覆盖率与 `scripts/startup_smoke.py`（真实启停服务 + 主库字节不变）。CI 直接调用同一入口。
- **简化打包与指针**：`scripts/build.py` 取代参数繁多的 PowerShell 编排，自动推导 `dist/` + `build/` 输出（不再依赖已消失的兄弟目录 `KB-V4_Candidates`），不传任何冻结哈希 / 质量证据参数；`scripts/activate_candidate.py` 从 `BUILD_RECORD.json` / `build_manifest.json` / EXE 推导指针身份字段，取代手工维护。`windows_bundle.py` 与 PyInstaller spec 的身份校验保持原样。
- **删除遗留**：4 个 `publication_*`（双副本单向同步 + `.github` 上传版所有权）、3 个冻结源码修订治理脚本、1 个产品阶段登记、5 个一次性评测/迁移脚本与 1 个发布修订注册表，共 14 个文件归档到 `Archive/20261109_p5_convergence/`（附逐文件 SHA256 与 `RESTORE.ps1`）。`refactor_tool.py --action probe` 改为验证当前单仓库验证链，不再 import 已归档模块。前端实验性 `document.modelContext`（WebMCP）分支移除。
- **单一仓库**：原「上传版」完整副本（含唯一 `.git`、36 次提交、4 个 tag、`PUBLICATION_EVIDENCE.json`、V3/V4 阶段文档与冻结证据）归档到 `Archive/20261109_p5_convergence/upload_snapshot/`；`.git` 历史迁入本目录，本目录成为唯一开发与发布仓库。发布改为 `git tag` + GitHub Actions + Release asset。
- **LICENSE**：新增明确许可状态文件（专有 / 未授予开源许可，遵循 README 原有「保留全部版权」意图）；未擅自替项目所有人选择开源协议。

## 20. Deferred Components

以下为已实现但**默认不启用**，或仍属 out-of-scope 的组件：

- **Reranker**（`BAAI/bge-reranker-v2-m3`，sidecar）：默认关闭；单教材饱和基线下排名增益有限，待多文档语料重新评估。
- **Qdrant 后端**：可选服务型后端，默认不启用（SQLite 为默认）。
- **L2 semantic verifier / NLI / LLM judge**：决策 DEFER_L2（L1 为当前引用核验层）。
- **KB Summary / Multi-document Summary 产品化扩展、通用文档/库元数据查询、Rich Citation UX、Performance SLA**：deferred 非阻断项，不进入当前主质量 Gate。
