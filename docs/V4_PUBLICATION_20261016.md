# V4 alpha.3 源码发布记录

本次 PUB-01 / PUB-02 发布目标为 `v4.0.0-alpha.3` **Development Snapshot / Pre-release**，对应生产基线 `V4_20261015_LOCAL_CANDIDATE_BASELINE`。生产源码 canonical SHA256 为 `bef1a9414eaa168702724b982e48338fbaa858661ac1cb1863af842ef7937b6d`。

Full144 的事实完整率 `0.7292`、事实召回率 `0.8471`、引用覆盖率 `0.5895` 均 FAIL。源码发布与工程检查不改变该质量状态，也不产生新的模型评测成绩。[原始质量工件](../eval/v4_local_candidate_full144_20261015.json)和[产品执行记录](V4_PROD_EVAL_REL_20261015.md)给出测量身份与限制。

## 候选与扫描

活跃开发继续在 V4 本地版。公开候选在独立目录生成，扫描器与同步工具使用同一份候选清单，包含 `eval`、历史 ZIP 成员以及必要的测试夹具。数据、数据库、模型、运行包、缓存和本地激活指针不在源码同步范围。上传版独有 `.github` 等资产保留其所有权。

同步默认只生成 dry-run 清单，逐项记录新增、修改、删除、源与目标 SHA256。实际应用必须同时提供该清单、候选扫描记录和逐项审阅理由；源、目标或保留资产漂移均拒绝继续。扫描命中分为认证实现、虚构安全测试输入、历史环境 provenance 与需匿名化的真实本机账号；测试文件不会获得自动豁免。

## 历史证据公开策略

本地 PUB 恢复点保存发布前 V4 源码、所有原始历史 ZIP、上传版工作树和完整 Git bundle，并逐成员核验。既有 engineering / WS-13 / product 登记及科学工件原始身份继续保留。

公开候选对真实本机账号路径制作派生副本。公开根目录的 `PUBLICATION_EVIDENCE.json` 记录原始 SHA256、实际公开 SHA256、ZIP 成员映射与转换类型，不保存被移除的账号路径。原始 ZIP 不被悄悄替换为“原字节”；未修改成员仍按原 SHA256 验证。需要已匿名化成员精确原始字节的历史重放明确报告 `PrivateHistoricalInputUnavailable`。这类不可重放项不计作执行通过；纯算法和当前生产行为测试继续运行。

非个人的冻结环境路径可作为历史 provenance 保留并按精确文件身份审阅。它们不是当前安装路径。当前 harness 改用相对外部输入和环境变量覆盖，公开 quickstart 无需本机账号或教材目录。

历史继承关系检查需要的 V3 / 同步前上传版各四份源码另存为独立夹具，逐成员记录真实 SHA 与来源版本；不存在旧兄弟目录或兄弟目录已更新时，显式读取该历史夹具进行原有 AST 比较。它不把新上传版当成旧继承输入。缺少私有库时，纯 SQL / observer 机制测试使用明确标识的临时 SQLite 及其实际哈希；冻结私有库身份的检查另行报告缺失，不把临时数据视为测量库或新的科学证据。

新发布修订独立登记于 `eval/v4_publication_20261016_source_revision.json`，其父为不可变的 product source revision。公开派生候选和本地原始证据分别绑定各自真实字节；当前生产 guard 始终读取实际 `core / desktop / web`。

冻结的 `eval/*.json`、夹具 JSON 和公开转换 manifest 使用 Git `-text` 保留真实原字节，避免 checkout 的换行转换破坏 raw SHA 承诺。Python、JavaScript、Markdown 等源码继续使用 LF，PowerShell 与 BAT 按既有 CRLF 规则；该规则不把换行变化伪装为原始哈希相同。

## 验证与交付边界

此前本地完整验收为 1707 项、0 failures、0 errors、26 skipped，属于 PROD / EVAL 阶段。本次公开 checkout 的检查必须重新执行并单独登记实际总数、失败与跳过原因。远端检查可在 [GitHub Actions](https://github.com/wt7439216/local-database-qa-system/actions) 按提交或 tag 核验，最终提交与发布说明以 [alpha.3 Release](https://github.com/wt7439216/local-database-qa-system/releases/tag/v4.0.0-alpha.3) 为准。

源码发布不附带私有知识库或已激活 EXE。Python 3.13 CI 覆盖源码工程检查；本地 Windows OCR 构建使用 Python 3.12，二者验证范围不同。下载源码后应导入自己的文档；本地 6 文档 / 637 块测量库及其模型身份仅用于解释既有质量证据。
