# V3 Final Baseline（冻结锚点）

> 本文是 KB-V3 的**冻结锚点**，不是重复 Master Status。它记录 V3 开发周期结束时的不可变事实，作为后续 V4 的起点与可追溯基线。

## Freeze Statement

```text
V3 DEVELOPMENT CYCLE     = CLOSED / FROZEN
V3 IMPLEMENTATION BASELINE = FROZEN
```

V3 的 active development cycle 已结束。本 baseline 之后，**不再修改 V3 的 production behavior**。未完成工作保留在 `docs/V3_MASTER_REQUIREMENTS_AND_STATUS.md`，未来版本可继承。

## V3 Final Source Baseline

- V3 FINAL SOURCE COMMIT：`b6164115ff72b0187fe2d6deaf6b3a35011deecf`（GitHub `main` 分支）
- Git publish workspace：`Local Database Q&A System上传版`
- GitHub：`https://github.com/wt7439216/local-database-qa-system`（分支 `main`）
- CI：`34439230553` = success（freeze 提交）

## Final Tests

```text
unit tests            = 511 OK (skipped=26)
Phase E router eval   = 108/108 PASS
F.2 citation eval     = 37/37 PASS
ruff / compileall     = clean
```

## Final Runtime Package（本地运行包，非 Git 资产）

```text
runtime\LocalDatabaseQA\LocalDatabaseQA.exe
timestamp = 2026-09-10 12:27
size      ≈ 2.25 MB
launcher  = 启动本地版.bat
knowledge base = 617 chunks / 1024 dimensions
```

> EXE / runtime 默认不进入 Git。V3 Source Baseline 与本地 Runtime Package 分别冻结。
> 已知非阻断打包 warning：PyInstaller/pygame 子进程 stdout `UnicodeDecodeError: 'gbk'`（不影响产物生成）。

## Quality Contract

```text
version = v1.0
status  = FROZEN
frozen_by = explicit user authorization
```

正式 Product Gate 与当前结果：

| Metric | Threshold | Current | Status |
|---|---:|---:|---|
| case_exact_fact_match_rate | >= 0.80 | 0.7014 | FAIL |
| fact_recall | >= 0.90 | 0.8248 | FAIL |
| false_refusal_rate | <= 0.03 | 0.0278 | PASS |
| citation_coverage | >= 0.80 | 0.5524 | FAIL |
| high_confidence_unsupported_rate | <= 0.05 | 0.0161 | PASS |

```text
2 / 5 PASS
Product Quality DoD = NOT_YET_PASS
```

## 最终状态

```text
Engineering Closure       = PASS
Evaluation Infrastructure = PASS
Quality Contract          = FROZEN v1.0
Quality Baseline          = FROZEN
Product Quality DoD       = NOT_YET_PASS
V3 Release Readiness      = CONDITIONALLY_READY
```

## 已完成 Workstream（摘要）

```text
Q1 / Q1.1 = PASS
Q2        = FAIL / ROLLED BACK
Q3 / Q3.1 = PASS
Q2.2      = INSUFFICIENT
Q4.0      = PASS
Q4.1      = SYNTHESIS_ONLY_INSUFFICIENT
Q4.2      = PASS
```

## Known Unfinished Work（继承到未来版本）

- Q4.3a Multi-turn History / Reference Resolution
- Q4.3b True Retrieval Miss
- Q4.3c Multi-document Document Identity
- Evaluator Fact Matcher Audit
- Golden Contract Review
- Citation Coverage（Product Gate 未过）

## Master Status Document

```text
docs/V3_MASTER_REQUIREMENTS_AND_STATUS.md
```

## Freeze 说明

- 本文只记录 V3 最终事实，不规划 V4，不创建 V4 roadmap / requirements / progress。
- 未完成项不因 V3 冻结而删除，保留在 Master Status 中供未来版本继承。
- 未来版本由用户自行复制冻结后的 V3 工作区作为起点。
