# Local Database QA

一个完全本地运行、答案可追溯到原文位置的教材/文档问答系统。

> 本仓库（公开版）只包含源码、测试与文档。教材、SQLite 知识库与 Windows 运行包仅存在于本地开发/使用环境，均被 `.gitignore` 排除、不会进入版本库。日常使用请先看 [本地使用说明](本地使用说明.md)。

系统把 PDF 整理成单个 SQLite 知识库，使用 FTS5 全文检索与向量检索双路召回，经 RRF 融合、质量加权和范围判断后，由本地 Ollama 模型生成带原文引用的回答。支持 PDF / DOCX / PPTX / TXT / Markdown 五格式通用导入、可插拔 Qdrant 稠密索引、知识库/标签管理与按范围检索（QueryScope）。桌面和手机共用响应式 Web 界面，内容无需上传云端。

## 当前状态

| 项 | 值 |
|---|---|
| 版本线 | **V4**（Development Active） |
| 当前发布 | `v4.0.0-alpha.2`（Development Snapshot / GitHub Pre-release，**NOT V4 Final**） |
| 当前治理 / 状态基线 | `V4_6_2_HASH_PORTABILITY_BASELINE` |
| 产品指标来源 | `V4_6_1_EMBEDDING_IDENTITY_BASELINE`（`metrics_recomputed_in_v4_6_2 = false`） |
| REMOTE_CI | **PASS**（fresh LF GitHub Actions checkout） |
| 下一产品阶段 | `V4.7 — Document Identity Root-Cause Confirmation` |
| Product Quality DoD | **NOT_YET_PASS** |

V4 仍在积极开发中。本快照可用于试用与评测复现，但**尚未达到 V4 最终产品质量目标**，不应被视为最终稳定版本。

- 当前权威总控：[docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md](docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md)
- 发布说明：[docs/V4_RELEASE_SNAPSHOT.md](docs/V4_RELEASE_SNAPSHOT.md) · [CHANGELOG.md](CHANGELOG.md)
- 文档导航：[docs/INDEX.md](docs/INDEX.md)

## V4 Development Snapshot

已发布的，是当前 V4 开发状态的一个 **Development Snapshot / Pre-release**：

```text
CURRENT_RELEASE = v4.0.0-alpha.2
RELEASE_TYPE    = GitHub Pre-release
REMOTE_CI       = PASS（fresh LF GitHub Actions checkout）
```

> `v4.0.0-alpha.1` 因跨平台 CRLF/LF hash portability 问题被 supersede（tag/commit 保持不变）。

它表示：

- canonical 评测体系稳定、可复现；
- Scope/OOS 与 Routing over-trigger 各完成一轮 product remediation；
- Embedding Identity（`bge-m3` / 1024）已正式收编，并带启动期 fail-closed 校验；
- baseline lineage 与 live production drift guard 已建立；
- workspace relocation 与 publication scanner 的可移植性已收口。

它**不表示**：V4 已达标、Document Identity / History / Retrieval / Generation / Measurement / Citation 已完成。

## 系统架构概要

```text
PDF / DOCX / PPTX / TXT / Markdown
        → 解析归一（ParserRegistry → NormalizedDocument → Section / Chunk）
        → SQLite 知识库（FTS5 全文 + 向量）
        → 查询：Router → Scope/OOS 判定 → FTS5 + 向量召回 → RRF 融合
        → （可选 reranker，默认关闭）
        → qwen2.5:7b 生成 → 结构化引用 → 引用核验 → 浏览器工作台
```

- **检索**：SQLite FTS5（正文 + 标题双列，bm25 加权）与稠密向量双路召回，RRF 融合（语义 1.25 / 词法 1.0）；嵌入输入携带章节/小节路径；OCR 质量折扣、标题加分、近重复过滤、同小节限额。
- **路由**：确定性 rules-first；全书目录 / 全书介绍 / 单章概括 / 页码定位 / 比较 / 普通问答；书籍级问题不调用模型。
- **引用纪律**：范围展开、越界剔除、拉丁实体核验（先核验后重编号）；引用核验未通过会显式提示。
- **Scope**：知识库 / 文档 / 类型 / 标签范围从 UI → API → 检索 → 引用核验全链路贯穿，越界引用属严重失败。
- **多轮追问**：追问与上一问合并用于路由与检索，最近 3 轮对话进入模型消息。

更完整的组件说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 模型依赖

| 用途 | 模型 | 说明 |
|---|---|---|
| 回答 | `qwen2.5:7b` | Ollama 本地推理 |
| 向量 | `bge-m3` | **1024 维，生产默认** |

- 启动时执行 **fail-closed embedding identity 校验**：`配置模型 == 库中模型 == 向量维度`，任一不一致会抛 `EmbeddingIdentityError` 并**拒绝启动**。
- 不存在自动 re-embed、静默切换模型、自动重建 SQLite 库或 Qdrant 的行为。
- `nomic-embed-text`（768 维）仅作为**兼容 / 回滚**模型保留，**不是**当前生产默认，仅在显式设置 `QA_EMBEDDING_MODEL=nomic-embed-text` 时生效。

```powershell
ollama pull qwen2.5:7b
ollama pull bge-m3
```

## 快速启动

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

日常使用直接双击 `启动本地版.bat`。配置项（含 `LIBRARY_IMPORT_ROOTS`）、问法示例、多轮追问、手机访问与排错见 [本地使用说明](本地使用说明.md)。

## Vector Backend / 数据层

| 后端 | 角色 |
|---|---|
| **SQLite**（默认，`VECTOR_BACKEND=sqlite`） | 进程内暴力扫描，零依赖；**始终是 Source of Truth** |
| **Qdrant**（`VECTOR_BACKEND=qdrant`） | 可选的 service-backed 稠密索引，可完全从 SQLite 重建；不可用时显式报错，不静默回退 |

- **默认无需 Qdrant**；仅在选择 `qdrant` 时才需先运行 `scripts/rebuild_vector_index.py` 建索引、`scripts/verify_vector_index.py` 校验一致性。
- 受管知识库 `data/library/documents.sqlite3`（managed schema 5）是运行时真相源；legacy 教材库保留不删除。
- 运行时仅依赖 Python 标准库 + 本机 Ollama；建库另需 `requirements-ingest.txt`。

## 当前质量状态

当前 canonical Full-144 指标（机器事实源：`eval/v4_6_1_embedding_identity_baseline.json`）：

| 指标 | 当前值 | 最终 Target | 状态 |
|---|---:|---:|:--:|
| case_exact_fact_match_rate | 0.7292 | ≥ 0.80 | FAIL |
| fact_recall | 0.8535 | ≥ 0.90 | FAIL |
| false_refusal_rate | 0.0000 | ≤ 0.03 | PASS |
| citation_coverage | 0.4657 | ≥ 0.80 | FAIL |
| high_confidence_unsupported_rate | 0.0132 | ≤ 0.05 | PASS |
| invalid_citation_count | 0 | = 0 | PASS |
| citation_scope_violation | 0 | = 0 | PASS |

> **Product Quality DoD = NOT_YET_PASS**。质量接受合同见 [docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md](docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md)（Target 档已冻结，不因阶段性发布下调）。

## 已完成能力

- **Evaluation Integrity**：canonical evaluator + 单一 Golden（185 例，其中 144 answer-eligible）。
- **Failure Attribution framework**：逐 case 机械归因机制（持续刷新；不代表所有失败已解决）。
- **Scope/OOS remediation**（V4.4）：消除已证明的 in-scope false refusal，同时保持纯离题拒答（pure-OOS false accept = 0/7，scope leakage = 0）。
- **Routing over-trigger remediation**（V4.5）：修正 `LOCATION_WORDS` 对 locate route 的过触发。
- **Embedding Identity alignment**（V4.6.1）：生产身份统一为 `bge-m3 / 1024`，启动期 fail-closed 校验。
- **Baseline lineage**：不可变历史 stage baseline + 单一 current pointer。
- **Live production drift detection**：live production hash 必须等于 current baseline 记录值。
- **Workspace relocation portability**：数据库 / baseline / ImportPathPolicy 可移植，不再依赖旧绝对路径。
- **publication_scan workspace-path portability**：泄漏扫描规则由脚本位置动态推导，无硬编码路径。

## 已知限制 / 未完成项

- **Document Identity** — NEXT（`V4.7 — Document Identity Root-Cause Confirmation`，先诊断后修复）
- **History**（多轮改写） — PENDING
- **Retrieval**（RRF ranking miss） — PENDING
- **Generation**（证据送达但答案省略/拒答） — PENDING
- **Measurement Closure**（Golden / Evaluator） — PENDING
- **Citation Coverage** — PENDING / DEFERRED

其余 deferred 非阻断项：KB Summary / Multi-document Summary / 文档级元数据查询 / 生产 L2 verifier / Rich Citation UX / Performance SLA / Reranker 重新启用。

## 测试与评测

不需要教材和 Ollama：

```powershell
python -B -m unittest discover -v
python -B -m compileall -q core desktop scripts tests
python -X utf8 scripts/eval_phase_e_router.py
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

V4 governance 关键回归：`python -m unittest tests.test_live_production_hash_guard -v`（live production hash 漂移侦测，必须 PASS）。

## 文档导航

| 文档 | 说明 |
|---|---|
| [docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md](docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md) | V4 权威总控：需求 / 状态 / 路线 / Gate |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 当前真实架构（不含 roadmap） |
| [docs/INDEX.md](docs/INDEX.md) | docs 总导航（当前文档 / 发布文档 / 诊断参考 / 历史证据 / 机器证据） |
| [本地使用说明.md](本地使用说明.md) | 本地运行、配置与排错 |
| [docs/V4_RELEASE_SNAPSHOT.md](docs/V4_RELEASE_SNAPSHOT.md) | 本次 Development Snapshot 发布说明 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |

## Release / Changelog

- 当前接受版本：**`v4.0.0-alpha.2`**（Development Snapshot / GitHub Pre-release，**NOT V4 Final**；remote CI PASS）。
- 变更记录见 [CHANGELOG.md](CHANGELOG.md)；发布说明见 [docs/V4_RELEASE_SNAPSHOT.md](docs/V4_RELEASE_SNAPSHOT.md)。

## 项目结构

```text
core/                    检索、知识库、向量后端、导入、QueryScope、问答引擎
desktop/                 本地 Web 服务（v2 API + v3 Library API）与桌面启动入口
web/                     响应式浏览器界面（问答页 + 知识库管理页）
scripts/                 导入/建库/迁移、索引 rebuild/verify、评测与回归
tests/                   单元与集成测试（不依赖真实教材；服务可达时跑集成）
docs/                    架构说明、V4 总控与发布说明、阶段计划与历史证据
reranker_service/        可选 Reranker sidecar（自带独立环境）
data/pdf|raw|library/    教材、提取文本、知识库（本地数据，不入库）
```

## Repository / License

仓库当前已公开，但尚未附带开源许可证。

如希望明确允许他人复制、修改或分发代码，请根据你的授权意图选择并添加 LICENSE。在未附带许可证的情况下，代码仍默认保留全部版权。
