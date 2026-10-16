# V4 本地候选：产品修复、质量验收与交付

完成记录续于 2026-10-16；冻结与测量身份沿用开始执行时的 20261015 编号。用户本轮要求执行 PROD-01、PROD-02、BASE-01、EVAL-01、REL-01。活跃目录为 V4 本地版；V3 与上传版继续保持各自原状态。

当前生产源码已冻结为 `bef1a9414eaa168702724b982e48338fbaa858661ac1cb1863af842ef7937b6d`。本轮五项执行任务均已完成；产品质量仍 FAIL，正式包为本地开发候选。

## PROD-01：答案缓存一致性

`desktop/web_server.py` 将状态指纹、范围缓存键、缓存读取、回答生成、序列化及缓存提交放入与库刷新相同的锁内。库变更回调返回前完成刷新与清空，使旧结果不能在清空后重新写回。显式空范围与默认范围的缓存键分离；在序列化、缓存命中窗口发生的取消不会提交完成结果。

12 项新测试通过，并覆盖真实临时 SQLite、LibraryService、HTTP 与真实问答引擎路径；模型依赖在该并发测试中使用可控替身。另有 44 项既有 Web、库生命周期和运行集成回归通过。修复前反事实运行得到预期失败，证明测试能捕获原竞态、范围碰撞和取消缺陷。

第一阶段身份为 `e8793f427266dc0a15c38df0e86915539d3db33df8a3223d889fe8efa0f9c16c`，见[源码基线](../eval/v4_prod01_cache_consistency_source_baseline_20261015.json)。本阶段没有新 Full144 成绩。

## PROD-02：统一材料编号格式

旧 WS-13 三次观察中的原始回答与最终回答均只有 `[材料1]`。本轮使用旧观察保留的 managed 库输入，独立预注册 A/B/C 三臂、共 12 次调用、零重试，不复用已消费的 WS-13 预算。

| 条件 | 唯一干预 | 目标题两次结果 |
|---|---|---|
| A | 原始消息 | 两次均仅输出材料标签 |
| B | 材料头由 `[材料1｜位置]` 改为 `[1] 位置` | 两次均输出 GSM/GMSK 实质结论与有效数字引用 |
| C | 仅追加必须给出实质结论的通用指令 | 两次均仅输出材料标签 |

完整响应显示 A/C 为正常 `stop`、生成 5 个 token，并非达到 800 token 限制或客户端丢弃正文。B 的可答控制保留 MS/BSS/NSS 事实。所有臂的材料不足控制均未编造具体年月日，但仍存在“材料未回答”类断言附引用的 unsupported 残留；不将该项写成引用安全全面通过。

生产仅修改 `core/engine_v2.py` 的材料头一行，保持材料正文、顺序、范围与检索算法、Golden、evaluator 和 verifier 不变。材料头缩短可能使临界字符预算多容纳尾块，因此不宣称所有问题发送的材料集合恒等；本例五块材料与冻结 B 干预逐字一致已有机械验证。离线测试证明新消息与奏效的 B 干预逐字一致。这支持当前具体输入与干预范围内的产品修复，不构成全局生成机制或所有引用问题的因果结论。

另行执行的三次真实 engine.answer 验证实际使用 legacy `textbooks.sqlite3`（1 文档、617 块），不是 managed 主库。原始计划、实际路径、响应和执行脚本均保留；该范围偏差单独披露。后续验证脚本已改为显式指定库、默认 managed，并新增防误用测试；未把旧结果改写成 managed 验证。当前 managed 主库效果由明确指定 `documents.sqlite3` 的统一评测验证。

第二阶段[源码基线](../eval/v4_prod02_numeric_material_header_source_baseline_20261015.json)的父节点为 PROD-01，最终候选生产身份为 `bef1a941…b6d`。

## BASE-01 与 EVAL-01

旧五项基线条目及旧科学工件原样保留，新生产阶段独立追加到 [lineage](../eval/v4_baseline_lineage.json)。历史诊断测试使用精确归档输入重放；当前 guard 仍对实际 `core/desktop/web` 重算，负向测试验证有效历史档案不能掩盖当前漂移。

冻结候选使用 managed 库 6 文档、637 块，原始 SHA256 为 `c6bc9b3eb63ae4e6d96caf859a2b0c5f2f1e5a5b6f438e81aa0bbc3cf4084c97`；embedding 为 bge-m3 / 1024，回答模型 qwen2.5:7b，SQLite，reranker 关闭。模型 digest、配置、Golden、evaluator、verifier 和主库身份在恢复目录的 `candidate-freeze.json` 保存。

Full144 已使用未修改的 canonical evaluator、新候选缓存和新输出路径完成，144 条新答案，耗时 2233.589 秒；同一答案集的指标双重重放一致，源码、主库、模型与冻结配置保持原身份。原始工件为 [新候选 Full144](../eval/v4_local_candidate_full144_20261015.json)。

| 指标 | 旧 V4.6.1 | 新候选 | 冻结门槛 | 结果 |
|---|---:|---:|---:|---|
| case_exact_fact_match_rate | 0.7292 | 0.7292（105/144） | ≥0.80 | FAIL |
| fact_recall | 0.8535 | 0.8471（266/314） | ≥0.90 | FAIL |
| citation_coverage | 0.4657 | 0.5895 | ≥0.80 | FAIL |
| false_refusal_rate | 0 | 0.0069（1/144） | ≤0.03 | PASS |
| high_confidence_unsupported_rate | 0.0132 | 0.0164 | ≤0.05 | PASS |
| invalid_citation_count | 0 | 0 | =0 | PASS |
| citation_scope_violation | 0 | 0 | =0 | PASS |

验收执行完成，产品质量仍 FAIL，不标 V4 Final。旧分数不复制为新成绩；源码变化与随机生成同时存在，逐案差异不能全部归因于单一格式变更。managed 库上的 cit-001 已实际给出 GSM/GMSK 结论、1/1 事实与 coverage 1.0；文档身份和定位类残留仍存在。41 个 Golden 非回答项与真实范围检索补充检查已完成；非回答项含元数据模板，不能把 41 项全部当作事实拒答分母。Phase E 与 F.2 离线检查均 PASS。

## REL-01

构建改为只读核验并复制当前 managed 主库，不重建或覆盖主库；旧 runtime 原样保留。Python 3.12 隔离构建环境满足 RapidOCR 1.4 的版本约束，实际五格式及扫描 PDF OCR 解析已通过。正式包已绑定候选源码、库、依赖确切版本和原始 canonical 质量工件，并在副本上验证 EXE。

根双击入口读取已激活的明确候选指针。正式包完整副本 smoke 和真实根启动器验收均通过；预检包独立保留，不作为交付。

## 恢复及历史边界

本轮恢复点为 `KB-V4_Recovery/20261015-PROD-151007`：369 个文件归档，全部成员逐项 SHA256 核验，主库、旧 EXE 等五项实际恢复检查通过。两个生产阶段均有独立源码身份；此前工程和 WS-13 来源登记不被覆盖。

原始旧文本输入另存 `tests/fixtures/product_20261015/pre_product_sources.zip`（262 项，SHA256 `45aefc20df47e0a2d8769184a4a8e13803540f7ac3848014806f72c3dd75ad5d`），仅用于显式历史输入重放。新源码修订登记为 [product source revision](../eval/v4_product_20261015_source_revision.json)，不把新测试解释为历史人工接受。

## 2026-10-16 完成结果

五项执行任务均已完成，产品质量保持三项 FAIL。统一本地工程验收 1707 项，0 failures、0 errors、26 skipped。正式 alpha.3 本地包、ZIP 和根启动器已验收并激活；这些私有运行材料不随源码公开。首次启动仅新增摘要来源兼容字段与 metadata；原文档、块及向量值不变。原始日志和完整恢复证据保存在本地工作区的 PROD 恢复点。后续 PUB 阶段见[源码发布说明](V4_PUBLICATION_20261016.md)；公开派生证据不能冒充私有原字节重放。
