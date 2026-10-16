# V4 Release Snapshot — v4.0.0-alpha.3

本次为 **Development Snapshot / GitHub Pre-release，NOT V4 Final**。日期：2026-10-16（Asia/Shanghai）。产品质量仍有三项 FAIL，工程验收与打包成功不改变这一状态。

```text
SOURCE_SNAPSHOT       = v4.0.0-alpha.3
RELEASE_TYPE          = Development Snapshot / GitHub Pre-release
PRODUCT_QUALITY_DOD   = NOT_YET_PASS
V4_FINAL              = NO
```

实际发布状态、commit、tag 与时间以 [GitHub Releases](https://github.com/wt7439216/local-database-qa-system/releases) 元数据为准。发布 CI 以 [GitHub Actions](https://github.com/wt7439216/local-database-qa-system/actions) 对应 tag / commit 的运行结果为准；本页不将历史本地结果充作本次远端 CI 成绩。

## 源码与测量身份

当前基线为 `V4_20261015_LOCAL_CANDIDATE_BASELINE`，机器指针见 [baseline lineage](../eval/v4_baseline_lineage.json)。生产源码范围为 `core/desktop/web`，使用 `sha256-path-content-v2-canonical-lf`：

```text
bef1a9414eaa168702724b982e48338fbaa858661ac1cb1863af842ef7937b6d
```

PROD-01 缓存阶段为独立父节点，PROD-02 数字材料头阶段随后追加，再登记本次新 Full144 测量节点。旧五项基线及历史 WS-13 结论保留，未改写为本次产品修复或人工接受。

回答模型为 `qwen2.5:7b`；嵌入模型 `bge-m3 / 1024`；默认 SQLite，reranker 关闭。嵌入身份启动校验为 fail-closed，不自动重嵌入、换模型、重建库或 Qdrant。

Full144 在开发环境的 managed 库上测量，明确指定 6 文档、637 块的原始快照；这不是公开克隆内置的数据。该 SQLite 原始 SHA256 为 `c6bc9b3eb63ae4e6d96caf859a2b0c5f2f1e5a5b6f438e81aa0bbc3cf4084c97`，原库未由打包或发布流程改写。

## 本次包含的产品变更

- 缓存查找、回答生成、序列化与提交和库刷新共用锁，阻断缓存清空后旧结果回写。区分显式空范围与默认范围，并覆盖取消窗口。
- 模型材料头改为 `[1] 位置` 形式，与数字引用格式一致。独立固定 12 次 A/B/C 调查支持当前具体输入及干预范围内的修复。
- Golden、canonical evaluator、verifier、质量门槛未修改；检索算法、材料正文及顺序未为该格式修复改动。材料头变短可能使临界字符预算多容纳尾块，不能宣称所有问题的材料集合恒等。
- 更新工程隔离、历史源码重放、当前漂移校验与 Windows 构建工具。详细范围和已披露的验证偏差见 [本地候选执行记录](V4_PROD_EVAL_REL_20261015.md)。

旧 WS-13 三次回答只有材料标签的观察保持原身份。后来三次定向 engine 验证实际使用 legacy 库的偏差也保留披露，没有改称 managed 证据；本次 managed 效果由显式绑定库的新 Full144 支持。

## 新候选质量结果

本次使用未修改的 canonical evaluator，生成 144 条新答案；机器事实源为 [v4_local_candidate_full144_20261015.json](../eval/v4_local_candidate_full144_20261015.json)。20261015 为冻结和阶段编号，实际完成于 2026-10-16。

| 指标 | 当前值 | 冻结 Target | 结果 |
|---|---:|---:|:--:|
| case_exact_fact_match_rate | 0.7292（105/144） | ≥ 0.80 | FAIL |
| fact_recall | 0.8471（266/314） | ≥ 0.90 | FAIL |
| false_refusal_rate | 0.0069（1/144） | ≤ 0.03 | PASS |
| citation_coverage | 0.5895 | ≥ 0.80 | FAIL |
| high_confidence_unsupported_rate | 0.0164 | ≤ 0.05 | PASS |
| invalid_citation_count | 0 | = 0 | PASS |
| citation_scope_violation | 0 | = 0 | PASS |

相对旧 V4.6.1，完整事实命中数不变、事实总命中少 2 个、引用覆盖增加 12.38 个百分点。源码变化与生成随机性同时存在，不把所有差异归因于一行材料头修改，也不将未达标状态改成 PASS。

另完成 41 项非回答补充及范围隔离专项 34/34 PASS。41 项含元数据模板，不能全部当作事实拒答分母；范围隔离通过也不能代替语义拒答质量。定位信息、mt-006 指代误拒、比较及多文档实体遗漏、材料不足类引用仍待处理。质量接受合同见 [V3_QUALITY_ACCEPTANCE_CONTRACT.md](V3_QUALITY_ACCEPTANCE_CONTRACT.md)，门槛未下调。

## 工程检查与公开验证范围

开发环境 2026-10-16 最近一次完整 unittest 为 **1707 项，0 failures、0 errors、26 skipped**，同时通过 Ruff、编译、三个浏览器 JavaScript 检查和 Phase E/F.2 离线评测。这是本次公开派生之前的本地工程记录，不能直接充作 fresh checkout 或远端 CI 的结果。

上传版原有 `.github/workflows/ci.yml` 为独有资产，由同步流程保留。当前 workflow 使用 Windows、Python 3.13、Node 22，安装 PyMuPDF、python-docx 和 python-pptx，执行 lint、完整 unittest、compileall、JS 和 Phase E/F.2。RapidOCR 1.4 不支持 Python 3.13，未被该 workflow 安装；完整 OCR 与 EXE 验收使用独立 Python 3.12 构建环境。

公开 fresh checkout 没有私有知识库、Ollama 模型、Qdrant、reranker 或未公开参考协议；实际测试数量、跳过原因及 CI 状态应分别读取本次执行证据。Phase E/F.2 可离线运行，无法代替基于私有库的 canonical Full144 重新推理。

公开路径处理产生独立派生副本时，原始身份与公开字节身份分别在 `PUBLICATION_EVIDENCE.json` 登记。公开脱敏副本不能冒称私有原件的逐字节重放；保留的原始哈希是 provenance，并不表示原件已公开。依赖匿名化成员精确私有原字节的历史重放会明确报告 `PrivateHistoricalInputUnavailable`，不计作执行通过；纯算法与当前生产行为检查继续运行。不得通过替换哈希函数、弱化 live guard 或重写旧科学结论制造通过。具体转换、扫描和同步结果见 [发布记录](V4_PUBLICATION_20261016.md)。

## 源码发布与本地运行包

本次 GitHub 发布包含源码、测试、文档及经过审阅的公开评测证据。评测证据可包含问题、模型答案与少量教材短引文；不宣称公开仓库完全没有文档内容。审阅未发现完整教材、完整知识库或高维向量。**不上传完整私有教材、SQLite、运行日志、缓存、模型、EXE / ZIP 资产或本机激活指针**。

干净克隆需先在本机安装 Ollama 与模型，并导入用户自己的文档创建 managed 库，再运行 `python -m desktop`。请按 [README 快速启动](../README.md#快速启动) 操作；公开克隆不能直接使用开发机的 `启动本地版.bat` 激活指针。

开发环境另已构建并验证 alpha.3 Windows 包，支持五格式与扫描 PDF OCR，携带上述 6 文档 / 637 块私有库的精确快照；该包没有作为本次 GitHub Release 资产公开。包首次启动的摘要来源兼容迁移和运行库身份与原始测量快照分列，未冒称为另一次 Full144 测量。

## 历史版本与后续工作

`v4.0.0-alpha.2` 为此前已发布的 hash portability 快照，其历史远端 CI 为 PASS。`v4.0.0-alpha.1` 曾因 CRLF/LF raw-byte 身份缺陷被 alpha.2 supersede；旧 tag / commit 保持不可变。历史指标保留，不替换成本次成绩。

V4 继续开发。Document Identity Loss 在特定历史 pipeline 中被 DISPROVEN；Generation shared mechanism 仍未建立。History、Retrieval、Generation、Measurement Closure 和 Citation 残留应按各自证据继续处理。本快照可用于试用和公开工程复现，不代表最终稳定产品。

相关文档：[当前状态](V4_CURRENT_STATE.md) · [CHANGELOG](../CHANGELOG.md) · [文档索引](INDEX.md) · [本地使用说明](../本地使用说明.md)。
