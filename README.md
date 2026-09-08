# Local Database QA

一个完全本地运行、答案可追溯到原文位置的教材/文档问答系统。

> 本仓库（公开版）只包含源码、测试与文档。教材、SQLite 知识库与 Windows 运行包仅存在于本地开发/使用环境，均被 .gitignore 排除、不会进入版本库。日常使用请先看 [本地使用说明](本地使用说明.md)。

系统把 PDF 整理成单个 SQLite 知识库，使用 FTS5 全文检索与向量检索双路召回，经 RRF 融合、质量加权和范围判断后，由本地 Ollama 模型生成带原文引用的回答。v3 起支持 PDF / DOCX / PPTX / TXT / Markdown 五格式通用导入、可插拔 Qdrant 稠密索引、知识库/标签管理与按范围检索（QueryScope）。桌面和手机共用响应式 Web 界面，内容无需上传云端。

## 阶段状态（KB-V3）

| 阶段 | 版本 | 内容 | 状态 |
|---|---|---|---|
| Phase A | v3.0 | 向量后端解耦 + Qdrant Dense Index | FINAL PASS |
| Phase B | v3.1 | 本地 Cross-Encoder Reranker | ACCEPTED_WITH_EFFICACY_DEFERRED |
| Phase C | v3.2 | 五格式通用导入 + 增量导入 | FINAL PASS |
| Phase D | v3.3 | 知识库管理 + 文档生命周期 + QueryScope | FINAL PASS |
| Phase D.1 | v3.3 | 运行时整合 + Scope 收口 + 错误脱敏 | FINAL PASS |

Phase E（Router / Query Rewrite）尚未开始。

## 核心特性

### 检索与知识库

- **SQLite FTS5 全文检索**（正文 + 标题双列，bm25 列加权）+ **稠密向量检索**双路召回，RRF 融合（语义 1.25 / 词法 1.0）；
- **可插拔向量后端**：默认 SQLite 进程内暴力扫描（零依赖，行为与 v2 一致）；可选本地 [Qdrant](https://qdrant.tech/) ANN 索引（纯标准库 REST 适配器）。SQLite 始终是 Source of Truth，Qdrant 是可完全重建的稠密索引（rebuild / verify / 一致性校验脚本齐备）；
- 嵌入输入携带章节/小节路径（上下文嵌入），bge-m3 1024 维；OCR 质量分折扣、标题命中加分、近重复过滤、同小节限额；
- 离题拒答：词法强度 + 密度门限双重判断；二字概念问题按集中命中度放行；
- 建库原子替换：临时库通过完整性校验后才替换，失败不破坏旧库；增量重建复用未变片段向量。

### 通用文档导入（Phase C）

- PDF / DOCX / PPTX / TXT / Markdown 统一解析为 NormalizedDocument → 通用层级 Section → 结构化切片；格式差异不出解析层；
- 增量导入：source_hash 未变跳过；变化按 chunk_id 复用未变嵌入；更新后 stale 片段/索引点完整清理（SQLite 与 Qdrant 双侧验证）；
- 解析安全：extension allowlist、大小上限、严格编码解码、DOCX/PPTX ZIP 中央目录预检（成员数/解压总量/单成员上限/压缩比，防 ZIP bomb）、加密/损坏文档类型化拒绝。

### 知识库管理（Phase D）

- **知识库（KnowledgeBase）+ 标签（Tags）**：稳定持久化身份，默认 Default Knowledge Base；
- **文档生命周期**：稳定 document identity（首次创建后永久持久化）、可变 source_path（relink：同内容纯改路径，内容变化显式确认后更新，绝不隐式合并）、READY / FAILED / FAILED_INDEX / DELETING / DELETE_FAILED 持久化状态、软停用（enable/disable 不删数据）；
- **安全删除**：标记 → 清 SQLite 可检索内容 → 删 Qdrant points → 校验 → 定稿；任一步失败进入 DELETE_FAILED 且已删内容不可再被检索，可重试恢复；Qdrant 不可达 / HTTP 500 / 畸形响应 / 部分残留均有故障注入测试；
- **QueryScope 全链路贯穿**：知识库 / 文档 / 类型 / 标签范围选择从 UI → API → 引用 → 检索（FTS SQL 级 pushdown + Qdrant filter）→ 引用核验（越界引用属严重失败）→ telemetry；scope leakage 评测为 0（34 例双后端评测集）；
- **Web 路径导入安全边界**：`LIBRARY_IMPORT_ROOTS` 显式配置允许目录（canonical 路径包含判断，防 `..`/symlink/junction 逃逸）；未配置时 Web 路径导入默认禁用，CLI 保持本机用户权限；API 不回显服务器绝对路径。
- **运行时整合（Phase D.1）**：Library Manager 与问答引擎共享同一 SQLite 库身份（静态三规则：受管库优先原地升级 → legacy 教材库原地接管 → 全新受管库；失败显式报错，绝不静默换库）；管理端变更即时通知服务端刷新快照、重算库指纹并清空答案缓存（无需重启）；书籍级路由与检索共用同一 effective scope；API 错误体路径脱敏单点收口；PDF 资源守卫（`QA_PDF_MAX_PAGES` / `QA_PDF_MAX_EXTRACTED_CHARS` 超限类型化拒绝）。
- **迁移闭包（Phase D.1.1）**：双库冲突守卫——managed 与 legacy 同时含数据且缺少迁移证据（`legacy_migration_completed` 标记 + 文档 id/sha256/chunk 数核对）时显式报错，绝不静默让受管库赢；`scripts/migrate_legacy_library.py` 单事务合并 legacy v4 教材库进 managed v5 库（可回滚、幂等、冲突安全），embeddings 逐字节复用（零重嵌入），迁移后写入带内容指纹的证据标记，并可 `--qdrant-sync` 把教材 points 收敛进 managed collection（`general_documents`），旧 collection 不删除。

### 问答与对话

- 意图路由：全书目录、全书介绍、单章概括、页码/章节定位、比较（按双方分侧检索）、普通问答；书籍级问题不调用模型；
- 多轮追问：追问与上一问合并用于路由和检索，最近 3 轮对话进入模型消息；回答仍只依据本轮材料；
- 引用纪律：范围/列表引用展开、越界剔除、拉丁实体核验（先核验后重编号）、按首次出现重编号；引用核验未通过会提示；
- 材料预算：按上下文窗口自动裁剪尾部材料；相同问题命中 LRU 缓存（按库指纹失效，scope 参与缓存键）。

### 可选 Cross-Encoder Reranker（Phase B，默认关闭）

- `RERANKER_ENABLED=false`（默认）：管线与 v3.0 完全一致；
- 工程实现验证通过（独立 sidecar 进程 + loopback HTTP，主运行时零第三方依赖）；当前单教材语料上排名增益有限（MRR +0.0048 / nDCG@5 +0.0084，未达 0.02 有意义增益参考值），**排名有效性 deferred**，待多文档语料就绪后重新评估；重排器无法改变离题拒答判定。

### 界面与服务

- 会话式回答、引用点击跳转证据卡、流式输出、任务排队与取消、SSE 心跳；
- 知识库管理页（`/library.html`）：文档列表、状态/失败原因、启用/停用、删除（二次确认）、失败重试、标签；问答页可按知识库/文档/标签选择检索范围；
- 安全：六位配对码 + 限速 + 12 小时会话令牌、Host 校验防 DNS rebinding、CSP 等安全响应头；
- 观测：QA telemetry（`qa_log.jsonl`，含 scope/v2/v3 分阶段耗时）、导入（`import_log.jsonl`）与库操作（`library_log.jsonl`）日志相互独立。

### 工程化

- 运行时仅用 Python 标准库（建库环境另需 requirements-ingest.txt）；
- 311 项单元/集成测试（真实 Qdrant/Ollama/Reranker 集成在服务不可达时自动 skip）；
- 评测门禁：教材 Golden Set（召回/范围/路由）、通用导入 25 例、Scope 34 例（leakage=0）、Reranker 53 例；
- ruff 静态检查、GitHub Actions CI、PyInstaller 一键打包；
- 数据目录保持可移植布局（`data/` 随程序存放）；Windows 受保护安装目录场景的 `%LOCALAPPDATA%` 搬迁为已登记 backlog（见 docs/V3_PROGRESS.md）。

## 项目结构

```text
core/                    检索、知识库、向量后端、导入、QueryScope、问答引擎
desktop/                 本地 Web 服务（v2 API + v3 Library API）与桌面启动入口
web/                     响应式浏览器界面（问答页 + 知识库管理页）
scripts/                 导入/建库/迁移、索引 rebuild/verify、评测与回归
tests/                   单元与集成测试（不依赖真实教材；服务可达时跑集成）
docs/                    架构说明、阶段计划与进度、Schema Impact Note
reranker_service/        可选 Reranker sidecar（自带独立环境）
data/pdf|raw|library/    教材、提取文本、知识库（本地数据，不入库）
```

## 环境要求

- Python 3.11+（运行时）；[Ollama](https://ollama.com/)；可选：本地 Qdrant（`VECTOR_BACKEND=qdrant`）
- 模型：`qwen2.5:7b`（回答）、`bge-m3`（向量，当前知识库使用；`nomic-embed-text` 为兼容默认值）

```powershell
ollama pull qwen2.5:7b
ollama pull bge-m3
```

## 快速开始

```powershell
# 1. 提取教材并建库（需要 requirements-ingest.txt 依赖和 Ollama）
python rebuild_all.py

# 2. 导入通用文档到受管知识库（本地用户权限）
python -X utf8 scripts/import_document.py --file path/to/doc.docx --kb kb-default

# 3. 源码运行（浏览器打开 http://127.0.0.1:8765，本机自动配对）
python -m desktop

# 4. 打包 Windows 运行包（-SkipIndex 保留当前知识库与 LLM 摘要）
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -SkipIndex
```

日常使用直接双击 `启动本地版.bat`。配置项（含 `LIBRARY_IMPORT_ROOTS`）、问法示例、多轮追问、手机访问、日志调优见 [本地使用说明](本地使用说明.md)。

## 验证

不需要教材和 Ollama：

```powershell
python -B -m unittest discover -v
python -B -m compileall -q core desktop scripts tests
node --check web/app.js
node --check web/library.js
node --check web/markdown.js
python -m ruff check core desktop scripts tests
```

已有真实知识库和 Ollama 时：

```powershell
python -X utf8 scripts/eval_recall.py
python -X utf8 scripts/regression_test.py
python -X utf8 scripts/eval_general_ingestion.py
python -X utf8 scripts/eval_scope.py
```

架构和安全边界参见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)；阶段记录见 [docs/V3_PROGRESS.md](docs/V3_PROGRESS.md)；可配置项见 [.env.example](.env.example)。

## 发布前说明

仓库当前未附带开源许可证。公开发布前请根据你的授权意图选择许可证；没有许可证时，其他人默认无权复制、修改或分发代码。
