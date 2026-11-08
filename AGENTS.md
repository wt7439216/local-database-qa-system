# 当前工作目录

这里是用户指定的 V4.1 活跃开发目录，**也是 P5 之后唯一的 git 仓库**。原「上传版」发布镜像（旧 `.git`、`PUBLICATION_EVIDENCE.json`、V3/V4 阶段文档与冻结证据）已完整归档到 `Archive/20261109_p5_convergence/`；发布走 `git tag` + GitHub Actions + Release asset，不再同步第二份源码副本。

程序及 EXE 版本仍为 `4.0.0-alpha.3`（`pyproject.toml` 中 `version = "4.0.0a3"`）。三项 Full-144 产品质量指标仍待 Ollama 实测，**不要因目录叫 v4.1 就把历史版本、验收结论或 EXE manifest 改成 4.1**。

- `V4.1迁移说明.md` 与 `docs/ARCHITECTURE.md` 是环境与当前架构的说明；`docs/INDEX.md` 是文档导航。历史阶段文档在 `Archive/` 下，均非当前验收约束。
- 日常双击 `启动V4.1.bat`；源码使用 `启动V4.1源码.bat`。PowerShell 入口支持 `-ValidateOnly`、`-NoBrowser`、`-Port`、`-ListenAddress`。源码环境为本目录 `.venv`（Python 3.12.13）；**依赖单一真源是 `pyproject.toml`**（`pip install -e ".[dev,modern]"`），`requirements*.txt` 是构建脚本使用的冻结镜像。
- 模型在本目录 `model/`，Ollama 是外部程序；`OLLAMA_MODELS` 指向此处，实际模型为 `bge-m3:latest` 与 `qwen2.5:7b`。不要自动换模型、重嵌入或重建已有库。
- 源码使用 `data/library/documents.sqlite3`；EXE 使用 `runtime/LocalDatabaseQA/_internal/data/library/documents.sqlite3`。两份数据互不自动同步，修改前先确认运行方式。候选指针由 `scripts/activate_candidate.py` 生成。
- **单验收入口**：`make check`（Windows 无 make 时 `powershell -File scripts/check.ps1`）→ `scripts/verify_all.py`，覆盖 10 项 CI 门禁 + 双栈契约 + 候选校验 + git 状态；`--full` 另加覆盖率与启动冒烟。CI 与本地完全一致。
- **打包**：`python -X utf8 scripts/build.py --plan` 查看计划，`make build` 打包到 gitignored 的 `dist/` 与 `build/`。旧 `-ExpectedProductionHash` / `-QualityEvidence` / `-Preflight` / `-SkipIndex` 已不再需要。
- **历史回滚**：`Archive/20261107_refactor_unbind/RESTORE.ps1`（142 项历史绑定资产）与 `Archive/20261109_p5_convergence/RESTORE.ps1`（P5 退役脚本）均可用。冻结源码修订治理、`publication_*` 双副本同步与一次性诊断脚本已在 P5 归档，不再是运行时的一部分。

常用检查（在本目录执行，全部不需要 Ollama）：

```powershell
make check
# 或：powershell -File scripts/check.ps1
# 或仅 10 项门禁：.\.venv\Scripts\python.exe -X utf8 scripts/check_all.py
```

P1/P2 分层：`desktop/web_server.py` 是组合根，实现位于 `desktop/{jobs,auth,answer_cache,transport,routes_v3,handler,worker}.py`；HTTP 契约真源是 `desktop/api_contract.py`（生成 `docs/openapi.json`）。改路由时先更新契约与 `scripts/capture_contract.py`，再改实现，并跑两个 backend。

P3：默认 HTTP 栈仍是标准库零依赖，但有 `QA_ANSWER_WORKERS` 个并发 worker（epoch 缓存一致性）、标准 SSE、ESM 前端（`web/shared.js`）与可选 FastAPI 栈（`python -m desktop --modern`）。取消/超时通过 `AnswerJob.is_cancelled` 透传到 `core/http_client.py`，不要重新引入全局引擎锁。

P4：质量攻坚的开关（`QA_FTS_DICTIONARY` / `QA_VECTOR_ANN` / `QA_STRUCTURED_ANSWERS` / `QA_CITATION_L15`，详见 `core/config.py`）**默认全部关闭**，新增能力必须保持「默认行为 + 零依赖」不变。改 prompt 必须同步 `eval/prompt_contract_baseline.json`；启用词典分词必须重建 `chunk_fts`；ANN 当前标定结论是暂不默认启用。

P5：工程元数据、依赖分组与 ruff/coverage/pytest 配置统一在 `pyproject.toml`；`Makefile` + `scripts/verify_all.py` 是唯一验收入口；`scripts/build.py` / `scripts/activate_candidate.py` 简化打包与指针；`LICENSE` 记录许可状态（专有，未授予开源许可）。不要再新增 `publication_*` 或第二份源码副本。

`core/engine_v2.py` 与 `core/library_service.py` 也是兼容门面：domain 在 `core/domain/`，用例在 `core/application/ask_question.py`，迁移链在 `core/migrations/`，事务/outbox/仓库/状态机在 `core/persistence/`。检索参数统一在 `core/retrieval_config.py`（`config.RETRIEVAL`）。写文档生命周期时必须在同一 `UnitOfWork` 事务内登记 `IndexOutbox` 事件；索引同步失败走 `_dispatch_index_event()` 延迟重放。共享基础设施在 `core/{config,tokenizer,hashing,db,library_model}.py`。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\启动V4.1.ps1 -ValidateOnly
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\启动V4.1源码.ps1 -ValidateOnly
```

完整可重复验证（含重构探针）见 `Archive/20261107_refactor_unbind/refactor_tool.py`。
