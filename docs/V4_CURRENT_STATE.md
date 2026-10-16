# V4 当前本地开发状态

状态日期：2026-10-16（Asia/Shanghai）。活跃版本为 **V4 本地版**；本次 PUB-01 / PUB-02 从独立公开候选同步上传版，发布目标为 **v4.0.0-alpha.3 Development Snapshot**。此前 PROD-01、PROD-02、BASE-01、EVAL-01、REL-01 的详细证据与限制见[产品执行记录](V4_PROD_EVAL_REL_20261015.md)。公开内容与历史身份策略见[发布说明](V4_PUBLICATION_20261016.md)。

| 维度 | 当前身份 / 状态 |
|---|---|
| 当前生产源码基线 | V4_20261015_LOCAL_CANDIDATE_BASELINE；[lineage](../eval/v4_baseline_lineage.json) |
| canonical production source hash | `bef1a9414eaa168702724b982e48338fbaa858661ac1cb1863af842ef7937b6d`，core / desktop / web |
| managed 主库 | documents.sqlite3，6 文档 / 637 块，bge-m3 / 1024，原库未改写 |
| 回答模型 / 后端 | qwen2.5:7b / SQLite，reranker 关闭 |
| 产品质量 | 新候选 Full144 已完成：72.92% / 84.71% / 58.95%，三项未达标，不标 V4 Final |
| 既有本地完整工程结果 | PROD / EVAL 阶段 1707 项，0 failures、0 errors、26 skipped；不代替本次公开 checkout 的实际结果 |
| 本地候选包 | 4.0.0-alpha.3 已完成 EXE smoke 与真实根启动器验收，候选指针已激活 |
| 本次源码发布目标 | v4.0.0-alpha.3，Development Snapshot / Pre-release；实际公开状态见 [GitHub Releases](https://github.com/wt7439216/local-database-qa-system/releases) |
| 上传版提交与 CI | 独立公开派生候选；提交与状态见 [main](https://github.com/wt7439216/local-database-qa-system/tree/main) 及 [Actions](https://github.com/wt7439216/local-database-qa-system/actions)；私有库与本地包不随源码发布 |

缓存修复已落地，阻断清空后旧结果回写，隔离显式空范围并覆盖取消。数字材料头修复由独立预注册的 12 次 A/B/C 调查支持；生产只改一行材料头，保持检索、材料正文、顺序、Golden、evaluator 和 verifier 不变。不能由此推断全局生成机制或所有引用问题已解决。材料不足类 unsupported 引用仍是残留问题。

另行三次真实 pipeline 验证实际使用 legacy 库（1 文档 / 617 块），该偏差已披露，旧计划与结果未改写为 managed 证据。新验证脚本显式绑定库，默认 managed；当前主库效果由明确指定 documents.sqlite3 的统一评测验证。

STATE-01、ENG-01～04 的来源见[工程恢复登记](../eval/v4_engineering_recovery_20261014.json)，STATE-02、DIAG-01～04 见[来源登记](../eval/v4_ws13_20261014_source_revision.json)与[归因说明](V4_WS13_FRESH_ATTRIBUTION_20261015.md)。WS-13 原归因为 NOT_ESTABLISHED_DUE_TO_CONFOUND，G6 为 R3 / FRESH_ATTRIBUTION；[G4](../eval/v4_ws13_g4_observations_20261015.json)、[G5](../eval/v4_ws13_g5_attribution_20261015.json)、[G6](../eval/v4_ws13_g6_readiness_20261015.json)保留原身份，本轮独立产品工作不改写其历史科学结论或人工接受状态。

源码运行使用 `python -m desktop`。新构建只读核验并复制当前 managed 库，包含五格式与扫描 PDF OCR，使用独立 Python 3.12 环境。正式包绑定真实质量工件并完成副本 smoke 后，才激活[根双击入口](../启动本地版.bat)的候选指针。旧 runtime 原样保留为恢复对象。详见[本地使用说明](../本地使用说明.md)。

本轮恢复点 KB-V4_Recovery/20261015-PROD-151007 保存 369 文件，全部归档成员逐项 SHA256 核验，五项实际恢复检查通过。精确历史源码单独归档；历史诊断重放与当前 live guard 分别验证。新源码修订见[product source revision](../eval/v4_product_20261015_source_revision.json)。[README](../README.md)、[INDEX](INDEX.md)及[Master](V4_MASTER_REQUIREMENTS_AND_ROADMAP.md)顶部导航指向本页；Master 的 2026-09-16 正文原样保留。

当前包首次启动仅完成摘要来源兼容迁移；运行库与初始快照身份分别记录，原文档和向量值不变。本地恢复材料不属于源码仓库。公开候选的匿名副本与精确历史输入分开验证，缺少私有精确输入的检查明确报告不可重放，不能据此声称历史验证全部通过。
