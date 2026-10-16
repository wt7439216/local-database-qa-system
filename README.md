# Local Database QA

一个完全本地运行、答案可追溯到原文位置的教材/文档问答系统。

> 本仓库（公开版）包含源码、测试、文档与评测证据；评测证据可包含问题、模型答案和少量教材短引文。完整私有教材、SQLite 知识库、日志、模型与 Windows 运行包不随源码发布，评测工件不包含完整知识库或高维向量。首次使用需自行导入文档；日常配置见 [本地使用说明](本地使用说明.md)。

系统把 PDF 整理成单个 SQLite 知识库，使用 FTS5 全文检索与向量检索双路召回，经 RRF 融合、质量加权和范围判断后，由本地 Ollama 模型生成带原文引用的回答。支持 PDF / DOCX / PPTX / TXT / Markdown 五格式通用导入、可插拔 Qdrant 稠密索引、知识库/标签管理与按范围检索（QueryScope）。桌面和手机共用响应式 Web 界面，内容无需上传云端。

## 当前状态

当前状态入口为 [docs/V4_CURRENT_STATE.md](docs/V4_CURRENT_STATE.md)。本地活跃开发以 **V4 本地版**为准；上传版在实际发布时同步。

| 项 | 值 |
|---|---|
| 版本线 | **V4**（Development Active） |
| 本次源码快照 | `v4.0.0-alpha.3`（Development Snapshot / GitHub Pre-release，**NOT V4 Final**） |
| 当前生产源码基线 | `V4_20261015_LOCAL_CANDIDATE_BASELINE`（新候选 Full144 已完成，产品质量 FAIL） |
| 产品指标来源 | 本轮新候选：事实全对率 72.92%、事实召回率 84.71%、引用覆盖率 58.95%；三项未达标 |
| 发布 CI | 以 [GitHub Actions](https://github.com/wt7439216/local-database-qa-system/actions) 对应 tag / commit 的实际结果为准；本地测试不能替代远端结果 |
| 最近完成诊断 / 治理阶段 | `V4.8.2` 诊断结案及 `Post-V4.8.2 Priority Review`；Generation 因果机制仍未建立 |
| 最近本地工程记录 | 发布派生前 1707 项测试，0 failures、0 errors、26 skipped；本次公开检查另列 |
| 快照内容 | 缓存一致性、数字材料头、新基线、Full144 与本地运行包构建工具；[修复及交付记录](docs/V4_PROD_EVAL_REL_20261015.md) |
| Product Quality DoD | **NOT_YET_PASS** |

V4 仍在积极开发中。本快照可用于试用与评测复现，但**尚未达到 V4 最终产品质量目标**，不应被视为最终稳定版本。

> 本次公开源码来自 V4 本地版冻结候选，生产哈希为 `bef1a9414eaa168702724b982e48338fbaa858661ac1cb1863af842ef7937b6d`。
> 公开副本的路径处理与历史证据重放边界见 [发布记录](docs/V4_PUBLICATION_20261016.md) 和 [发布说明](docs/V4_RELEASE_SNAPSHOT.md)；实际 commit、tag 与发布状态以 [GitHub Releases](https://github.com/wt7439216/local-database-qa-system/releases) 为准。

- 当前开发状态与证据：[docs/V4_CURRENT_STATE.md](docs/V4_CURRENT_STATE.md)
- 需求与治理路线：[docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md](docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md)（正文保留 2026-09-16 历史检查点）
- 发布说明：[docs/V4_RELEASE_SNAPSHOT.md](docs/V4_RELEASE_SNAPSHOT.md) · [CHANGELOG.md](CHANGELOG.md)
- 文档导航：[docs/INDEX.md](docs/INDEX.md)

## V4 Development Snapshot

本次源码快照定位为 **Development Snapshot / Pre-release**：

```text
CURRENT_SNAPSHOT = v4.0.0-alpha.3
RELEASE_TYPE    = GitHub Pre-release
REMOTE_CI       = 查看对应 tag / commit 的 GitHub Actions 结果
```

> `v4.0.0-alpha.1` 因跨平台 CRLF/LF hash portability 问题被 supersede（tag/commit 保持不变）。

它表示：

- canonical 评测体系稳定、可复现；
- Scope/OOS 与 Routing over-trigger 各完成一轮 product remediation；
- Embedding Identity（`bge-m3` / 1024）已正式收编，并带启动期 fail-closed 校验；
- baseline lineage 与 live production drift guard 已建立；
- 答案缓存与库刷新保持一致，显式空范围和取消窗口有回归覆盖；
- 模型材料头统一使用数字引用格式，当前 Full144 已独立重测；
- 发布扫描、同步清单及公开证据处理规则见本次发布记录。

产品质量仍有三项 FAIL。数字材料头修复只得到具体输入及干预范围内的支持，不能据此宣称所有生成或引用问题已解决。

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
# 1. 建立独立环境并安装导入依赖（完整 OCR 使用 Python 3.12）
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-ingest.txt

# 2. 启动本机 Ollama 并安装模型，再导入你自己的文档
ollama pull qwen2.5:7b
ollama pull bge-m3
python -X utf8 scripts/import_document.py --file path/to/your-doc.md --kb kb-default

# 3. 源码运行，按终端提示打开本机地址并配对
python -m desktop
```

公开源码不包含预建知识库，也不包含已激活的 EXE 指针。`python -m desktop` 使用本机 managed 库；导入命令默认在 `data/library/documents.sqlite3` 创建或更新它。`启动本地版.bat` 需要另行构建、验证并激活本地候选，不能在新克隆中直接当作成品运行包入口。

开发环境另有已验证的 alpha.3 Windows 包，绑定 6 文档 / 637 块的私有库快照；该库与 EXE 均不作为本次 GitHub 附件上传。构建流程只读复制已核验的 managed 库，不自动重建、合并或重嵌入。完整 OCR 和 PyInstaller 构建使用独立 Python 3.12 环境，详见 [本地使用说明](本地使用说明.md)。配置项（含 `LIBRARY_IMPORT_ROOTS`）、问法示例、多轮追问、手机访问与排错也见该文档。

## Vector Backend / 数据层

| 后端 | 角色 |
|---|---|
| **SQLite**（默认，`VECTOR_BACKEND=sqlite`） | 进程内暴力扫描，零依赖；**始终是 Source of Truth** |
| **Qdrant**（`VECTOR_BACKEND=qdrant`） | 可选的 service-backed 稠密索引，可完全从 SQLite 重建；不可用时显式报错，不静默回退 |

- **默认无需 Qdrant**；仅在选择 `qdrant` 时才需先运行 `scripts/rebuild_vector_index.py` 建索引、`scripts/verify_vector_index.py` 校验一致性。
- 受管知识库 `data/library/documents.sqlite3`（managed schema 5）是运行时真相源；legacy 教材库保留不删除。
- 运行时仅依赖 Python 标准库 + 本机 Ollama；建库另需 `requirements-ingest.txt`。

## 当前质量状态

本次候选的 canonical Full-144 指标（2026-10-16 完成；机器事实源：[eval/v4_local_candidate_full144_20261015.json](eval/v4_local_candidate_full144_20261015.json)，144 条新答案）：

| 指标 | 当前值 | 最终 Target | 状态 |
|---|---:|---:|:--:|
| case_exact_fact_match_rate | 0.7292 | ≥ 0.80 | FAIL |
| fact_recall | 0.8471 | ≥ 0.90 | FAIL |
| false_refusal_rate | 0.0069 | ≤ 0.03 | PASS |
| citation_coverage | 0.5895 | ≥ 0.80 | FAIL |
| high_confidence_unsupported_rate | 0.0164 | ≤ 0.05 | PASS |
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

- **Document Identity** — 已由 V4.7 结案：当前 pipeline 中 canonical document title 全程可见，**Document Identity Loss = DISPROVEN**；identity remediation **BLOCKED**
- **Generation / Prompt-Evidence Framing** — V4.8 / V4.8.1 / V4.8.2 已结案；`GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED`，未建立 shared causal mechanism；V4.7 的 `MATERIAL_INDEX_REPRESENTATION_BIAS` 属于当时阶段表述
- **Measurement 语义（独立轨道）** — `MEASUREMENT_SEMANTIC_ISSUE = SUPPORTED`（canonical title vs Golden 角色词），不得并入 Product remediation
- **History**（多轮改写） — PENDING
- **Retrieval**（RRF ranking miss） — PENDING
- **Generation**（证据送达但答案省略/拒答） — PENDING
- **Measurement Closure**（Golden / Evaluator） — PENDING
- **Citation Coverage** — 当前 Full144 为 0.5895，仍低于 0.80；材料不足类引用、定位信息遗漏及部分多轮问题仍待处理

其余 deferred 非阻断项：KB Summary / Multi-document Summary / 文档级元数据查询 / 生产 L2 verifier / Rich Citation UX / Performance SLA / Reranker 重新启用。

## 测试与评测

以下工程检查不需要私有教材和 Ollama。现有 GitHub workflow 使用 Python 3.13 / Node 22，安装 PyMuPDF、python-docx 与 python-pptx；不安装不支持 Python 3.13 的 RapidOCR 1.4。因此该 CI 不等于完整 OCR 或 Windows EXE 验收。

```powershell
python -B -m unittest discover -v
python -B -m compileall -q core desktop scripts tests
python -X utf8 scripts/eval_phase_e_router.py
python -X utf8 scripts/eval_phase_f_citation.py
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

开发环境最近一次完整结果为 2026-10-16 的 1707 项、0 failures、0 errors、26 skipped。这是本地历史记录；公开 fresh checkout 的测试数量、跳过原因和远端结果分别按实际执行记录，不能直接沿用该数字。私有数据、可选服务及未公开参考协议不随仓库提供；匿名化成员所需的精确原字节不可公开重放时会明确报告，不计作执行通过，见 [公开证据策略](docs/V4_PUBLICATION_20261016.md)。

## 文档导航

| 文档 | 说明 |
|---|---|
| [docs/V4_CURRENT_STATE.md](docs/V4_CURRENT_STATE.md) | 当前本地开发位置、工程结果、WS-13、产品指标、EXE 与发布身份 |
| [docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md](docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md) | V4 需求 / 路线 / Gate；历史检查点正文与当前状态入口分开 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 当前真实架构（不含 roadmap） |
| [docs/INDEX.md](docs/INDEX.md) | docs 总导航（当前文档 / 发布文档 / 诊断参考 / 历史证据 / 机器证据） |
| [本地使用说明.md](本地使用说明.md) | 本地运行、配置与排错 |
| [docs/V4_RELEASE_SNAPSHOT.md](docs/V4_RELEASE_SNAPSHOT.md) | 本次 Development Snapshot 发布说明 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |

## Release / Changelog

- 本次源码快照：**`v4.0.0-alpha.3`**（Development Snapshot / GitHub Pre-release，**NOT V4 Final**）。实际发布与 CI 状态见 [Releases](https://github.com/wt7439216/local-database-qa-system/releases) 和 [Actions](https://github.com/wt7439216/local-database-qa-system/actions)。
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
