# docs — 文档导航索引

> **历史治理解锁（2026-11-07）**：历史阶段文档、发布记录、诊断证据与治理注册表已归档到
> `Archive/20261107_refactor_unbind/`。**单仓库收敛（2026-11-09, P5）**：原「上传版」发布镜像、
> `publication_*` 双副本同步机制与冻结治理脚本已归档到 `Archive/20261109_p5_convergence/`。
> 本索引只保留当前有效入口；需要历史资料请查对应目录的 `ARCHIVE_MANIFEST.json`，或用 `RESTORE.ps1` 完整回滚。

## 当前入口

| 文档 | 用途 |
|---|---|
| [`../README.md`](../README.md) | 项目第一入口：当前状态、模型依赖、快速启动、测试与评测、文档导航。 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 当前真实架构（查询流 / Router / Scope / Retrieval / Embedding Identity / 后端 / Citation / 评测），以及「源码身份与历史治理已解锁」说明。 |
| [`../本地使用说明.md`](../本地使用说明.md) | 本地运行、配置、排错、手机访问、打包说明。 |
| [`../CHANGELOG.md`](../CHANGELOG.md) | 版本变更记录。 |
| [`../AGENTS.md`](../AGENTS.md) | 活跃开发目录的操作约束与常用检查命令。 |
| [`../pyproject.toml`](../pyproject.toml) | 元数据、依赖分组与工具配置的单一真源。 |
| [`../Makefile`](../Makefile) | `make check` / `make build` / `make smoke` 等统一入口。 |
| [`../LICENSE`](../LICENSE) | 许可状态（专有 / 未授予开源许可）。 |
| [`openapi.json`](openapi.json) | v2/v3 HTTP 契约（OpenAPI 3.1 + JSON Schema）。 |

## 当前机器可读输入

| Artifact | 用途 |
|---|---|
| [`../eval/phase_e_router_golden.json`](../eval/phase_e_router_golden.json) | Phase E Router 确定性评测（108 例）。 |
| [`../eval/phase_f_citation_golden.json`](../eval/phase_f_citation_golden.json) | Phase F.2 引用核验评测（37 例）。 |
| [`../eval/v3_final_golden.json`](../eval/v3_final_golden.json) | canonical Golden（185 例 / 144 answer-eligible）。 |
| [`../eval/v4_baseline_lineage.json`](../eval/v4_baseline_lineage.json) | 历史 baseline lineage（仅作历史记录，不再约束 live 源码）。 |

## 解锁后的验证

```powershell
make check                 # P5 单一入口；Windows 无 make 用 scripts/check.ps1
# 或仅门禁：python -X utf8 scripts/check_all.py
```

可重复的完整验证与「模拟改动 core 源码」的重构探针见
`Archive/20261107_refactor_unbind/refactor_tool.py` 及同目录验证报告。
