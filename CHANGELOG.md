# Changelog

本项目的显著变更记录于此。格式参考 [Keep a Changelog](https://keepachangelog.com/)。

> 当前处于 **V4 Development Active**。最新条目对应一个 **Development Snapshot / Pre-release**，
> **尚未**达到 V4 Final。发布状态与基线以 [`docs/V4_RELEASE_SNAPSHOT.md`](docs/V4_RELEASE_SNAPSHOT.md)
> 和 [`docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md`](docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md) 为准。

---

## [v4.0.0-alpha.3] - 2026-10-16

Development Snapshot / GitHub Pre-release，**NOT V4 Final**。本条描述本次源码快照；实际 commit、tag、发布状态与远端 CI 分别见 [GitHub Releases](https://github.com/wt7439216/local-database-qa-system/releases) 和 [GitHub Actions](https://github.com/wt7439216/local-database-qa-system/actions)。

### Fixed

- 答案缓存与库刷新共用锁，阻止清空后旧结果回写；区分默认范围与显式空范围，并处理序列化及缓存命中窗口内的取消。新增 12 项回归及修复前反事实验证。
- 模型材料头由 `[材料1｜位置]` 统一为 `[1] 位置`。独立固定 12 次 A/B/C 调查支持该具体干预；没有修改检索算法、材料正文顺序、Golden、canonical evaluator、verifier 或质量门槛。不宣称全局生成机制或全部引用问题已经解决。
- 工程测试与离线 Phase E 使用隔离夹具，保留真实项目日志；历史源码重放与当前生产漂移校验分别验证。

### Added / Changed

- 追加 PROD-01、PROD-02 源码阶段及 `V4_20261015_LOCAL_CANDIDATE_BASELINE`；旧五项基线和历史科学结论保留。
- canonical production hash：`bef1a9414eaa168702724b982e48338fbaa858661ac1cb1863af842ef7937b6d`（`core/desktop/web`，canonical LF）。
- 独立运行新候选 canonical Full144、41 项非回答补充及 34 项范围隔离检查；未把旧成绩复制为新测量。
- Windows 构建工具只读核验并复制 managed 库，收集五格式与扫描 PDF OCR 依赖；独立 Python 3.12 构建、明确候选激活及 EXE 身份校验。开发环境已验证 alpha.3 EXE，私有数据库与运行包不随本次源码发布。
- 发布扫描与同步预演覆盖实际候选和评测工件；公开副本的路径处理和历史身份边界独立登记，保留本地原始证据。

### Validation / Quality

- 本地完整工程检查：2026-10-16，1707 tests、0 failures、0 errors、26 skipped。该历史结果与本次公开 fresh checkout / 远端 CI 分列，不能代替实际发布检查。
- 新候选 Full144：`case_exact 0.7292` / `fact_recall 0.8471` / `false_refusal 0.0069` / `citation_coverage 0.5895` / `high_conf 0.0164` / `invalid 0` / `scope 0`。
- **Product Quality DoD = NOT_YET_PASS**：事实全对率、事实召回率与引用覆盖率三项仍 FAIL。范围隔离专项 34/34 PASS，不替代语义拒答质量；定位事实遗漏、mt-006 误拒答、多文档实体遗漏与材料不足类引用继续保留为残留问题。
- 单次新旧答案差异同时包含源码变化与生成随机性，不将指标变化全部归因于材料头格式修复。

本次发布不包含完整私有教材、SQLite、日志、模型、EXE / ZIP 附件或本机候选激活指针；公开评测证据可包含问题、模型答案与少量教材短引文。干净源码克隆需要用户自行导入文档。

## 历史未发布诊断记录 — V4.7

以下为当时阶段的诊断与治理记录，保留原表述；当前产品身份、后续结论及质量结果以上方 alpha.3 条目和当前状态入口为准。

### Diagnosis / Governance

- **V4.7 — Document Identity Root-Cause Confirmation + Diagnosis Closure**（`READ-ONLY DIAGNOSIS`，**仅诊断 / 治理，无产品变更**）：
  对 `md-004` / `md-009` / `md-015` 机械确认 canonical document title 在
  `documents.title → ChunkRecord.document_title → chunk.location → serialized material header → application-level Ollama request`
  全链路保持可见 ⇒ **当前 V4.6.2 pipeline 的 Document Identity Loss = DISPROVEN**；
  `DOCUMENT_IDENTITY_ROOT_CAUSE = NOT_PROVEN`；**Document Identity remediation = BLOCKED（未授权）**。
- 当前 pipeline root cause family = `GENERATION`（shared mechanism `MATERIAL_INDEX_REPRESENTATION_BIAS`）；
  `GENERATION_MECHANISM_ISOLATION = NOT_ESTABLISHED`（**尚未**隔离出具有因果作用的主导机制）。
- Measurement 语义问题（canonical document title vs Golden semantic-role token）作为**独立轨道**记录
  （`MEASUREMENT_SEMANTIC_ISSUE = SUPPORTED`）；本轮**未**修改 Golden / evaluator / citation semantics。
- 历史结论：V4.6 的 `DOCUMENT_IDENTITY_FAILURE` 解释被**强挑战**（`STRONGLY_CHALLENGED`）；
  历史 pipeline 等价性因缺少 exact historical source anchor 而 `NOT_ESTABLISHED`；V4.6 历史 artifact 保持不可变。
- 本轮为 governance / documentation alignment：**production behavior unchanged**、
  **no new product baseline**（current pointer 仍为 `V4_6_2_HASH_PORTABILITY_BASELINE`）、
  未重算指标、未执行 V4.8、未做任何 publication。

## [v4.0.0-alpha.2] - 2026-09-12

> GitHub Pre-release（Development Snapshot，**NOT V4 Final**）。已发布并接受；
> **REMOTE_CI = PASS**（fresh LF GitHub Actions checkout；699 tests OK）。
> 日期取自 release commit / tag metadata（commit `4a75919`，`2026-09-12T01:14:55+08:00`）。

### Added

- **V4.6.2 — Hash Portability & CI Reproducibility Formalization**（governance / measurement）：
  versioned canonical content-hash contract `sha256-path-content-v2-canonical-lf`（仅对已识别 text 后缀
  规范化行尾；binary / 未知类型保持 raw bytes，绝不 decode / normalize）。
- 新 stage baseline：`V4_6_2_HASH_PORTABILITY_BASELINE`（parent `V4_6_1_EMBEDDING_IDENTITY_BASELINE`）。

### Fixed

- CRLF/LF hash portability：canonical text identity **仅规范化行尾**，使 Windows CRLF 工作树与
  Git-normalized LF checkout 得到一致身份；binary 保持 raw byte hashing；历史 raw hashes 作为
  provenance 保留；product behavior unchanged。由 fresh LF GitHub CI 验证通过（alpha.1 的 5 个
  byte-identity 失败全部消除）。
- Live production drift guard 改为校验 **canonical** production hash（跨 CRLF / LF 一致）。

### Notes

- `production_behavior_changed_in_stage = false`；`measurement_hash_contract_changed_in_stage = true`；
  产品指标未重算（`metrics_recomputed_in_v4_6_2 = false`，源自 `V4_6_1_EMBEDDING_IDENTITY_BASELINE`）。
- 本条目为 governance / hash-portability release correction，**不**代表产品质量提升。
- Supersedes `v4.0.0-alpha.1`（其 tag/commit 不变；release notes 已标注 superseded）。

## [v4.0.0-alpha.1] - 2026-09-12

> GitHub Pre-release（Development Snapshot，**NOT V4 Final**）。**已发布**。
> 基线 `V4_6_1_EMBEDDING_IDENTITY_BASELINE`。
> **CI postcheck FAILED**：CRLF/LF raw-byte hash portability defect（product behavior unaffected），
> 随后被 `v4.0.0-alpha.2` **superseded**；tag/commit **retained immutable**（`86c9479`）。
> 日期取自 tag/commit metadata（`2026-09-12T00:47:29+08:00`）。

### Added

- Canonical evaluation integrity：单一 canonical evaluator（`v4-baseline-v1`）+ 单一 Golden（185 例，其中 144 answer-eligible）。
- Failure Attribution framework：逐 case 机械归因机制（持续刷新）。
- Baseline lineage：不可变历史 stage baseline + 单一 current pointer（`eval/v4_baseline_lineage.json`）。
- Live production drift guard（`tests/test_live_production_hash_guard.py`）：live production hash 必须等于 current baseline 记录值。
- Embedding identity **fail-closed** 启动校验（`validate_embedding_identity`）：`配置模型 == 库中模型 == 向量维度`，不一致拒绝启动。
- 文档体系：`docs/INDEX.md`（文档导航）、`docs/V4_RELEASE_SNAPSHOT.md`（发布说明）、本 `CHANGELOG.md`。

### Changed

- 生产默认嵌入模型正式定为 **`bge-m3`（1024 维）**；`nomic-embed-text`（768 维）降为兼容/回滚模型。
- 文档与配置与当前状态对齐（README / 本地使用说明 / ARCHITECTURE / `.env.example`）。

### Fixed

- **Scope/OOS**：移除已证明的 in-scope false refusal（`loc-018` / `md-014`；`mt-006` 的 Scope 阻塞移除）——`false_refusal = 0`、纯离题 false accept `0/7`、scope leakage `0`。
- **Routing over-trigger**：`LOCATION_WORDS` 命中改为需位置意图，修正 `md-004` / `md-019` / `cit-001` / `cit-007` 误入 `locate` route。
- **Workspace portability**：`publication_scan.py` 移除旧硬编码工作区路径，改为由脚本位置动态推导。
- 修正 `docs/ARCHITECTURE.md` 中过期的引用核验版本（`f2-v2` → 当前 `f2-v4`）。

### Security / Safety

- Embedding identity 启动校验 fail-closed；no auto re-embed / no silent model switch / no automatic SQLite rebuild / no automatic Qdrant rebuild。
- Web 路径导入安全边界：`LIBRARY_IMPORT_ROOTS`（未配置时 Web 路径导入默认禁用）；QueryScope 越界引用属严重失败（scope leakage Gate = 0）。
- Citation hard gates 保持：`invalid_citation_count = 0`、`citation_scope_violation = 0`。

### Evaluation / Governance

- 当前 canonical Full-144（基线 `V4_6_1_EMBEDDING_IDENTITY_BASELINE`）：
  `case_exact 0.7292` / `fact_recall 0.8535` / `false_refusal 0.0000` / `citation_coverage 0.4657` / `high_conf 0.0132` / `invalid 0` / `scope 0`。
- `Product Quality DoD = NOT_YET_PASS`（仅 `false_refusal`、`high_conf` 与两项 hard gate 达标）。
- 质量接受合同（Target 档）保持冻结，不因 Dev Snapshot / Pre-release 下调。

### Known Limitations

- **Document Identity** — 下一产品阶段（`V4.7`）。
- **History**（多轮改写） / **Retrieval**（RRF ranking miss） / **Generation**（证据送达但答案省略/拒答） — PENDING。
- **Measurement Closure**（Golden / Evaluator） — PENDING。
- **Citation Coverage** — PENDING / DEFERRED。
- 其它 deferred 非阻断项：KB Summary / Multi-document Summary / 文档级元数据查询 / 生产 L2 verifier / Rich Citation UX / Performance SLA / Reranker 重新启用。

---

## [v3-final]

V3 冻结阶段。详见历史文档（`docs/V3_*`），包括分层评测基础设施、通用文档导入（五格式）、
知识库管理 + QueryScope、Conversation-aware Router、Hierarchical Summary、Deterministic Citation。
V3 结束时：Engineering / Evaluation Closure = PASS，质量合同 = FROZEN，`Product Quality DoD = NOT_YET_PASS`。
