# WS-13 cit-001 真实观察、归因与后续决策

日期：2026-10-15（Asia/Shanghai）。对应任务：DIAG-01、DIAG-02、DIAG-03、DIAG-04；状态入口见 [V4_CURRENT_STATE](V4_CURRENT_STATE.md)，整体执行与恢复记录见本轮执行报告（本地恢复点原件，未随源码公开）。

本轮完成了冻结 `cit-001` 的三次有效真实观察。三轮均已把包含 `GMSK` 的支持材料送达生成阶段，模型原始答案和应用最终答案却都只有 `[材料1]`。冻结分类器因此输出 **`NOT_ESTABLISHED_DUE_TO_CONFOUND`：生成遗漏构成混杂，独立引用缺陷未建立**。本轮没有实施 citation 产品修复，没有改变产品基线，也没有重测 Full-144。

## 执行对象与有效边界

| 项目 | 本轮固定内容 |
|---|---|
| case / query | `cit-001` / `GSM 使用 GMSK 调制，请指出出处。` |
| 预期事实 / 实体 | 事实 `GMSK`；实体 `GSM`、`GMSK` |
| 分支 | canonical 非流式 QA 分支；实际 `qa / DEFAULT_QA`，无 follow-up |
| 产品身份 | `V4_6_2_HASH_PORTABILITY_BASELINE`；canonical production hash `108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c` |
| 本地运行配置 | `qwen2.5:7b`、`bge-m3 / 1024`、SQLite managed 库；按当前绑定的实际请求配置运行 |
| 运行预算 | ordinal `1、2、3`，实际完成 3；额外运行 0，重试 0，control / counterfactual / Full-144 运行 0 |
| 设计 | G1 base + A001 + FC1；有效设计 digest `646d354284fe6a419e144ead01ffd879c7cd426a05346d523c350be178b2ea94` |
| 本轮规则 | [TPR2](../eval/v4_ws13_canonical_telemetry_permission_rule_002.json)；仅覆盖这一次固定的三轮批次 |
| 接受依据 | 本轮用户明确指令、精确输入绑定、实际保护检查及独立代理技术审查（本地恢复点原件，未随源码公开）；不声称历史人工接受 |

TPR2 raw SHA256 为 `5c014483c111837ac461d8301153f93676f2213ae50c49c4436d58a8f3e340d3`，semantic digest 为 `b016fe9499901108c2e0b0519a5e4ba00593b48572c601dcb056bf48176f8b8b`。旧 TPR1 的过期绑定原样保留；TPR2 没有改动 G1、计时契约、生产 pipeline、Golden、evaluator 或 verifier。

观察器保持 canonical 模型锁、操作顺序和计时区间，遥测调用仍计入其原本所在区间；稳定遥测字段取自同一次真实执行。时间戳和 elapsed 的动态验证使用绑定的执行窗口，没有声称完整重建动态 payload，也没有为缩短耗时去掉原有操作。

## 三轮实际事实

机器证据：[G4 观察汇总](../eval/v4_ws13_g4_observations_20261015.json)；外部原始 envelope：run 1（本地恢复点原件，未随源码公开）、run 2（本地恢复点原件，未随源码公开）、run 3（本地恢复点原件，未随源码公开）。

| 字段 | ordinal 1 | ordinal 2 | ordinal 3 |
|---|---|---|---|
| 观察时间（+08:00） | 11:42:22 | 11:44:06 | 11:45:00 |
| STATUS / live guards / equivalence | OBSERVED / true / YES | OBSERVED / true / YES | OBSERVED / true / YES |
| 路由 | qa / DEFAULT_QA | qa / DEFAULT_QA | qa / DEFAULT_QA |
| 送达上下文数 | 5 | 5 | 5 |
| 所需 GMSK 支持送达 | YES | YES | YES |
| raw_model_answer | `[材料1]` | `[材料1]` | `[材料1]` |
| final_application_answer | `[材料1]` | `[材料1]` | `[材料1]` |
| expected_fact_presence | 空 | 空 | 空 |
| evaluator fact_present / fact_total | 0 / 1 | 0 / 1 | 0 / 1 |
| canonical citation_count | 0 | 0 | 0 |
| citation_verified | false | false | false |
| invalid / scope violation | 0 / 0 | 0 / 0 | 0 / 0 |
| evaluator elapsed_ms | 54041 | 4692 | 4678 |
| model / embedding / retrieval 次数 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |

三轮实际送达的上下文顺序相同：`chk-130b681ce8010b26`、`chk-61a7acce435461ad`、`chk-eef9fec28eeb9787`、`chk-09d1b35eb2e202b9`、`chk-d276b1ca3e833ad2`。GMSK 精确支持出现在第 1 与第 3 个 sent evidence record；其原文、顺序及逐条内容哈希保存在 G4，不以“曾经检索到”替代“实际送入生成”。

从 raw / final 一致可以判断：所需事实在本轮模型原始输出里已经缺失，应用后处理没有把一个含 GMSK 的原始正确答案删成当前结果。该观察还不能说明模型为何只输出材料标签。首轮与后两轮计时不同；本报告不把该差异归因于冷启动、缓存或任何未单独验证的性能机制。

## G5：为什么不能据此建立 citation defect

[G5 机器结论](../eval/v4_ws13_g5_attribution_20261015.json)按冻结谓词消费三轮实际 envelope，没有重新调用模型、嵌入或检索。

| G5 字段 | 结果 | 含义 |
|---|---|---|
| CITATION_STATUS | NOT_ESTABLISHED | 当前独立引用缺陷未建立 |
| CITATION_CONFIDENCE | NOT_ESTABLISHED_DUE_TO_CONFOUND | 现象受到生成遗漏混杂，不能隔离为引用问题 |
| GENERATION_CONFOUND | YES | 支持已送达，但预期事实未出现在生成答案 |
| RETRIEVAL_CONFOUND | NO | 本 case 所需 GMSK 支持已实际送达生成阶段 |
| MEASUREMENT_CONFOUND | NO | 本轮没有触发冻结设计中的测量混杂条件 |
| CITATION_SPECIFIC_FAILURE | NO（逐轮） | 冻结引用缺陷谓词未成立 |
| RUN_VARIABILITY | NO | 三轮归因结果一致；不表示耗时或所有运行字段完全相同 |
| ATTRIBUTION_FRESHNESS / LATEST_PRODUCT_STATE_COMPATIBLE | FRESH / YES | 本轮证据确实来自当前固定产品状态 |
| ADDITIONAL_FRESH_EVIDENCE_REQUIRED | YES | 建立独立引用问题还需要补充有效证据 |

三个容易误读的字段必须保留原有语义：

1. `CLAIM_PRESENT=NO` 对应本 case 预期事实的缺失；canonical verifier 的 `factual_claim_count=1` 是另一个计量字段。二者不能直接互换，本轮没有据此判定 measurement defect。
2. `CITATION_EXPECTED=NO` 是冻结分类谓词在预期事实未生成时的输出，不等于“该问题无需给出处”。
3. `CITATION_TARGET_VALID=YES` 与 invalid / scope 为 0 不能证明引用正常：本轮 canonical 解析到的引用 token 和目标集合均为空。字面量 `[材料1]` 没有成为 canonical 引用输出。

本轮不建立“引用模块已正常”“当前引用缺陷为阴性”或某个全局 Generation 因果机制。`NOT_ESTABLISHED` 也不是 `CURRENT_NEGATIVE`。已有历史生成标签与本轮 Generation confound 均不得扩写成未经隔离验证的根因证明。

## G6：状态桥接与允许的下一步类别

[G6 机器结论](../eval/v4_ws13_g6_readiness_20261015.json)从[冻结父输入](../eval/ws13_frozen_parent_state_20261014.json)及 A001 / A005 规则确定性派生；没有重做 Priority Review 排名。

| G6 字段 | 结果 |
|---|---|
| READINESS_CLASS / NEXT_PERMISSIBLE_ACTION | R3 / FRESH_ATTRIBUTION |
| CURRENT_UNRESOLVED_ISSUE_ESTABLISHED | NO |
| SINGLE_PRIMARY_SUBSYSTEM | NO |
| CURRENT_ATTRIBUTION_STATUS | NOT_CURRENTLY_ESTABLISHED |
| UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_FRESH_ATTRIBUTION | NO |
| UNRESOLVED_UPSTREAM_DEPENDENCY_FOR_SEPARATE_EXECUTION | YES |
| PROJECTED_A003.PROJECTION_BRANCH | PRESERVE_INHERITED_HISTORICAL_OR_STALE_RECORD |
| BLOCKED_ACTIONS | SEPARATE_EXECUTION |
| SEPARATE_EXECUTION_AUTHORIZED / PRODUCT_REMEDIATION_AUTHORIZED | NO / NO |

G5 的新观察 freshness 与 A003 的历史记录保留属于不同层次。当前 citation 缺陷尚未建立，A001 规定保留 inherited historical 记录；这不抹掉本轮 fresh evidence，也不把旧历史状态自动升级为当前根因。WS-11 相关上游依赖继续限制 separate execution，不能仅因已执行三轮就判为 R0 或允许独立 citation 修复。

## 产品修复条件与最小补充调查

`PROD-02` 仍是条件任务。本轮没有建立 citation-specific defect，因此不具备直接实施引用补全、改 verifier 或改 Golden 来消除本例失败的证据条件。本轮没有任何此类产品变更。

最小下一项调查应先使用已经保存的实际输入和输出，核对生成内容缺失与材料标签格式的关系：

1. 对照真实 model-visible messages、问题、材料内容及标签，检查需要生成完整事实答案的要求与实际标签格式；先建立可定位的代码 / 输入事实。
2. 对照 raw → normalization → renumber → verifier → final 的既有记录，维持“原始输出已经缺事实”与“标签是否可被解析”的独立问题边界。
3. 在形成可检验的单一假设后，再单独固定补充实验的目标、控制、预算和输入身份。不能把三次相同输出本身当作标签格式已经导致生成遗漏的因果证明。

`PROD-01` 答案缓存并发一致性有独立的内存交错复现，属于剩余 P0 工程工作，可作为后续优先项。应在临时真实库与服务器路径验证，再登记生产身份变化；它不能充当本轮只输出材料标签的已证明原因。

本轮 TPR2 的 ordinal 1～3 预算已经全部消费，初始遥测状态也已推进。该规则和 G6 `FRESH_ATTRIBUTION` 字段都不授权重跑本批次、补第 4 轮或启动未定义的新实验。

## 执行完整性与验证入口

逐轮 `GOVERNANCE_DELTA_VALIDATION=PASS`，每轮恰有一次 canonical telemetry 调用和一条成功 JSONL 追加。QA 遥测从 1238 行推进到 1241 行，native file identity 不变，旧文件字节是新文件精确前缀。三次追加分别为 915、913、912 字节，总计 2740 字节；目标大小从 1064168 增至 1066908 字节，保持完整 CRLF 记录边界。

运行间 immutable manifest 仅精确排除 QA 遥测与 TPR2 两个路径；TPR2 自身仍逐次单独校验精确 raw SHA 和 semantic digest。每轮前后 manifest 均为 19690 项、digest `457dee2b33f699121de1e22fa1734cfcdcfefc7545a15b79448e849cbe7cce49`。生产代码、DB、缓存和其他日志没有被本批次改写；G4/G5/G6 汇总工件在固定三轮结束后才写入活跃区。

本轮全量工程验收：1662 项，0 failures、0 errors、26 skipped，耗时 850.570 秒。Ruff、Python 源码编译及 3 个前端 JavaScript 语法检查通过。

真实观察、逐轮物理遥测链与 G5/G6 全字段已通过独立重算审计（本地恢复点原件，未随源码公开），审计没有新增模型、嵌入或检索调用。

具体测试、初次 G2 三项失败的修复记录、恢复点和保护核验见执行报告（本地恢复点原件，未随源码公开）。本轮诊断不能替代 Full-144 重测；最近仍使用 V4.6.1 的旧指标，case exact 0.7292、fact recall 0.8535、citation coverage 0.4657 的最终门槛均未通过。
