# 本地教材问答架构

## 目标

系统优先保证三件事：答案可追溯、离题时不猜、教材库重建失败时不破坏可用版本。运行时保持完全本地，只依赖 Python 标准库和本机 Ollama。

## 数据流

```text
PDF → 带文档/页码标记的文本 → 章节与小节识别 → 结构化切片
    → SQLite v4（文档、页、章节目录、片段、FTS5 正文/标题双列、向量、摘要材料）
    → 书籍级意图直接查询目录/摘要
    → 其余问题使用 FTS5 + 向量召回 → RRF 融合与范围判断
    → Ollama 流式回答 → 结构化引用 → 浏览器工作台
```

`scripts/build_library.py` 先写临时数据库，校验完整性、片段数和向量数后才替换正式文件。旧库在任何中途失败时都保持不变。

## 运行时

- `core/library_store.py`：SQLite 真相源的只读加载；执行 FTS5 关键词检索、片段回查、目录/摘要访问；构造向量后端与混合检索器。SQLite `embeddings` 表同时是旧内置稠密后端的数据源和 Qdrant 重建的向量来源。
- `core/vector_store.py`：v3.0 引入的向量后端合同（`VectorStore` Protocol、DTO、错误类型），并定义 `chunk_id` / `content_hash` / `vector_input_hash` 三个互相独立的标识与哈希，以及由 `chunk_id` 确定性派生的 Qdrant point ID。
- `core/sqlite_vector_store.py`：默认稠密后端——进程内全量向量 + O(N) 暴力点积扫描，行为与 v2 完全一致（任一向量缺失即整体禁用稠密路径）。
- `core/qdrant_store.py`：可选 Qdrant 后端，纯 Python 标准库 `urllib` 直连 REST（显式绕过系统代理），主查询走 `/points/query` API；支持 collection 创建/校验、批量 upsert、按文档过滤删除、count/scroll 与索引一致性校验。Qdrant 仅是可完全重建的稠密索引，不是业务真相源。
- `core/hybrid_retriever.py`：FTS5 + 稠密候选的 RRF 融合、OCR 质量折扣、标题加分、近重复过滤、同小节限额、front_matter 回填与离题门限；RRF/门限等参数自 v2 冻结未变。v3.1 起支持可选二阶段重排：候选池（`RERANK_CANDIDATE_K`，默认 16）经 cross-encoder 重排后取 final top_k；`SearchHit.rerank_score` 单独记录重排分，融合分含义不变；Scope/OOS 门限仍只使用重排前的检索信号，重排器无法改变拒答判定；`RERANKER_ENABLED=false`（默认）时管线与 v3.0 完全一致。候选重排文本由 `build_rerank_passage` 从 SQLite 权威片段确定性构造（文档/章节/小节 + 正文）。
- `core/reranker.py`：重排器协议与适配器（`HTTPReranker` / `IdentityReranker`），通过 loopback HTTP 调用独立 sidecar 进程 `reranker_service/`（自带 torch/transformers 可选环境，主运行时保持零第三方依赖），loopback 请求显式直连；ID 一一对应、NaN/inf、超时、模型不匹配等均有类型化错误；`RERANKER_FALLBACK=disabled`（默认）时 sidecar 不可用显式报错，`rrf` 时回退 RRF 排序。默认关闭。
- `core/engine_v2.py`：区分全书目录、全书介绍、单章概括、定位、比较和普通问答；书籍级问题绕过离题阈值；追问与上一问合并用于路由和检索，最近 3 轮对话进入模型消息；材料按上下文窗口预算裁剪；限制模型只能使用检索材料；核对引用编号（先核验后按首次出现重编号）；每次回答追加 telemetry JSONL（v3.0 起附 `vector_backend` 与分阶段耗时字段）。
- `desktop/web_server.py`：提供静态页面、v2 API、单工作队列、流式事件（含心跳）和取消操作；LRU 答案缓存按教材指纹失效（追问不缓存）；配对限速、Host 校验与安全响应头。
- `web/`：桌面与手机共用的响应式界面。页面额外注册 `ask_textbook` WebMCP 工具，但不影响普通浏览器使用。

### 向量后端选择

`VECTOR_BACKEND=sqlite|qdrant`（默认 `sqlite`）。选择 `qdrant` 时必须先运行 `scripts/rebuild_vector_index.py` 从 SQLite 建索引，`scripts/verify_vector_index.py` 校验一致性；Qdrant 不可用时检索显式报错，不会静默回退，也不会破坏 SQLite。`scripts/benchmark_retrieval.py` 提供稠密延迟基准与双后端行为对比。

### 通用文档导入（v3.2）

Phase C 新增与格式无关的导入管线，SQLite/Qdrant 不感知来源格式：

    任意来源 → ParserRegistry 选择解析器 → NormalizedDocument
            → Section Builder（通用层级） → Chunk Builder → SQLite → 嵌入 → Qdrant- ：NormalizedDocument / NormalizedSection /
  NormalizedBlock / SourceLocation 契约；（来源路径确定性身份，
  内容编辑不改变）、（原始字节版本）、（规范化内容
  版本）三者分离；统一的  嵌入
  输入构造器（兼容旧教材约定）。
- ： Protocol +  集中分派；
  TXT（UTF-8/BOM/GB18030 严格解码，保守标题启发式，可关闭）、Markdown
  （ATX 标题/围栏代码/列表/表格/引用/front matter，纯标准库）、DOCX
  （Word 标题样式/表格/不支持内容计数，python-docx）、PPTX（slide 顺序/标题/
  文本框/表格/备注，python-pptx）、PDF（包装既有 PyMuPDF+OCR 管线，page 级
  SourceLocation）。DOCX/PPTX 在交给格式库之前先做 ZIP 中央目录预检
  （成员数/解压总量/单成员上限 + 压缩比 backstop，只读元数据不解压）。
  解析失败类型化：UnsupportedFormat / ParseFailure /
  EncodingFailure / EncryptedDocument / EmptyDocument / CorruptDocument。
- ：DocumentImporter 统一管线——增量（source_hash 未变化
  返回 UNCHANGED；变化则 UPDATE 并按 chunk_id 复用未变嵌入）、dry-run 不落
  库、SQLite 单事务原子写入、嵌入失败回滚（FAILED）、Qdrant 失败不破坏
  SQLite（FAILED_INDEX，可 rebuild 修复）；导入遥测写
  ，与 QA telemetry 分离。
- ：导入 CLI（--file/--dry-run/--backend/--force）。
- ：5 格式 × 5 查询的通用导入评测（每格式
  独立库），25 条用例全部通过。

Schema 决策：Phase C 保持 **v4** 核心（通用文档以「section 路径字符串 + chapters 兼容
映射（level-1 节 → chapters 行）」落库）；Phase D 在受管库 `documents.sqlite3` 上
加性迁移到 **v5**（knowledge_bases / document_sources / tags / document_tags 四表，
稳定 KB/文档身份 + 可变 source_path + 持久化生命周期状态，见
docs/V3_SCHEMA_IMPACT_NOTE_PHASE_D.md）。教材库继续 v4 legacy 不迁移。

### Knowledge Library Manager + QueryScope（v3.3）

Phase D 在导入能力之上建立受管知识库域：

- `core/library_service.py`：LibraryService——KB CRUD、稳定身份导入
  （document_id 首次创建后永久持久化，source_path 是可变属性）、relink（同 hash
  纯改路径；不同 hash 显式 SOURCE_CHANGED 确认后走 UPDATE；拒绝隐式合并）、
  enable/disable（软停用不删数据）、安全删除（标记 DELETING → 清 SQLite 可检索
  内容 → 删 Qdrant points → verify → finalize；失败落 DELETE_FAILED 且文档不可
  再被检索，可 retry-delete）、retry-index、标签、duplicate-content 提示
  （只提示不合并）、`library_log.jsonl` 操作遥测。Web 层只做 HTTP 适配。
- `core/query_scope.py`：QueryScope（knowledge_base_ids / document_ids /
  document_types / tags / section_ids 预留）。None 与空 Scope = 默认可检索范围
  （READY + enabled），`restrict_nothing()` = 显式空结果；解析一次得到具体文档集，
  FTS SQL 子查询与 Qdrant filter 使用同一集合。
- Scope 贯穿：UI 选择 → `/api/v2/jobs` scope 字段（缓存键含 scope）→ Engine
  （`answer(question, scope=)`，书籍级路由材料同步过滤）→ HybridRetriever（FTS
  pushdown + VectorScope）→ Qdrant filter（document_id/kb/document_type/tags）→
  Citation 门卫（越界引用抛 `CitationScopeViolationError`）→ telemetry（计数 +
  指纹）。Scope leakage 的评测 Gate 为 0（`scripts/eval_scope.py`，34 cases 双后端）。
- `web/library.html`：最小知识库管理页（状态、启用/停用、删除二次确认、重试）。
  教材库保持 legacy 不受管理；浏览器文件上传与 section scope 为 DEFERRED。
- 路径导入安全边界（Phase D Security Closure）：`LIBRARY_IMPORT_ROOTS`
  （os.pathsep 分隔）定义 Web 路径式导入/relink 唯一允许的目录；客户端路径经
  `Path.resolve()` canonical 化（跟随 symlink/junction、消解 `..`/混合分隔符）
  后以 `os.path.commonpath` 做包含判断（大小写变体安全），绝不使用原始字符串
  前缀比较。**未配置根目录时 Web 路径导入默认禁用**；CLI
  （`import_document.py`）代表本机用户权限，不受此策略约束。路径位于根内的
  文件仍必须通过 extension allowlist / parser registry / 大小上限 / ZIP 安全 /
  损坏加密检查——Path Policy 不替代 Parser Security。API 响应不返回服务器绝对
  路径（以 `source_name` / `source_display`（根内相对路径）呈现），完整路径仅存
  于 SQLite 与本机 CLI。
- 语义记录（Phase D security closure，防止 Phase E 误用）：
  ```text
  enabled=false means the document is excluded from default retrieval.

  An explicitly selected document scope may include a disabled-but-READY
  document; enabled is a default-selection control, not an authorization ACL.
  ```
- Phase E Router Safety Invariant（v3.4 已实现，见 docs/V3_PHASE_E_ROUTER_DECISION.md）：
  任何 Router、document/global summary、multi-document QA、query rewrite 组件必须
  接收 effective QueryScope，且禁止绕过 LibraryService / scoped retrieval 访问
  非 READY、DELETE_FAILED 或 scope 外文档。Phase E 实现：router 只决定语义与路由、
  零 scope 变更；问题点名范围外文档时只报告 `scope_conflict`，由既有 scope 门限
  继续保证检索与 citation 不越界（eval 实测 leakage=0）。

### 运行时集成收口（v3.3 Phase D.1）

Phase D 主体验收后的运行时整合（4 项 P0 关闭：双库分叉 / 运行中导入不可见 /
book 路由 scope / 路径泄露）：

- `core/runtime_library.py`：整机唯一库身份的静态决策点（非动态路由）——受管库
  `documents.sqlite3` 存在即以它为准并原地升级（v4→v5 纯加性）；无受管库但
  legacy 教材库存在则原地接管（同一文件升级，绝不复制出第二真相源）；两者皆无
  则创建空受管库。升级/创建失败显式抛错，绝不静默换库。
- 变更可见性（P0-02 关闭）：`LibraryService` 每次提交式变更后回调 `on_mutated`；
  `WebQAServer._on_library_mutated` 在引擎锁内 `library.refresh()` → 重算库指纹
  → 清空 LRU 答案缓存；导入/启停/更新/删除对问答即时生效，无需重启。同路径并发
  导入由变更锁串行化，收敛为单一身份（READY + UNCHANGED）。
- 错误脱敏统一收口（P0-04 关闭）：`desktop/library_api_safety.py` 单点处理——API
  响应经 `redact_source_paths` 把绝对路径替换为 `source_name` / `source_display`；
  错误消息经 `sanitize_error_message` 把路径形 token（盘符/UNC/POSIX）统一降为
  basename，导入根目录整体替换为 `<导入目录>`（含 Windows OSError 双反斜杠
  归一化，防根目录名残留）。
- PDF 资源守卫（P1）：`QA_PDF_MAX_PAGES` / `QA_PDF_MAX_EXTRACTED_CHARS` 上限，
  超限以 `DocumentTooLargeError`（RESOURCE_LIMIT）类型化拒绝。
- Scope 单一真相（P0-03 关闭）：`effective_allowed_ids` 同时驱动检索（FTS
  pushdown + dense 候选）与书籍级路由（目录/全书概览/章节摘要/缺章提示）；
  空 scope 永不回退全库，book 路由与检索看到同一文档集。

### Hierarchical Summary（v3.5 Phase F.1）

F.1 建立统一 Summary 生命周期（`core/summary.py`）；SQLite `summaries` 表是唯一业务真相源（Qdrant / 进程缓存都不是 summary 真相源）：

- 层级：source chunks → **section/chapter summary**（extractive：绑定该 section 真实 chunk ids + 内容哈希，无正文的 section 用显式 heading-only 描述符）→ **document summary**（aggregate：由多个 section summary 聚合生成；禁止单个 chunk / 前置章节块冒充完整文档摘要——F.0 审计发现的旧模式已关闭）。
- Provenance（additive 列，metadata `summary_provenance=1` 标记）：`scope_id`（稳定章节 ID 关联，summary_contexts 优先按 ID join、legacy 行按标题相等回落，解决同名/改题串数据与标题漂移）、`source_ids`、`dependency_hash`、`generator_type`（mechanical / extractive / aggregate / llm_rewrite / heading_only / legacy）、`model`、`prompt_version`、`generated_at`、`summary_version`。旧库行 migration 后默认 `generator_type='legacy'`、provenance 全空——可识别、不崩溃、绝不伪造。
- Dependency fingerprint：`(算法版本 + generator + prompt/model + 有序 source id/hash)` 的稳定哈希；source 或配置变化 → 指纹变化 → 旧摘要不再 CURRENT。
- Invalidation：文档未变（source_hash 相同）跳过全部写入、摘要安全复用；文档变化 → 文档级重建（受影响 section 摘要与 document 摘要全部重新生成，无 stale 行）；删除 → summaries 按 document_id 清空，无 orphan，其他文档不受影响。迁移幂等（ALTER ADD COLUMN + INSERT OR REPLACE 标记）。
- LLM 路径语义：`--llm-summaries` 被明确标记为 **summary rewrite**（generator_type=`llm_rewrite` + model + prompt_version，source 绑定不变），而非 source-grounded 文档摘要；失败保留机械文本，库级标签如实记 `mixed`（不再把混合库误标为纯机械）。
- 双真相裁决：`chapters.overview` 裁定为兼容镜像——写路径从同一 summary record 文本生成，业务真相只在 summaries 表；两者由测试锁定不漂移。

### Reranker（可选，默认关闭）

已实现可选本地 Cross-Encoder Reranker（`BAAI/bge-reranker-v2-m3`，经独立 sidecar 进程调用），并完成真实 CPU/CUDA 性能、故障回退及排名评测；当前单教材饱和基线下整体收益有限（MRR +0.0048 / nDCG@5 +0.0084，未达 0.02 有意义增益参考值），因此**默认关闭**，待多文档阶段重新评估。

`RERANKER_ENABLED=false`（默认）。开启前需在 `reranker_service/` 建独立环境并启动 sidecar（127.0.0.1:7998，loopback-only）。`scripts/eval_reranker.py` 以 `scripts/reranker_eval_set.json`（53 条人工标注查询）对比 RRF-only 与 RRF+Reranker 的 MRR / nDCG@5 / Recall@5 / Top1 / Top3 / compare coverage。

## 接口与安全

本机页面可读取一次启动配对信息；局域网设备必须输入主机显示的六位配对码。配对成功后服务签发 256 位随机会话令牌，默认 12 小时失效。六位码不能直接访问其他接口，失败尝试会被限速。

服务没有开放 CORS，并设置了 CSP、禁止嵌入、禁止 MIME 猜测等响应头。它仍是可信局域网 HTTP 服务，不应暴露到公网；公网访问应另加 TLS 和正式身份认证。

## 仓库边界

仓库只保存程序、测试和文档。教材 PDF、OCR 文本、SQLite 知识库、Windows 安装产物及运行缓存都由 `.gitignore` 排除，避免提交版权材料、机器相关文件和可再生成的大文件。

## 质量门槛

单元测试覆盖自然语言变体、结构化目录、摘要路由、跨章小节过滤和引用编号校验；v3.0 起还覆盖向量后端合同（两种后端共用同一套契约测试）、Qdrant 传输层错误映射与融合行为等价。已有真实教材库时，`scripts/regression_test.py` 进一步检查典型知识点、离题拒答、七章目录和书籍级意图，未通过时不应重新发布运行包。本地 Qdrant 可达时，`tests/test_qdrant_integration.py` 会对真实实例运行集成验收。
