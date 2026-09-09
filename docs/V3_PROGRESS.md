# V3 Progress

> 阶段执行记录（TRANSITION）。基线数值来自 Phase 0 只读审计与 Phase A 实测。

## Baseline

- branch / commit：本地版v3 目录（开发工作区，无 Git）；GitHub `d0ad1bef…` 为最近一次发布基线
- date：2026-09-06
- tests：52/52 PASS（v2_library 35 / web_server 8 / text_rules 5 / rebuild_all 4）
- golden：false_refusal 0.0 / false_accept 0.0 / top1 0.65 / top3 1.0 / compare 1.0（PASS）
- embedding：bge-m3 / 1024 维（gates 0.48/0.55 为冻结兼容基线，未校准）
- schema：SQLite v4，617 chunks（606 body + 11 front_matter），1 文档 352 页 7 章
- performance：Dense O(N) p50 ≈ 10.4 ms @617；query embedding ≈ 2.2 s（bge-m3）

## Phase 0

- Status: PASS
- Evidence: 审计报告（HEAD 核验、Gap Matrix、测试/Retrieval/性能基线、Phase A 方案适配性检查、QD-01 分析）
- Risks: top1 余量仅 0.05；bge-m3 未入注册表；重建默认模型漂移
- Decision: 授权进入 Phase A（QD-01 = Option A 标准库 HTTP Adapter）

## Phase A — v3.0

- Status: PASS（证据见下）
- Authorized scope: Vector Backend 解耦 + Qdrant Dense Index；backend behavior equivalence
- Branch / workspace: `Local Database Q&A System本地版v3`
- Rollback snapshot: `..\_phase_backups\kb-v3-phase-a-pre\`（41 个源文件 + SHA256 清单）

### Changes

- 新增 `core/vector_store.py`：VectorStore Protocol、DTO（VectorRecord/VectorHit/VectorScope/VectorHealth/IndexManifest/IndexEntry/IndexVerification）、错误合同、`chunk_id`/`content_hash`/`vector_input_hash` 三哈希助手、确定性 point ID（uuid5 固定命名空间）、后端工厂
- 新增 `core/sqlite_vector_store.py`：默认后端，O(N) 暴力扫描（行为等价迁移），只读运行时 + 可写测试模式，verify 与 manifest 构建
- 新增 `core/qdrant_store.py`：stdlib urllib REST 适配器（显式 no-proxy），Query API 主读路径，transport 可 mock，超时/HTTP/JSON/status 四层校验
- 新增 `core/hybrid_retriever.py`：RRF + 质量/标题/去重/小节限额/front_matter/离题门限（常量自 v2 冻结），分阶段计时
- 修改 `core/library_store.py`：稠密加载与融合逻辑迁出，`retrieve()` 委托，`normalize_vector` 移至 vector_store（保持导出），新增 `EMBEDDING_PROFILES`（bge-m3 标记为 compatibility baseline，未校准）
- 修改 `core/config.py`：`VECTOR_BACKEND`（默认 sqlite）/`QDRANT_URL`/`QDRANT_COLLECTION`/`QDRANT_TIMEOUT_SECONDS`
- 修改 `core/engine_v2.py`：telemetry 新增 `vector_backend`/`embedding_ms`/`lexical_ms`/`dense_ms`/`fusion_ms`（向后兼容）
- 修改 `core/ollama_http.py`：本地 HTTP 显式直连（绕过系统代理）
- 新增 `scripts/rebuild_vector_index.py`（复用 SQLite 向量、幂等、终验）、`scripts/verify_vector_index.py`（只检测不修复）、`scripts/benchmark_retrieval.py`（dense 基准 + compare 双后端对比）
- 新增 `tests/test_vector_store_contract.py`、`tests/test_qdrant_store.py`、`tests/test_hybrid_retriever.py`、`tests/test_qdrant_integration.py`、`tests/fake_qdrant.py`
- 删除：无

### Tests

- 全套测试 PASS（原 52 未删改 + Phase A 新增，逐模块真实计数见 Closure Audit），真实集成在 Qdrant 不可达时自动 skip
- regression_test.py PASS；Golden Set 与冻结基线逐项一致（含"香农公式"敏感个案行为不变）

### Regression

- Golden Set：false_refusal 0.0 / false_accept 0.0 / top1 0.65 / top3 1.0 / compare 1.0 —— 与冻结基线相同
- 双后端对比（29 条冻结查询）：dense top1 match 29/29、top3/top5 overlap 1.000、top1 分差 <1e-6、章节一致 29/29、scope 一致 29/29

### Performance（1024 维，p50/p95，synthetic 数据，真实库未触碰）

| chunks | SQLite O(N) | Qdrant ANN |
|---|---|---|
| 617 | 8.1 / 8.9 ms | 4.7 / 24.0 ms |
| 1 000 | 13.4 / 14.8 ms | 4.4 / 29.6 ms |
| 10 000 | 138.5 / 150.3 ms | 5.0 / 27.0 ms |

- Hybrid @617（缓存向量）：SQLite p50 19.8 ms / Qdrant p50 27.9 ms（小规模 Qdrant 有 HTTP 固定开销，大规模占优）
- 结论：在本次 1k–10k benchmark 中，Qdrant 未表现出应用侧 Python O(N) 暴力扫描的线性延迟增长；10k chunks 下 Dense p50 从约 138.5 ms 降至约 5.0 ms。

### Integration evidence

- Qdrant v1.19.1（Docker，named volume `kb_v3_phase_a_qdrant_storage`，仅绑定 127.0.0.1:6333）
- rebuild 复用 SQLite 现有 617 条 embedding（零重复嵌入）→ 617 points → verify PASS
- filter：document_id / knowledge_base_id 真实索引验证通过
- delete：专用测试 collection 验证按 point / 按文档过滤删除；破坏性一致性测试（missing/orphan/model/dimension/content/vector-input）全部在临时 collection 中验证后清理
- outage：停机时 health 明确报错、retrieve 显式异常、SQLite 完整无损、默认 sqlite 后端不受影响、无静默回退

### Known issues / limitations

- knowledge_base_id 使用过渡值 `"default"`；正式 KB 模型在 Phase D
- SQLite 后端保持 v2 全量完整性语义：删除任一向量即整体禁用稠密路径（冻结行为）
- 50k 合成基准未运行（10k 已满足验收判据，50k 属可选扩展）
- bge-m3 gates 为冻结兼容基线；threshold calibration 后续独立进行
- compare 路由的 telemetry 分阶段计时记录的是最后一次子检索

### Rollback

- 源码：恢复 `..\_phase_backups\kb-v3-phase-a-pre\` 快照（SHA256 清单校验）
- 运行时：`VECTOR_BACKEND=sqlite`（默认即 sqlite），Qdrant 可停止/删除，SQLite 问答功能不受影响

### Closure Audit（2026-09-07）

- **测试计数修正**：机器 discovery 实测，Phase A 修复前基线 107 = 原 52 + 新增 55（test_vector_store_contract 27、test_qdrant_store 14、test_hybrid_retriever 5、test_qdrant_integration 9）。此前报告中"contract 30 / mock+transport 16"的分类统计有误；总数 107 正确。Closure 修复后最终 **115 = 原 52 + 63**（另增 test_proxy_bypass 7、test_telemetry_isolation 1、原 52 中 test_v2_library 夹具重定向 +2 行夹具代码）。
- **文件变更修正**：机器递归 diff（SHA256）实测 Added 13 / Modified 5 / Deleted 0。此前报告误将 core/ollama_http.py 列为已修改；本轮 closure audit 按授权落实 loopback 直连策略后，该文件成为真实修改。
- **telemetry 测试隔离**：test_v2_library 夹具重定向 `config.LOG_DIR` 至 TemporaryDirectory（生产语义不变）；新增 `tests/test_telemetry_isolation.py` 证明全套件运行前后项目真实 `data/logs/qa_log.jsonl` 字节不变。
- **proxy 策略统一**：ollama_http 与 qdrant_store 对 127.0.0.1 / localhost / ::1 强制直连（不受 HTTP_PROXY/HTTPS_PROXY 影响）；非 loopback 地址保留 urllib 默认（环境/系统）代理语义；新增 `tests/test_proxy_bypass.py`。

### Gate decision

Phase A = PASS。下一阶段（Phase B / v3.1 Reranker）未开始，等待用户授权。

## Phase B — v3.1

- Status: **FAIL（仅一项验收未达标：排名增益 < 0.02 参考值）**；工程实现与全部其余验收项通过
- Authorized scope: Local Reranker Adapter + Cross-Encoder Reranking（仅此一项变量）
- Branch / workspace: `Local Database Q&A System本地版v3`
- Rollback snapshot: `..\_phase_backups\kb-v3-phase-b-pre\`（53 文件 + SHA256 清单）

### Changes

- 新增 `core/reranker.py`：`Reranker` Protocol、`HTTPReranker`（loopback HTTP，transport 可注入）、`IdentityReranker`、类型化错误（Unavailable/HTTP/Protocol/ModelMismatch）
- 新增 `reranker_service/`：独立可选环境（own venv + requirements：torch>=2.6、transformers>=4.51），stdlib HTTP sidecar（/health /model /rerank，ID 一一对应协议，loopback-only）
- 修改 `core/hybrid_retriever.py`：candidate pool（RERANK_CANDIDATE_K）→ 可选重排 → final top_k；`build_rerank_passage` 确定性候选文本；Scope 门限仍全部使用重排前信号；fallback 显式配置
- 修改 `core/library_store.py`：`SearchHit.rerank_score` 新字段（fused `score` 含义不变）；构造时按配置创建 reranker
- 修改 `core/engine_v2.py`：telemetry 新增 `reranker_enabled / reranker_candidate_count / reranker_ms / reranker_truncated_candidates`
- 修改 `core/config.py` / `.env.example`：`RERANKER_ENABLED=false`（默认）/ `RERANKER_URL` / `RERANKER_MODEL` / `RERANK_CANDIDATE_K=16` / `RERANK_TIMEOUT_SECONDS` / `RERANKER_FALLBACK=disabled`
- 新增 `scripts/eval_reranker.py` + `scripts/reranker_eval_set.json`（53 条人工标注查询）；`tests/test_reranker.py`（29 项契约）+ `tests/test_reranker_integration.py`（4 项真实 sidecar 集成，不可达时 skip）
- 主 requirements.txt 未变（运行时仍零第三方依赖）；模型缓存位于用户 HF cache（仓库外）

### Tests

- 全套 148/148 PASS（原 115 未删改 + reranker 契约 29 + 真实 sidecar 集成 4）
- regression PASS；Golden Set 与冻结基线逐项一致

### Scope freeze（实测）

- 8 条 hard negative + 全部 in-scope 查询：Reranker ON/OFF 的 `out_of_scope`/`confidence`/`top_dense_score` 完全一致（含真实模型与反转排序的激进 fake）
- 已知：'NBA比赛比分是多少？' 在 RRF-only 即被冻结门限放行（conf=medium，top_dense=0.4186，两字/缩写集中命中规则）——Phase A 既有特性，非本阶段回归

### Reranker Eval（53 条查询，graded relevance 2/1/0，top_k=5，sqlite 与 qdrant 后端结果一致）

| system | MRR | nDCG@5 | Recall@5 | Top1 | Top3 | Compare | OOS拒绝 |
|---|---|---|---|---|---|---|---|
| RRF-only | 0.956 | 0.651 | 1.000 | 0.933 | 0.978 | 0.750 | 7/8 |
| RRF+Reranker(K=8) | 0.961 | 0.654 | 1.000 | 0.933 | 0.978 | 0.750 | 7/8 |
| RRF+Reranker(K=12) | 0.961 | 0.655 | 1.000 | 0.933 | 0.978 | 0.750 | 7/8 |
| RRF+Reranker(K=16) | 0.961 | 0.660 | 1.000 | 0.933 | 0.978 | 0.750 | 7/8 |
| RRF+Reranker(K=20) | 0.950 | 0.664 | 1.000 | 0.911 | 0.978 | 0.750 | 7/8 |

- 逐例分析：4/45 top1 变化 = 2 修复（**香农公式 top1 第5章→第3章，已知敏感个案被自然排序修复**；cell 小区 6→1）+ 2 新回退（频率复用 1→6；Turbo码 3→1）
- **增益结论：最佳 +0.008（K=16 nDCG@5）< 0.02 参考值；按合同不强行判定 PASS**。基线在单教材 + 强 RRF 下已近饱和（Recall@5=1.0），评测集区分度不足。

### Performance（bge-reranker-v2-m3，max_length 1024，truncated=0）

| device | K=8 p50 | K=16 p50 | K=20 p50 |
|---|---|---|---|
| CPU（float32） | 6 852 ms | 13 948 ms | 17 721 ms |
| CUDA（RTX 4060 fp16） | 162 ms | 285 ms | 366 ms |

- CUDA 模型加载：sidecar 启动后 ~15-20s；VRAM 峰值（qwen2.5:7b + bge-m3 + reranker fp16 + 系统）7510/8188 MiB，无 OOM

### Coexistence（实测）

- Ollama（qwen2.5:7b 生成 + bge-m3 嵌入）+ Qdrant + CUDA reranker 同时运行，完整问答 3/3 成功（citations 正常）；LLM 总时长 8.1–37.4s；rerank 负载下 410ms–3.1s（与 LLM 生成争抢 GPU）

### Failure tests

- sidecar 停机：health ok=False 明确报错；`RERANKER_FALLBACK=disabled`（默认）显式抛 `RerankerUnavailableError`；`=rrf` 回退 RRF 排序（rerank_score=None）并在 telemetry 记录 reranker_error
- 契约层：duplicate/missing/unknown id、NaN/inf、超时、malformed JSON、模型不匹配全部检出

### Rollback

- `RERANKER_ENABLED=false`（默认）：逐字段断言 answer/route/mode/confidence/oos/citations 与 Phase A 输出完全一致；sidecar 可停止/卸载/删除，不影响 SQLite/Qdrant/Ollama

### Known issues

- 排名增益未达 0.02 参考值（评测集区分度不足/基线饱和）；reranker 保持默认关闭
- K=20 出现 Top1/MRR 轻微回退 → 推荐 K=16（即默认值）
- CPU rerank 延迟（K=16 约 14s）不支持交互式使用，建议 CUDA 或保持关闭
- 旧 telemetry 日志 96 行测试生成记录按合同保留，未清理

### Gate decision（初评）

Phase B 严格按原验收标准初评为 FAIL：唯一未达标项为"至少一个主要排名指标有明确正增益（≥0.02 参考值）"，其余 23 项 PASS 条件全部满足。按合同不强行判 PASS，提交用户治理决策。

### 项目治理决策（2026-09-07，用户正式决定）

**Phase B Overall = ACCEPTED_WITH_EFFICACY_DEFERRED**（方案 ②：保留 Reranker 作为可选能力，默认关闭）。

```text
Phase B implementation: COMPLETE
Engineering validation: PASS
Ranking efficacy: DEFERRED / NOT_PROVEN
Default enabled: NO（RERANKER_ENABLED=false 冻结为默认配置）
Recommended experimental K: 16（experimental / optional）
Re-evaluation trigger: multi-document / larger corpus
```

有效性结论（raw 数值，冻结记录）：

```text
RRF-only:      MRR 0.9563   nDCG@5 0.6512   Recall@5 1.0000   Top1 0.9333   Top3 0.9778   Compare 0.7500
Reranker K=16: MRR 0.9611   nDCG@5 0.6596   Recall@5 1.0000   Top1 0.9333   Top3 0.9778   Compare 0.7500
               （MRR +0.0048，nDCG@5 +0.0084；Top1/Top3/Compare 无净变化）
Reranker K=20: nDCG@5 0.6639（+0.0127，为最大单项 nDCG 数值），但 MRR -0.0063、Top1 -0.0222 → 不作为推荐配置
```

解释：MRR 小幅提升；nDCG@5 小幅提升；Recall@5 已饱和无提升空间；Top1 聚合无净提升；部分 case 修复（含香农公式 top1 第5章→第3章）；部分 case 新回退。**不得表述为"显著提升"**。未达到 ≥0.02 有意义增益参考值，属 DEFERRED 而非 PASS。

Phase B 文件变更勘误（机器 diff，Phase B pre snapshot vs workspace）：**Added 8 / Modified 8 / Deleted 0**。`docs/V3_PROGRESS.md` 在 Phase B pre snapshot 中已存在（Phase A 创建），归入 **Modified**；此前报告"新增 9"含该文件属分类错误。另有 5 个顶层文件（.gitattributes、build_windows.ps1、windows_desktop.spec、启动本地版.bat、本地使用说明.md）因快照遗漏出现在假 Added 中——经与 Phase A pre snapshot 哈希比对确认在 Phase B 期间**未被修改**，不计入变更。快照根部的 SHA256SUMS-pre.txt 与重复的 V3_PROGRESS.md 为备份伪影，已排除。

### Backlog（登记，不在当前阶段执行）

1. **Reranker Re-evaluation Gate**：满足以下至少一项时重评（保持其他变量冻结）：多文档导入完成；chunks 明显超过 617；出现多文档相似章节/同名术语；multi-document QA eval set 建立；hard-negative 候选空间真实扩大。届时重比 RRF-only vs RRF+Reranker（K=8/12/16/20）；若出现稳定明确增益再评估 `RERANKER_ENABLED=true` 作为默认值。
2. **Scope Gate hard-negative false accept**："NBA比赛比分是多少？"被当前冻结门限放行（缩写集中命中，conf=medium，top_dense=0.4186）。属 Phase A 既有特性；后续单独做 Scope Calibration，本轮不动 strong/accept gate、缩写规则与集中命中规则。
3. **telemetry housekeeping**：99 行已识别的测试/探针日志（96 行测试夹具 + 3 行 Phase B 共存探针，均可按时间戳与罐装答案特征无歧义区分）待单独清理，不与 Phase C 功能开发混合。

## Phase C — v3.2

- Status: **PASS**
- Authorized scope: Parser Adapters + Normalized Document Model + Generic Sections + Import Pipeline + Incremental Import
- Branch / workspace: `Local Database Q&A System本地版v3`
- Rollback snapshot: `..\_phase_backups\kb-v3-phase-c-pre\`（65 文件 + SHA256 清单）

### Changes

- 新增 `core/document_model.py`：NormalizedDocument / NormalizedSection / NormalizedBlock / SourceLocation / DocumentMetadata；document_id（来源路径 + 固定命名空间的确定性身份，内容编辑不改变）/ source_hash（原始字节）/ content_hash（规范化内容）三者分离
- 新增 `core/parsers/`：base（DocumentParser Protocol + 类型化错误合同：UnsupportedFormat/ParseFailure/EncodingFailure/EncryptedDocument/EmptyDocument/CorruptDocument + 大小/编码守卫）、registry（集中分派，禁止 CLI 按 suffix 分支）、text_parser（UTF-8/BOM/GB18030 严格解码，保守标题启发式可关闭）、markdown_parser（标题/围栏代码含语言/列表/表格/引用/front matter，纯标准库）、docx_parser（Word 标题样式/表格 row-cell/正文顺序/不支持内容计数/OLE 加密检测）、pptx_parser（slide 顺序/标题/文本框/表格/备注）、pdf_parser（包装既有 PyMuPDF+OCR 管线，page 级 SourceLocation）
- 新增 `core/chunking.py`：通用 Section Builder（层级树，容忍级别跳跃）+ Chunk Builder（确定性 chunk_id = sha256(document_id|section_path|block_ordinal|piece_ordinal|content)，非页依赖；统一 build_vector_input(title, section_path, text)，兼容旧教材约定）
- 新增 `core/importer.py`：DocumentImporter——增量（source_hash 未变 → UNCHANGED；变化 → UPDATE 并按 chunk_id 复用未变嵌入）、dry-run 不落库、SQLite 单事务原子写入、嵌入失败回滚（FAILED）、Qdrant 失败不破坏 SQLite（FAILED_INDEX）、嵌入模型一致性守卫、导入遥测写 data/logs/import_log.jsonl（与 QA telemetry 分离，测试重定向 temp）
- 新增 `scripts/import_document.py`（CLI：--file/--dry-run/--backend/--force/--library）与 `scripts/eval_general_ingestion.py` + `scripts/general_ingestion_eval.json`（25 条）
- 新增 fixtures：tests/fixtures/documents/（md/txt/docx/pptx/pdf 五格式同语义内容 + make_fixtures.py 生成器）与 tests/test_document_model.py、test_parsers.py、test_importer.py、test_general_ingestion.py（真实 E2E 在服务不可达时自动 skip）
- 修改 `core/sqlite_vector_store.py`：build_index_manifest 对导入文档使用统一 vector_input 约定（legacy 教材约定保持字节不变）
- 未修改主 requirements.txt（运行时零依赖不变）；requirements-ingest.txt 扩展 python-docx/python-pptx（仅建库环境，运行时零依赖不变）

### Schema Decision

**remained v4**。Impact Analysis：v4 的 chunks（chapter/section 字符串列）+ chapters 表可完整承载通用文档（section 路径字符串 + level-1 节映射为 chapters 行 + 文档级摘要行），无运行时消费者需要 sections 全量表；迁移 v5 会迫使既有 617-chunk 教材库迁移且无对应收益。全量 sections 表推迟到出现真实需求的阶段（届时附 v5 DDL/迁移/回滚设计）。通用文档默认导入独立库 data/library/documents.sqlite3，教材库零改动。

### Tests / Eval

- 全套 195/195 PASS（原 148 未删改 + Phase C 47：document_model 10、parsers 16（含注册表/编码/加密/损坏）、importer 9、general ingestion 12（含真实 E2E 4，服务不可达自动 skip））
- 教材 Golden Set 与冻结基线逐项一致（PASS）；regression PASS；教材库 verify PASS（617/617）
- General Ingestion Eval：25/25 PASS（5 格式 × 5 查询，document hit / section hit / 无误判离题 / 格式元数据；qdrant 后端）

### Performance（真实 bge-m3 嵌入 + Qdrant 索引，单文档导入）

| 格式 | chunks | parse | embed | index | total |
|---|---|---|---|---|---|
| markdown | 3 | 0.7ms | 2616ms | 66ms | 2684ms |
| txt | 3 | 0.9ms | 2475ms | 65ms | 2542ms |
| docx | 6 | 50.5ms | 2617ms | 69ms | 2737ms |
| pptx | 2 | 71.3ms | 2406ms | 62ms | 2540ms |
| pdf(OCR) | 6 | 4383ms | 2464ms | 120ms | 6967ms |

- 嵌入占主导（Ollama 单次批量往返 ~2.5s）；PDF 解析含 OCR 4.4s；无异常量级

### Known issues

- PDF OCR 标题检测局限：第 2/3 节标题未独立成节（OCR 行合并），section 路径粒度受限
- PPTX 小节体（<20 字符）按最小长度规则跳过；通用 chunk 最小长度沿用教材约定
- sections 全量表未持久化（v4 内以路径字符串 + chapters 兼容映射承载）
- 5 份 fixture 内容语义相同，混合检索 top5 会因冻结近重复过滤折叠跨文档重复（跨格式可达性在 FTS/稠密候选层断言）

### Rollback

- 源码：恢复 `..\_phase_backups\kb-v3-phase-c-pre\` 快照（SHA256 校验 + restore 演练通过）
- 运行时：新管线完全增量，未改变教材库/检索默认行为；RERANKER_ENABLED 仍默认 false

### Phase C Closure Audit（2026-09-07）

工程主体 PASS 之后、正式关闭之前，按 Closure 目标逐项验证并补齐了以下缺口。

#### Closure 1 — UPDATE stale 清理（真实 bug，已修复）

- **确认的真实一致性 bug**：`DocumentImporter._index_qdrant` 此前只 upsert 新 points，从不删除该文档在本轮更新后不再存在的旧 points（旧 chunk D/E 残留在 Qdrant，SQLite 却已正确收敛）。
- **修复**：
  - `core/qdrant_store.py`：`scroll_payloads(batch, query_filter=None)` 扩展支持 Qdrant filter（`POST /points/scroll` 带 `filter`），可按 `document_id` 枚举现有 payload；
  - `core/importer.py`：`_index_qdrant` 支持 injectable `qdrant_store`；upsert 后按 `stale = 现有 document_id points − 新 chunk 集` 用确定性 point ID `delete_points`，只删 stale、绝不清空 collection。
- **行为证明（mock 层，`tests/test_importer_closure.py`）**：V1（A–E 节）→ V2（A–C 节）UPDATE 后——SQLite `chunks`/`chunk_fts`/`embeddings` 三表均无 stale 行；keyword（FTS）、dense、hybrid 检索均无法命中旧 D/E 内容；fake Qdrant `deleted_chunk_ids` 恰为 2 个 stale chunk，剩余 points 与新 chunk 集完全一致。B 节内容改写产生新 chunk_id 时：旧 B point 删除、新 B point 存在、未变节 point 保留。
- **行为证明（真实 Qdrant E2E，`tests/test_importer_qdrant_e2e.py`，隔离 collection `closure_import_e2e_test`，结束即删除；正式 collection 零接触）**：生产 REST adapter 实测 V1→V2 UPDATE——`count_points` 收敛到新版数量；按 document_id filter scroll 只返回新 chunk；dense query 无法返回 stale；`build_index_manifest` + `verify` PASS（expected == actual，orphan 空）；内容改写用例同样通过。

#### Closure 2 — UPDATE failure / repair

- SQLite 已提交完整新版后 Qdrant upsert 中途失败：状态 `FAILED_INDEX`（非 READY）；SQLite Source of Truth 保持完整新版（无 D/E 内容）；`verify` 能检出真实索引不一致（旧 points 识别为 orphan，missing 为空）；对健康后端 `force` 重导（repair）后 points 收敛、verify PASS。mock 与真实 Qdrant 双层证明。不引入分布式事务——失败可检测、可重试、可修复。

#### Closure 3 — duplicate-content policy（冻结）

- `different canonical path → different document_id；same source_hash → duplicate-content candidate；默认允许分别导入`（不做自动去重）。测试证明：path A/B 字节相同 → 两个不同 document_id、相同 source_hash、SQLite 两个 documents、两套 chunk ownership、Qdrant points 按 document_id 归属互不重叠且并集等于全量 points（mock + 真实 Qdrant 双层）。

#### Closure 4 — ZIP bomb 防护（补齐实现）

- 审计发现 DOCX/PPTX 此前仅有 100MB 源文件上限与解压后文本上限，base.py 注释宣称的 member/extraction limits 实际不存在。本轮补齐：`core/parsers/base.py::check_zip_safety` 在交给 python-docx / python-pptx 之前只读 ZIP 中央目录（不解压任何成员数据），强制 `MAX_ZIP_MEMBERS=10000`、`MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES=1GiB`、`MAX_ZIP_MEMBER_UNCOMPRESSED_BYTES=256MiB`，另加压缩比 backstop（`MAX_ZIP_COMPRESSION_RATIO=1000`，仅对 ≥10MB 成员生效，deflate 单层上限 1032:1 不会误伤正常文件）；负数声明大小与损坏/截断中央目录均拒绝（`CorruptDocumentError`）。两个 parser 均在 OLE 检测后、格式库 import 前调用。
- 测试（`tests/test_parsers.py::ZipSafetyGuardTests`，9 项）：normal DOCX/PPTX 预检通过、成员数/总量/单成员超限、压缩比、损坏 ZIP（截断+噪声）、**中央目录声明 1GiB 成员而实际数据 4 字节（证明检查只读元数据不解压）**、DOCX/PPTX parser 在格式库之前触发守卫。全部 fixture 小型化（patch 上限或改写声明大小），零大数据解压。

#### Closure 5 — deferred meta queries（4 条，DEFERRED）

- content ingestion eval = 25/25 PASS；**deferred meta queries = 4，current support = DEFERRED**（不得表述为 PASS）。
- 证据保存于 `docs/deferred_meta_queries.json`（query / source_format / observed_current_behavior / reason_deferred / target_phase）。2026-09-07 用 bge-m3 真实嵌入在 eval 独立库实测：4 条文档级元问题（小节数/标题/幻灯片数/列目录）全部被冻结 Scope Gate 拒答（out_of_scope=true, confidence=low），与历史记录一致；target = Phase E / Router + document-level intent。

#### Design debt 登记 — document_id（本轮不改）

```text
Current:
document_id derived from canonical source path.

Known consequence:
rename/move => new document identity.

Phase D design question:
persisted stable document identity + mutable source_path?
```

留给 Phase D Schema Impact Analysis。

#### Telemetry 隔离修复

- 本轮发现并修复：`tests/test_importer.py`（9 项契约测试）与 `tests/test_general_ingestion.py::CrossFormatEquivalenceTests` 从未重定向 `config.LOG_DIR`，全套件每跑一次就向真实 `data/logs/import_log.jsonl` 追加行。按 Phase A closure 对 test_v2_library 的同类先例补夹具重定向（生产语义不变）；本轮 Gate 期间产生的追加行按字节截断恢复至会话起点状态（SHA256 校验一致），历史行零改动。
- 最终守卫实测：全套件运行前后 `data/logs/qa_log.jsonl`（27409 B，sha256 fe63316b…）与 `data/logs/import_log.jsonl`（171963 B，sha256 f3a5ebc6…）**字节完全一致**。

#### Final Gate（2026-09-07 实测）

| 项目 | 结果 |
|---|---|
| ruff（repo，ruff.toml） | All checks passed |
| Python 语法（core/scripts/tests/desktop compileall） | OK |
| node 语法（web/app.js、web/markdown.js） | OK |
| full unittest | **212/212 PASS**（195 + closure mock 4 + 真实 E2E 4 + ZIP 9；逐模块：document_model 12 / general_ingestion 9 / hybrid_retriever 5 / importer 9 / importer_closure 4 / importer_qdrant_e2e 4 / parsers 26 / proxy_bypass 7 / qdrant_integration 9 / qdrant_store 14 / rebuild_all 4 / reranker 29 / reranker_integration 4 / telemetry_isolation 1 / text_rules 5 / v2_library 35 / vector_store_contract 27 / web_server_v2 8） |
| General Ingestion Eval（25 条，qdrant 后端） | **25/25 PASS**（导入 UNCHANGED 秒级，检索真实嵌入） |
| 教材 Golden Set（eval_recall） | PASS：false_refusal 0.0 / false_accept 0.0 / top1 0.65 / top3 1.0 / compare 1.0（与冻结基线逐项一致） |
| regression_test（真实教材库） | PASS（1 教材 / 7 章 / 617 片段） |
| 教材 Qdrant verify（local_knowledge_chunks） | PASS，617/617，missing/orphan/mismatch 全 0 |
| 通用文档 Qdrant verify（general_documents） | PASS，20/20，missing/orphan/mismatch 全 0 |
| qa_log / import_log 字节守卫 | before == after（size + SHA256 双一致） |

#### 本轮文件变更（Closure Audit）

- **Modified**：`core/parsers/base.py`（ZIP 守卫）、`core/parsers/docx_parser.py`、`core/parsers/pptx_parser.py`（接入守卫）、`tests/test_parsers.py`（+ZipSafetyGuardTests）、`tests/test_importer.py`（仅 LOG_DIR 夹具重定向，测试语义未改）、`tests/test_general_ingestion.py`（CrossFormatEquivalenceTests 同上）、`docs/V3_PROGRESS.md`（本节）
- **Modified（上一会话已改、本轮核验）**：`core/importer.py`（injectable qdrant store + stale 删除）、`core/qdrant_store.py`（scroll_payloads query_filter）
- **Added（上一会话 + 本轮）**：`tests/test_importer_closure.py`（4 项 mock closure 测试）、`tests/test_importer_qdrant_e2e.py`（4 项真实 Qdrant E2E）、`docs/deferred_meta_queries.json`
- **Deleted**：无

#### Gate decision

**Phase C Final Gate = PASS。Phase C 正式关闭。** 未开始 Phase D；等待用户授权。

## Phase D — v3.3

- Status: **PASS**
- Authorized scope: Knowledge Library Manager + Persistent Document Lifecycle + QueryScope（授权合同 42 节 + V3_IMPROVEMENT_PLAN §10/§11）
- Branch / workspace: `Local Database Q&A System本地版v3`
- Rollback snapshot: `..\_phase_backups\kb-v3-phase-d-pre\`（154 源文件 + SHA256 清单 ok=159/bad=0 + textbooks/documents.sqlite3 与 qa/import 日志字节副本）

### Schema Decision（详见 docs/V3_SCHEMA_IMPACT_NOTE_PHASE_D.md）

**v4 → v5 加性迁移，仅用于受管库 `documents.sqlite3`；教材库保持 v4 legacy。** 新增 4 表 2 索引：
`knowledge_bases`（稳定持久化 KB 身份，默认 `kb-default`）/ `document_sources`（stable document identity + 可变 source_path + 持久化 status + enabled + last_error）/ `tags` / `document_tags`。v4 核心 DDL 零改动；`LibraryStore` 版本检查放宽为 {4,5}（v4 读路径对 v5 有效）；`sections` 全量表继续推迟（section_ids scope 显式 DEFERRED，QueryScope 预留字段，越界使用抛 `SectionScopeUnavailableError`）。

生产迁移实测：`scripts/migrate_library.py` → documents.sqlite3 schema_version=5，5 documents / 20 chunks / 20 embeddings 不变，integrity ok，备份 `documents.sqlite3.pre-v5.bak`；Qdrant payload 同步（`sync_index_payloads()`：knowledge_base_id→kb-default + document_type + tags；embedding_model 以 embeddings 表权威值为准）→ general verify 20/20 PASS。

### Changes

- 新增 `core/query_scope.py`：`QueryScope` 合同（None=默认范围 / 空 Scope=默认范围 / `restrict_nothing()`=显式空结果，三者语义严格区分）+ `resolve_scope`（READY+enabled 门禁；KB/type/tag 间接选择排除 disabled；显式 document_ids 可点名 disabled-but-READY；任何路径都不可达 FAILED/DELETING/DELETE_FAILED 文档；legacy v4 库解析为全库）
- 新增 `core/library_service.py`：`ensure_managed_schema`（幂等 v4→v5，事务 + 前后 integrity_check + 行数校验）+ `LibraryService`（KB CRUD、稳定身份导入、relink、enable/disable、安全删除、retry-delete、retry-index、tags、duplicate candidates、statistics、`library_log.jsonl` 操作遥测、Qdrant payload 同步）
- 修改 `core/importer.py`：`import_file(document_id=)` 稳定身份注入（Phase C path-hash 路径不变）；schema 检查接受 v5
- 修改 `core/library_store.py`：`retrieve(scope=)` + `resolve_scope()`；`_fts_search` SQL 级 scope pushdown（`chunk_id IN (SELECT id FROM chunks WHERE document_id IN ...)`）；`chapter_catalog`/`summary_contexts` 支持 document 过滤
- 修改 `core/hybrid_retriever.py`：`allowed_document_ids` 贯穿 FTS + dense；选段防御守卫；空集 scope 显式短路（绝不回退全库）；无向量时 dense_ms 确定性为 0.0
- 修改 `core/vector_store.py`：`VectorScope` + `document_types`/`tags`；`VectorRecord` + `document_type`/`tags`
- 修改 `core/qdrant_store.py`：filter 增加 document_type/tags must 子句；payload 写入新字段；payload index（document_type/tags keyword）
- 修改 `core/engine_v2.py`：`prepare/answer(scope=)`；book 路由材料 scope 化；**Citation Scope 门卫**（`citation.document_id ∈ effective scope`，越界抛 `CitationScopeViolationError`，真实注册文档之外的合成 id 不触发）；QA telemetry 增加 scope_mode/scope_document_count/scope_knowledge_base_count/scope_tag_count/scope_fingerprint（完整 IDs 仅 QA_DEBUG_SCOPE）
- 修改 `desktop/web_server.py`：`/api/v3/library/*`（KB CRUD、documents list/detail/import(路径式)/enable/disable/retry-index/retry-delete/relink/tags/delete，错误映射 400/404/409/500）；`/api/v2/jobs` 接受 `scope`（缓存键含 scope，向后兼容不带 scope 的引擎）
- 修改 `desktop/web_main.py`：装配 LibraryService（失败软降级）
- 新增 `web/library.html` + `web/library.js`（最小 Library Manager：总览/KB/导入/文档表格 + enable/disable/delete(二次确认)/retry-index/retry-delete/标签）；修改 `web/index.html` + `web/app.js`（QA 页 scope 选择器：全部/按知识库/按文档/按标签，选择真实进入 API）
- 新增 `scripts/migrate_library.py`、`scripts/eval_scope.py` + `scripts/scope_eval_set.json`（34 cases）；`scripts/import_document.py` 默认走 LibraryService（`--legacy` 保留 Phase C 直连路径）
- 修改 `tests/fake_qdrant.py`：`_matches` 支持 keyword-array payload 语义（Qdrant tags 一致）

### Tests / Eval

- 全套 **262/262 PASS**（212 基线未删改弱化 + Phase D 50：schema_migration 5 / library_service 22 / scope_propagation 10 / library_qdrant_e2e 5 / web_server_v3 8；逐模块计数见 Closure Audit 附录）
- **Scope Eval：34/34 PASS（sqlite 与 qdrant 双后端），scope leakage = 0，citation leakage = 0，false_accept 0/6，false_refusal 0/28**；§19 隔离用例（KB-A scope 下 BETA_ONLY 不得泄漏）在 dense/FTS/fused/citation 各层断言
- 真实 Qdrant 生命周期 E2E（隔离 collection，TXT/DOCX 各删除一轮）：import→retrieve→delete→points 清空→retrieve 失效→verify PASS；disable/enable 循环数据不变；relink 保身份
- 删除故障注入（§12 A/B/C/D）：Qdrant 不可达 / delete HTTP 500 / malformed result / 部分残留——均不伪装成功、verify 可见、retry 恢复、查询不返回已删文档

### Performance

| 检索（scoped FTS pushdown） | p50 |
|---|---|
| sqlite scoped / unscoped | 3.3 / 3.7 ms |
| qdrant scoped / unscoped | 25.6 / 18.6 ms* |

*qdrant 评测期波动较大（同机 LLM 评测负载）；scope pushdown 无性能惩罚，FTS IN-子查询在 617/20 chunk 规模下开销不可测量。

### Known issues / limitations

- `browser file upload` = **DEFERRED**：Library Manager 采用主机路径导入（本机单用户场景）；若未来实现浏览器上传需独立 endpoint + streaming + allowlist（合同 §23 允许）
- `section_ids` scope = **DEFERRED**（sections 表未持久化，合同 §20 允许，字段已预留）
- 教材库保持 v4 legacy（unmanaged）；Phase E 统一路径已登记（v5 增加教材 KB 归属 + Router 按 KB 路由）
- Qdrant collection 按"一库一 collection"约定共享时，删除后 verify 会以本库 manifest 检出他库 points 为 orphan（DELETE_FAILED，诚实失败）；scope eval 已改用专用 collection
- Qdrant payload 的 tags/type 与 SQLite 注册表的一致性由 LibraryService 写路径同步保证，无后台对账任务

### Rollback

- 源码：恢复 `..\_phase_backups\kb-v3-phase-d-pre\`（SHA256 清单校验）
- 数据：`data/library/documents.sqlite3.pre-v5.bak`（迁移前字节副本）；v5 为加性迁移，v4 代码可直接读 v5 库，无强制降级需求
- 运行时：`VECTOR_BACKEND=sqlite` / `RERANKER_ENABLED=false` 冻结不变；scope 未传时检索管线与 Phase C 行为一致（含缓存键）

### Gate decision

**Phase D = PASS。** Phase D PASS 条件 41 项全部满足（browser upload、section_ids scope 按合同标记 DEFERRED）。未开始 Phase E；等待用户授权。

## Phase D Security Closure Audit（2026-09-08）

Phase D 主体验收后、Phase E 前的短范围收口：Library Manager 本地文件系统安全边界。

### 审计发现与修复

- **发现（真实安全边界问题）**：`POST /api/v3/library/documents` 的 `path` 字段此前直通 `LibraryService.import_document`，服务进程可读取任意本地绝对路径并导入——局域网 Web 客户端获得了不应有的文件系统读取能力。
- **修复（Import Path Policy）**：新增 `core/path_policy.py::ImportPathPolicy`——客户端路径先 `Path.resolve()` canonical 化（跟随 symlink/junction、消解 `..`/相对路径/混合分隔符），再以 `os.path.commonpath` + `os.path.normcase` 对 canonical 根做包含判断（大小写变体安全、跨盘拒绝）；错误信息不回显根目录。`LIBRARY_IMPORT_ROOTS`（os.pathsep 分隔，`.env.example` 已登记）为唯一配置；**未配置 = Web 路径导入默认禁用**。
- **CLI ≠ Web**：CLI（`import_document.py`）以本机用户权限运行、不附加策略；Web（`web_main.py` 装配）强制附加策略——relink 同样受策略约束，不构成绕过后门（域内 relink 保持可用，域外 relink 拒绝，即使 `update_if_changed=true`）。
- **Source Path 泄露治理**：所有 `/api/v3/library` 响应（overview/list/detail/import/relink/duplicate candidates）经 `desktop/library_api_safety.py::redact_source_paths` 递归脱敏——`source_path`/`source` 绝对路径不再出 API，替换为 `source_name`（文件名）+ `source_display`（根内相对路径或文件名）；完整路径仅存 SQLite（CLI 本机输出保留）。UI（library.js / app.js）只消费 safe display 字段。
- **Parser Security 保持**：根内文件仍须通过 extension allowlist / parser registry / 大小上限 / ZIP 安全 / 损坏加密检查（测试断言根内 .exe 由 parser 拒绝且错误为 unsupported_format，非策略错误）。

### 测试与证据

- 新增 `tests/test_path_policy_security.py`（21 项）：根内导入 PASS、`..` traversal 拒绝、域外绝对路径拒绝、相对路径拒绝、**真实 junction/symlink 逃逸拒绝**（环境可创建时实测，否则 skip 并注明原因）、域外 relink 拒绝 + 域内 relink 通过、未配置根默认禁用、CLI 无策略保持 Phase C 行为、根内 parser 安全链保持、list/detail/overview 响应零绝对路径（含盘符正则扫描）+ `source_display` 正确 + SQLite 保留完整路径、未认证 v3 调用仍 401（配对/令牌/Host 校验无回归）。
- 全套回归（Security Closure Gate 实测）：**283/283 PASS**（262 + test_path_policy_security 21）；scope eval sqlite/qdrant 双后端 leakage=0 保持；qa/import telemetry 基线字节不变。

## Phase D.1 Runtime Integration Closure（2026-09-08）

Phase D 主体 + Security Closure 之后的运行时收口：Library Manager 与 QA 运行时的整机整合。授权范围：Runtime Integration / Scope / Error Redaction 收口 + 必要测试/文档/发布修复。**Phase E = NOT STARTED**，等待单独授权。

### 复现的 4 项 P0（修复前 D2 实测，全部确认）

- **P0-01 双库分叉**：Library Manager 写 `documents.sqlite3`，QA Engine 读 `config.LIBRARY_DB`（textbooks.sqlite3）——管理端导入对问答不可见，Qdrant 读写也各指一库；
- **P0-02 运行中变更不可见**：服务运行期间导入/启停/更新/删除后，库快照不重载、指纹不变、答案缓存按旧指纹继续命中；
- **P0-03 书籍级路由 scope 缺口**：book_toc / book_overview / chapter_overview 未按 effective scope 过滤，disabled 文档仍出现在目录（触发 CitationScopeViolationError 崩溃路径）；
- **P0-04 错误体路径泄露 3/3**：missing file / relink / unexpected exception 三类响应均含服务器绝对路径。

### 修复

- 新增 `core/runtime_library.py`：整机唯一库身份的静态三规则——managed 存在即优先并原地升级（v4→v5 纯加性）→ 无 managed 则 legacy 原地接管（同一文件升级，不复制第二真相源）→ 两者皆无则创建空 managed；升级/创建失败显式抛错，绝不静默换库。
- `core/library_service.py`：`on_mutated` 回调（每次提交式变更后触发，自身绝不抛错）；import/relink/delete 全流程变更锁（RLock）串行化；FK 纪律（每连接 `PRAGMA foreign_keys=ON` + 注册表行前先插 placeholder documents 行，其 sha256 置空——否则 importer 的 unchanged-check 会把首次导入误判为 UNCHANGED）。
- `desktop/web_server.py`：`_on_library_mutated`（引擎锁内 `library.refresh()` → `_recompute_fingerprint()` → 清空 LRU 答案缓存）；缓存命中显式 "命中缓存" status 事件。
- `core/library_store.py`：`effective_allowed_ids` 作为单一 scope 真相（检索 pushdown 与 book 路由共用同一文档集）；`refresh()` 原地重载快照；managed（v5）库的 Qdrant collection 绑定 `importer.DEFAULT_GENERAL_COLLECTION`（不再读 `config.QDRANT_COLLECTION`，杜绝 manager/engine 指到不同 collection）；engine health 上报 `schema_version`。
- `desktop/library_api_safety.py`：错误体路径形 token（盘符/UNC/POSIX）统一降为 basename + 导入根整体替换为 `<导入目录>`；含 Windows OSError 双反斜杠归一化（否则根目录名残留泄露）。
- `core/config.py` + pdf parser：`QA_PDF_MAX_PAGES`（默认 2000）/ `QA_PDF_MAX_EXTRACTED_CHARS`（默认 20 MiB）资源守卫，超限 `DocumentTooLargeError`（RESOURCE_LIMIT）类型化拒绝。
- Windows 数据目录方案：仅 ADR + backlog + README 登记，本轮不改行为（见下方 Backlog）。
- 禁用清单全程保持：未把 disabled 文档重新加入默认 scope、未删除 CitationScopeViolationError、未让空 scope 回退全库、未关闭 Host 校验/pairing/path policy、未返回服务器绝对路径、未把 LIBRARY_IMPORT_ROOTS 默认改为任意目录、未删除 ZIP bomb 守卫、无 Qdrant 静默 fallback。

### Backlog（登记，不在当前阶段执行）

- **Windows 数据目录搬迁**：当前 `data/` 目录随程序可移植布局。若未来出现安装到受保护目录（Program Files 等）的真实场景，再设计并搬迁至 `%LOCALAPPDATA%\LocalDatabaseQA\`（含迁移与回滚方案）。本轮不改行为；ADR 见 `docs/V3_RUNTIME_LIBRARY_DECISION.md`。

### 测试

- 新增 `tests/test_runtime_integration.py`（24 项）：真实 LibraryService + 真实 StructuredQAEngine + 真实 WebQAServer + 临时 SQLite + fake 嵌入/模型（无 fake engine 替代）——导入即时可见（P0-01）、空库全拒答、KB/文档/标签 scope、停用/启用即时生效、全停用默认 scope 为空、更新保身份 + 缓存失效（P0-02）、删除、book 路由 scope（目录/缺章列表/全书概览，P0-03）、错误脱敏（盘符/UNC/POSIX/嵌套异常/500/parser 失败，P0-04）、engine health schema 版本、runtime 库选择三规则、v4 原地升级。
- 新增 `tests/test_library_concurrency.py`（1 项）：同路径并发导入（barrier 同步）→ 单一 document_id、状态收敛（READY + UNCHANGED）、document_sources 恰一行。
- 新增 `tests/test_pdf_guard.py`（3 项）：页数/提取字符上限类型化拒绝 + 默认上限正常解析。
- 修正 `tests/test_library_qdrant_e2e.py`：按 D.1 新契约，managed 库 Qdrant collection 绑定 `importer.DEFAULT_GENERAL_COLLECTION`（patch 点同步更新）；本机真实 Qdrant 1.19.1 可达时 5/5 PASS。
- 全套回归（本机，Qdrant 1.19.1 + Ollama 可达，PYTHONUTF8=1/PYTHONIOENCODING=utf-8）：**311/311 PASS**（283 + 28，0 skip）；ruff（repo）/ compileall / node --check（web ×3）全过；telemetry 隔离测试（内嵌子进程全量重跑）PASS。

### Gate decision

**Phase D.1 = PASS**（4 项 P0 关闭 + 回归锁定 + 本地 311/311 + 远端 CI success + 发布同步 0/0 clean，证据见下 D10）。Phase E = NOT STARTED，等待用户单独授权。

## D10 远端 CI 复核与发布记录（2026-09-08）

### 中断恢复审计（Recovery Audit）

上一会话在"Node checks = PASS、Full suite 311 tests / 3 errors、Qdrant 8 vs 1024 维度不匹配"状态下中断。恢复后先做只读审计：本地版v3 与上传版工作树逐文件对比，除 `reranker_service/.venv`（.gitignore 排除的本机资产）外**零漂移**；上传版 HEAD == origin/main == `3416de3`、ahead/behind 0/0、worktree clean——上一轮已把修复同步、提交并推送。

### 311 tests / 3 errors 根因（已闭合）

3 个 error 与上一轮线索"8 维查询 vs 1024 维库/索引"完全吻合，根因是**测试隔离 bug（hermeticity，A 类）**，非生产绑定问题：

1. D.1 把 managed 库的 Qdrant collection 绑定到 `importer.DEFAULT_GENERAL_COLLECTION`（`general_documents`），并明确不再读 `config.QDRANT_COLLECTION`（`core/library_store.py::_vector_collection` + `create_vector_store(collection=...)`）；
2. 但该 e2e 测试仍 patch 旧的 `config.QDRANT_COLLECTION`——生产路径根本不读这个符号，patch 无效；
3. 于是测试用 fake embedder 的 **8 维**向量直写本机真实 Qdrant 的 `general_documents` 集合（真实语料、**1024 维**、20 点），Qdrant 拒绝维度不匹配 → 3 个 error。

修复（已含在 3416de3）：测试 patch 点改为 `importer.DEFAULT_GENERAL_COLLECTION`，e2e 全程使用隔离集合。恢复后本机复跑：该模块 5/5 PASS，全套 **311/311 PASS（0 FAIL / 0 ERROR / 0 skip）**；修复方式未引入静默 keyword fallback、未 pad 向量、未关闭 Qdrant 校验、未 skip 真实集成测试（本机 Qdrant 1.19.1 + Ollama 在线时真实集成测试照常全量执行并 PASS）。

### 远端 CI（GitHub Actions）

- 代码提交 `3416de3`（fix(v3.3): close runtime library integration gaps）：run `34196063045`，**completed / success**（2m24s）；job `test` 五步全绿：Install ingestion dependencies / Lint Python sources / Run unit tests / Compile Python sources / Check browser JavaScript。
- 文档收尾提交（本 D10 记录随其推送）同样经 CI 复核，SHA 见仓库 git log 最新提交。

### 发布记录

- 同步方式：`scripts/publication_sync.py`（allowlist 单向 本地版v3 → 上传版）；`.github/` 为 GitHub-only 资产，脚本不复制不删除，`git ls-files .github` 确认 `ci.yml` 持续受跟踪。
- 上传版复核：ruff / unittest 全量 / compileall / node --check（web ×3）全过；`publication_scan.py` secret/路径扫描全部命中均为认证实现代码、测试期生成 token 与脱敏测试的故意假路径（`C:\Users\secretuser\...`），无真实凭据与本机路径。
- 最终：HEAD == origin/main、ahead/behind 0/0、worktree clean。

## D11 Phase D.1.1 — Legacy Library Migration Compatibility Closure（2026-09-08）

### 现场核验（只读 preflight）

- GitHub main = `57e0bb2`（与已知记录一致），上传版 HEAD == origin/main、ahead/behind 0/0、worktree clean；
- 真实本机：`documents.sqlite3`（v5，5 docs / 20 chunks / bge-m3 1024）、`textbooks.sqlite3`（v4，1 doc `doc-01d13356ce2f` / 617 chunks / 352 pages / bge-m3 1024），两者 integrity ok；
- 迁移前 `resolve_runtime_library()` 在真实机状态正确 **FAIL LOUDLY**（双库有数据 + 无迁移证据）；
- Qdrant 1.19 在线：`general_documents` 20 点（managed）、`local_knowledge_chunks` 617 点（legacy 教材），均 1024 维；
- 发现 v3 已有未发布的 D.1.1 进行中代码（guard + 迁移工具），但含 3 处缺陷且无专用测试——本会话修复后才进入 Gate。

### 本会话修复的工具缺陷（未发布代码审计）

1. `scripts/migrate_legacy_library.py` 缺 `ROOT_DIR` sys.path 引导（直接运行 ModuleNotFoundError）→ 已按仓库统一模式补齐；
2. dry-run 返回结构与非 dry-run 不一致导致 `main()` 取 `result["plan"]` KeyError → 已修；
3. `analyze()` 返回语句后的死代码 → 已删；
4. Windows 上 sqlite3 cursor 引用环在 GC 前持有文件句柄，迁移类测试的临时目录清理失败 → `tests/test_runtime_integration.py` 与 `tests/test_migrate_legacy_library.py` 在 temp cleanup 前补 `gc.collect()`（测试环境修复，非生产行为）。

### 迁移工具与守卫（本次发布内容）

- `core/runtime_library.py` dual-library conflict guard：managed 与 legacy 同时存在且 legacy 含文档时，必须凭 `legacy_migration_completed` 标记 + 逐文档 id/sha256/chunk 数核对证明已吸收，否则 RuntimeError 显式报错并给出修复命令；空 legacy 视为已吸收；绝不 silent managed wins；
- `scripts/migrate_legacy_library.py`：单事务合并（BEGIN IMMEDIATE + 前/后计数与引用完整性校验，失败回滚）；文档/chunk/chapter/summary id 冲突（内容不一致）显式中止；内容逐字节一致则 ALREADY_MIGRATED（幂等 NOOP）；embeddings 逐字节复制（工具不 import Ollama，零重嵌入）；embedding 空间不一致（model/dimension）中止，空目标库采纳源空间；迁移后写证据标记（counts + 源文件名 + 时间戳 + 内容指纹）；`--qdrant-sync` 将 points 收敛进 managed collection `general_documents`（向量取自 SQLite，旧 collection 不删）；
- `core/library_service.py`：`sync_index_payloads(force=True)` / `_sync_document_payload(force=True)` 支持 sqlite 后端下的强制收敛（ops 命令路径）。

### 测试

- 新增 `tests/test_migrate_legacy_library.py`（20 项）：dry-run 零写入、全行合并与 document_id 保留、embeddings 字节级一致、源库绝不修改、证据标记内容、二次运行幂等 NOOP、文档/chunk/chapter/summary id 冲突中止、embedding 空间 model/dimension 不一致中止、空目标采纳源空间、源/目标 schema 版本拒绝、事务中途失败回滚、同文件拒绝、缺文件拒绝、迁移后满足 runtime absorbed 检查、Qdrant 收敛目标为 managed collection；
- `tests/test_runtime_integration.py`：旧 "managed wins" 测试替换为 3 项守卫测试（无证据 FAIL LOUDLY / 有证据服务 managed / 空 legacy 服务 managed）；
- 全套回归（本机，Qdrant 1.19 + Ollama bge-m3 在线）：**333/333 PASS（0 fail / 0 error / 0 skip）**——迁移前与真实迁移后各跑一次；ruff（repo）全过。

### 仓库外备份（`_phase_backups/kb-v3-phase-d11-pre/`）

| 文件 | SHA256 |
|---|---|
| documents.sqlite3 | `34255abf8382622f33da4859c39b06344b7a155a7e8bbe5181e715077fefa912` |
| textbooks.sqlite3 | `bb2a5cd83cb977f6371c4e37b735c10ac992606f4739049f89eb304097c165cc` |
| general_documents.snapshot | `23bd9e9a5cb087d31a6df5df9c63f839199d4b385776204c5626e17589d9928f` |
| local_knowledge_chunks.snapshot | `7207a403c72ee5b1c63b4b7127f9113ca32168d7e6306c78a8e3fb0ba5ed04b2` |

备份 == 源文件逐字节比对通过，清单写入 `SHA256SUMS.txt`。

### Dry-run Gate（全绿后放行真实迁移）

- 计划：`doc-01d13356ce2f` NEW；迁移 617 chunks / 617 embeddings / 7 chapters / 8 summaries / 352 pages；目标总量 6 docs / 637 chunks / 637 embeddings / 17 chapters / 13 summaries / 352 pages；embedding bge-m3/1024 兼容；fingerprint `99da771f66ac1fa942e3a982c1e1eeb518f1d38dbd862b5bc206bce9578dd45f`；
- 零写入验证：dry-run 前后双库 SHA256 完全不变、marker 未出现、exit 0。

### 真实迁移与验证（`--qdrant-sync`，exit 0）

- managed 库：6 docs / 637 chunks / 637 embeddings / 17 chapters / 13 summaries / 352 pages / chunk_fts 637 / document_sources 6，integrity ok；
- `doc-01d13356ce2f`《移动通信 (李兆玉)》page_count 352 完整保留；证据标记完整（counts、源名、时间戳、指纹）；
- embeddings：617/617 与 legacy 逐字节一致（零重嵌入）；
- legacy 库：SHA256 与备份一致（未修改、未删除），仍为 v4；
- 幂等：二次 dry-run 全部 ALREADY_MIGRATED、0 待迁移；
- Qdrant：`general_documents` 20 → 637 点（含教材 617 点）；`local_knowledge_chunks` 保持 617 点未删除；
- runtime：`resolve_runtime_library()` 返回 managed 路径，absorbed check 通过；
- QA 真实冒烟（bge-m3 检索）：教材专属问题（Um接口 / OFDMA）教材 rank 1；与 sample 文档主题重叠的问题（多径衰落 / 均衡）教材 top-10 可见（rank 6）——5 个示例文档本身含移动通信测试语料，排名竞争属语料重叠的预期行为，如实记录，不属于迁移正确性问题。

### 发布与 CI

- 首个发布提交 `7de0e4e`（feat(v3.3): close Phase D.1.1 legacy library migration compatibility closure）经 `publication_sync.py` 同步（+2 改 6 删 0，`.github/` 未触碰）；上传版复核 ruff / unittest 333/333 / compileall / node --check（web ×3）全过，`publication_scan.py` 无真实凭据与本机路径；
- GitHub Actions run `34213629093`：**completed / success**（job test 3m8s，五步全绿：Install ingestion dependencies / Lint Python sources / Run unit tests / Compile Python sources / Check browser JavaScript）；唯一 annotation 为 actions 自身 Node 20 弃用提示（与本仓库代码无关）；
- 本地数据侧：`LOCAL_DATA_COMPATIBILITY = PASS`，`MIGRATION_COMPATIBILITY_CLOSURE = PASS`（证据见本记录上文）；Phase E = NOT STARTED，等待用户单独授权。

## Phase E — v3.4 Router + Query Rewrite + Follow-up Resolution（2026-09-08）

- Status: **PASS**
- Authorized scope: Query Intent Router + Query Rewrite + Follow-up / Pronoun Resolution + Conversation-aware routing + 与 QueryScope / retrieval / book routes 安全接线（分 Gate E0–E4 执行）
- Branch / workspace: `Local Database Q&A System本地版v3`
- Rollback snapshot: `..\_phase_backups\kb-v3-phase-e-pre\`（121 文件 + SHA256SUMS.txt，roundtrip 校验通过）
- 架构决策：`docs/V3_PHASE_E_ROUTER_DECISION.md`

### E0 Recovery / Baseline

- 上传版 HEAD == origin/main == `f6782c3`，worktree clean；本地版v3 无 .git（正常）
- runtime 数据核验（只读）：managed v5 = 6 docs / 637 chunks / 637 embeddings；legacy v4 = 1 doc / 617 chunks（与 D.1.1 一致，未重迁移）
- baseline 全量：**333/333 PASS**（0 fail / 0 error / 0 skip，196.6s）
- 审计结论：现有路由 = classify_route 确定性规则链；现有追问 = looks_like_follow_up + 上一轮问题字符串拼接（naive merge）；缺口 = 无 RouteDecision/置信/原因码、无代词/省略解析、无 topic shift、无 ambiguity、无结构化 history、telemetry 无 original/rewritten

### Changes

- 新增 `core/query_router.py`：单一确定性 Routing Pipeline——`HistoryTurn`（结构化 history 解析）→ `_resolve_followup`（9 类确定性解析规则）→ 最小语义改写（`_attach_referent`）→ `RouteDecision(route, confidence, reason_code, original_question, normalized_question, resolution_status, referent, follow_up, scope_conflict)`。纯规则实现，**无 LLM**（ADR §1 记录边界与理由）；classify_route / looks_like_follow_up / extract_chapter_number / chinese_numeral_to_int / normalize_history / split_compare_entities 迁移至此，engine_v2 保留 re-export（`__all__`），既有 import 合同不变
- 修改 `core/engine_v2.py`：prepare/answer 接入 router；ambiguous → 澄清回答（不检索）；unsupported（问候/无内容）→ 固定引导语；scope_conflict → 范围提示（§8 安全不变量）；`PreparedAnswer.decision` + `AnswerResultV2.history_entry`（加性）；telemetry 新增 route_reason / resolution_status / rewritten_question；clean_location_query 扩展「帮我找一下…的地方」类脚手架
- 修改 `desktop/web_server.py`：`sanitize_history` 白名单透传 route / chapter / document_ids / compare_entities / referent（旧客户端纯 {question, answer} 合同不变）
- 修改 `web/app.js`：history_entry 整体往返（旧服务端无此字段时自动降级）
- 新增测试：`tests/test_query_router.py`（E1，20）、`tests/test_query_rewrite.py`（E2，13）、`tests/test_followup_resolution.py`（E3，26）
- 新增 eval：`eval/phase_e_router_golden.json`（108 cases / 12 类，含中文真实问法、ambiguity、scope-sensitive、topic shift、adversarial）+ `scripts/eval_phase_e_router.py`（离线确定性，含 engine 级 scope leakage 检查：真实临时 v5 库 + fake embedder）
- 新增 `docs/V3_PHASE_E_ROUTER_DECISION.md`；修改 `docs/V3_PROGRESS.md`、`docs/ARCHITECTURE.md`（Router Safety Invariant 由 backlog 约束更新为实现状态）
- 未触碰：RRF/FTS/dense 公式、reranker、embedding、chunking、Qdrant schema、QueryScope contract、citation verification、library lifecycle、D.1.1 migration guard

### Tests / Eval

- 全套回归（本机，Qdrant 1.19 + Ollama 在线）：**392/392 PASS**（333 基线未删改 + Phase E 59；0 fail / 0 error / 0 skip）
- ruff（repo）/ compileall / node --check（web ×3）全过
- Phase E eval（108 cases）：**route accuracy 108/108 = 100%（≥95%）、follow-up 66/66 = 100%（≥90%）、ambiguous false-resolution 0/8 = 0%（≤2%）、scope conflict 10/10、engine scope leakage 0/4 runs**；failure cases 0

### Performance

- deterministic fast-path：**≈15.9 µs/decision**（12k 次决策实测，纯规则无 LLM 调用）
- LLM-assisted path：未启用（无 LLM 组件，ADR §1）

### Known issues / limitations

- 文档级元问题（deferred_meta_queries.json 4 条）仍 DEFERRED：需文档级元数据查询路径，超出本轮 route 枚举，未伪装 PASS
- 纯文本 history 下链式代词追问依赖 history_entry 往返；文本降级路径宁可 AMBIGUOUS
- Phase B reranker efficacy 保持 DEFERRED / RERANKER_ENABLED=false（Phase E 未重开）

### Gate decision

**Phase E = PASS。** READY_FOR_NEXT_PHASE_AUTHORIZATION（Phase F 未授权，STOP）。


## Phase F.0 — 只读就绪审计（2026-09-08）

F.0（只读，未改任何仓库文件）：Summary/Citation AS-IS 审计 + Gap Matrix + 文件级设计 + 内部 Gate 拆分建议（F.1 Summary+Provenance/Invalidation → F.2 确定性 Citation Quality → F.3 Verifier 仅评估 → F.4 Golden/Eval/Release Gate）。关键发现：禁止模式在线上存在（机械摘要→LLM 改写→充当文档摘要 + 单前置 chunk 充当 whole-document overview）；summaries 表零 provenance；Citation coverage/support NOT IMPLEMENTED；golden 集距 TO-BE 目标差距大。

**Phase F.0 = PASS。READY_FOR_PHASE_F_AUTHORIZATION。**

## Phase F.1 — Hierarchical Summary + Provenance / Invalidation（2026-09-08）

授权范围：统一 Summary 生命周期；修正禁止模式；provenance；dependency/invalidation；修复 re-import 静默降级；保持 Phase A–E 行为不回归。Out of scope：Citation Coverage/Support、claim extraction、F.2/F.3/F.4、Golden Set 扩充、Router/QueryRewrite/Retrieval/Reranker/Qdrant 改动。

### 实施

- 新增 `core/summary.py`：SummaryRecord DTO（16 列：8 核心 + 8 provenance）、dependency fingerprint（算法版本 + generator + prompt/model + 有序 source id/hash 的稳定哈希）、extractive section summary（带标题前缀；无正文 → heading_only 显式描述符）、aggregate document summary（多 section 聚合，cap 1200）、`ensure_summary_provenance_schema`（幂等 additive ALTER + metadata `summary_provenance=1` 标记）。
- `core/importer.py`：UPDATE 路径按 section 生成 extractive 摘要行（scope_id=chapter_id、source_ids=该 section 全部 chunk ids、dependency_hash），document 行改为 aggregate（不再用首块文本）；chapters.overview 从同一 record 文本写入（兼容镜像，不漂移）；`_ensure_schema` 补 ensure 调用（新库分支早退 bug 已修）。
- `scripts/build_library.py`：机械章摘要逻辑原样迁入 `mechanical_chapter_summary_text`；`chapter_summary_records` 生成带 provenance 的记录（scope_id 与 chapter_rows 的章节 ID 同公式）；`chapter_summaries` 保留为 8 列 legacy 投影（既有测试兼容）；`rewrite_summaries_with_llm` 改为 SummaryRecord 流并明确标记 `llm_rewrite`（model/prompt_version/generated_at/version+1，source 绑定不变）；库级标签支持 `mixed`（部分改写失败不再误标 mechanical）。
- `core/library_store.py`：`summary_contexts` 在存在 scope_id 列时优先 `c.id = s.scope_id` join、legacy 行按标题相等回落；无列（pre-F.1 库）走原标题 join——读路径双兼容，标题漂移不再丢摘要。
- `core/library_service.py`：`ensure_managed_schema` 对 v4 与已 v5 库都执行幂等 provenance 迁移（提交独立事务，避免与 v4→v5 迁移的显式 BEGIN 冲突）。
- `scripts/migrate_legacy_library.py`：summaries 迁移改为显式 8 核心列 INSERT——目标库新列以默认值把旧行标为 `generator_type='legacy'`，provenance 未知、绝不伪造。

### 行为变化（old → new mapping，均已加回归测试）

- 通用文档 `chapter_overview`：旧 = 章节存在但无摘要行 → 目录 fallback；新 = 章节存在 → 用该章节 extractive 摘要作答（F.1 要求 section summary 真实存在）；章节不存在 → 目录 fallback 文案不变。`test_runtime_integration.test_missing_chapter_lists_scoped_catalog` 相应改用不存在的第 9 章（语义不变：缺摘要 → 列 scoped 目录）。

### 验证（本机）

- 新增 `tests/test_summary_lifecycle.py` 27 项：provenance / hierarchy / invalidation / migration / failure 全覆盖。
- 全套回归：419/419 PASS（392 基线 + 27 新；0 fail / 0 error）。
- Phase E router eval 冻结指标全部保持：route 108/108、follow-up 66/66、ambiguous false-resolution 0/8、scope conflict 10/10、engine scope leakage 0。
- ruff / compileall / node --check 全过。

### Known limitations（不伪装）

- KB Summary / Multi-document Summary：DEFERRED_TO_LATER_PHASE_F（接口与 scope_type 已为 future-ready，无自然低风险实现路径，未声称支持）。
- 同标题 chunk 分组（section→chunk 映射）继承 Phase C 数据模型限制（section_path 首段 = 标题）；summary↔chapter 的 join 已改用稳定 ID。
- 旧程序可读新库（SELECT 均为显式列），但旧程序对新库执行导入/重建会因 16 列位置 INSERT 失败——additive migration 的固有属性，无需 destructive down-migration；代码回滚到 b57e68a 即恢复旧写入路径。
- 发布库摘要内容未重生成（data safety）：legacy textbooks v4（summaries=llm）与 managed v5（structural）的既有行保持原文本，仅被标为 legacy；下次 rebuild / 重导入时以新格式重建。

### Gate decision

**Phase F.1 = PASS。** Phase F overall = IN_PROGRESS（F.2 / F.3 / F.4 = NOT STARTED，等待单独授权，STOP）。

## Phase F.2 — Deterministic Citation Quality Closure（2026-09-08）

- Status: **PASS**
- Authorized scope: 完整 Citation validity / deterministic factual-claim heuristic / Citation Coverage / deterministic Layer-1 Citation Support / CJK key-term / Latin entity / number / unit / multi-citation / SUPPORTED·UNSUPPORTED·UNCERTAIN·NOT_APPLICABLE / unsupported·uncited 行为 / Citation telemetry / 独立离线 eval / 保持 API·UI 向后兼容 / 不破坏 Phase A–F.1 资产
- Branch / workspace: `Local Database Q&A System本地版v3`
- 权威发布基线：`35b439b`（F.1 发布 commit，HEAD == origin/main，ahead/behind 0/0，worktree clean）

### Preflight 冲突报告（以代码为最高事实源）

- 授权提示声称 "Phase F.2 = NOT STARTED"，但现场核验发现 `core/citation_verifier.py`（已含 Claim/CitationVerification/CitationReport DTO、claim segmentation、validity、coverage、四值 support、number+unit check、CJK meta 检测、reason codes）、`tests/test_citation_verifier.py`（31 项）已存在，且 `core/engine_v2.py` 已集成（verify 调用 + telemetry 11 字段）。
- 按权威规则（当前代码 = AS-IS 最高事实源），F.2 实际状态 = **部分实现未闭环**：core + tests + engine 集成已完成；`eval/phase_f_citation_golden.json`、`scripts/eval_phase_f_citation.py`、文档记录、publication sync 缺失。
- 本轮动作：继承已有实现、不重写；补齐缺失 eval/文档/发布，并修复现场核验发现的 2 个真实缺陷。

### 修复的 2 个真实缺陷

1. **renumber 编号错位（真实 bug）**：`engine_v2.py::answer()` 在 `renumber_citations` **之后**才调用 `citation_verifier.verify(answer, ...)`，但 `evidence_texts` 的 key 是 pre-renumber 的原始编号（`1..len(sent_contexts)` + 章节 offset）。模型乱序输出 citation（如 `...结论[2]...结论[1]`）时，renumber 按首次出现重编号（`[2]→1,[1]→2`），导致 clause 被错误配对到另一条 evidence chunk，verify 结果失真。修复：在 renumber 前保存 `pre_renumber_answer`，verify 改用它（与 evidence_texts 编号对齐）。注释原意即如此，代码此前未落实。
2. **斜杠单位误判（真实 bug）**：`_latin_key_terms` 把 `270.833 kbit/s` 提取为 key term `kbits`（去斜杠），但证据里保留 `kbit/s`（`_normalize_compact` 只去空格不去斜杠），`kbits not in "kbit/s"` → 正确 claim 被误判 UNSUPPORTED。修复：`_latin_key_terms` 先用 `_extract_number_units` 识别"数字+单位"，把这些单位从 key-term 集合中排除（单位属于 number/unit check，不属于 key-term check）。`CITATION_VERIFIER_VERSION` 随之 `f2-v1 → f2-v2`（确定性合同变化，eval/telemetry 据此检测 stale 结果）。

### Changes

- 修改 `core/engine_v2.py`：`answer()` 捕获 `pre_renumber_answer` 供 verify 使用（renumber 前），消除 clause↔evidence 错位；其余 F.2 集成（`DeterministicCitationVerifier` 实例化、`verify().to_dict()`、`AnswerResultV2.citation_report` 加性字段、telemetry 11 字段 + `citation_verified` 冻结）保留。
- 修改 `core/citation_verifier.py`：`_latin_key_terms` 排除"数字+单位"单位词（含 `kbit/s` 斜杠单位）；`CITATION_VERIFIER_VERSION = "f2-v2"`。既有 number+unit check（`_extract_number_units`）、claim_body（strip citation markers）、CJK meta 检测（`_is_pure_meta_discourse`）保留。
- 修改 `tests/test_citation_verifier.py`：+`test_unsupported_wrong_unit`（相同数字不同单位 → UNSUPPORTED）+ `test_supported_slash_unit`（`kbit/s` 斜杠单位 → SUPPORTED）。
- 新增 `eval/phase_f_citation_golden.json`：30 条完全离线 fixture，覆盖 21 类（valid/invalid/duplicate/malformed/no citation/partial+full coverage/wrong evidence/wrong document/scope violation/correct+wrong number/correct+wrong unit/Latin entity/CJK entity/unsupported CJK/uncertain paraphrase/multi-citation/mixed/not_applicable）。
- 新增 `scripts/eval_phase_f_citation.py`：纯离线确定性 eval（无 LLM/NLI/embedding/外部服务），逐 case 断言 validity/coverage/support/计数 + verifier version 一致，exit code 0/1。
- 修改 `docs/ARCHITECTURE.md`（Citation Quality AS-IS 小节）、`docs/V3_PROGRESS.md`（本节）。

### Tests / Eval

- `tests/test_citation_verifier.py`：**33/33 PASS**（31 既有未删改 + 2 新）。
- F.2 offline eval：**30/30 PASS**（21 类全覆盖，failure 0，version golden=f2-v2 runtime=f2-v2，wall 1.9ms）。
- 全套回归见下方 "Final Gate"（含 Qdrant 环境脏状态处理说明）。

### Known limitations（不伪装）

- **单位换算超出 deterministic 范围**：`5 GHz` vs `5000 MHz` 这类等值换算在 number check 会因数字不相等被判定 number mismatch（UNSUPPORTED），不会静默判 SUPPORTED——这是 conservative 方向的误判，语义换算属 `F.3 CANDIDATE`。
- **unit mismatch 复用 number mismatch reason code**：wrong-unit 与 wrong-number 均归 `unsupported_number_mismatch`（`mismatched_numbers` 内已携带 `"3.84 kbps"` 这类 unit 信息），未引入独立 unit reason code（避免行为变更，非缺陷）。
- 本模块是 **deterministic Layer-1**，非 semantic entailment / NLI / complete factual verification；不得宣传为语义蕴涵或完整事实核查。
- KB Summary / Multi-document Summary / NLI Citation Verifier / LLM Citation Judge / Coverage 正式质量阈值 / 最终 150–300 Golden Set = **DEFERRED**（`F.3 CANDIDATE` 或后续阶段），未声称支持。

### Rollback

- 源码：`core/citation_verifier.py` 行为变化仅 2 处（`_latin_key_terms` 排除数字单位 + version bump），`core/engine_v2.py` 仅 verify 输入改为 pre-renumber answer；回滚到 F.1 发布 commit `35b439b` 即完全恢复 F.1 行为（F.1 无 citation verifier 集成，verify 输出为 None）。
- 数据：零 schema 变化、零数据迁移、零 Qdrant 变化；无回滚数据成本。
- 运行时：`citation_verified` 字段语义冻结不变；`citation_report` 为加性字段，旧客户端忽略。

### Gate decision

**Phase F.2 = PASS。** Phase F overall = IN_PROGRESS（F.3 / F.4 = NOT STARTED，等待单独授权，STOP）。

## Phase F.3 — Semantic Citation Verifier Decision Gate（2026-09-08）

- Status: **PASS**（评估与决策完成，结论 **DEFER_L2**）
- 阶段性质：EVALUATION / DECISION GATE——只读分析 + 隔离临时评测资产；**未修改任何 production code**，未接入 runtime，未改变 F.2 deterministic verifier / `citation_verified` 语义。
- 决策文档：`docs/V3_PHASE_F3_CITATION_DECISION.md`（含 L1 Capability Matrix、Judge 合同、逐指标对比、决策依据）。

### 核心结论

- 建立 `eval/phase_f3_semantic_challenge.json`（**50 cases** 人工标注 ground truth：SUPPORTED 23 / UNSUPPORTED 20 / UNCERTAIN 7，15 类语义边界）+ `scripts/eval_phase_f3.py`（离线 L1 + Ollama L2 judge 评测，L1 不进外部服务）。
- L1（f2-v2）在语义挑战集：accuracy 0.28，false-support 0.10（5），uncertain rate 0.54（27）——「否定/因果/比较/条件省略」类 token 匹配但语义相反 → false-support（最高风险）。
- 候选 L2（qwen2.5:7b judge，temperature=0，`judge-f3-v1` 冻结合同，复用现有模型零新依赖）：accuracy 0.74，false-support 0.04（2），false-reject 0.08（4）。
- **但 L2 契约未闭合**：从不输出 UNCERTAIN（7 个真 UNCERTAIN 强行二值化全错，resolution accuracy 19/27=0.70）；2 个 false-support 均为「条件省略」未消除；通信领域知识不足（0 dBm=1 mW、20 dB=100 倍、2000 kHz=2 MHz 判错）；延迟 p50 2.74s/case 且与 answer 共用 qwen2.5:7b（Strategy A 不可接受）。
- **决策 = DEFER_L2**：L2 有明确价值（accuracy +0.46、false-support -0.06），但 judge 契约未闭合 + 真实回答级语义难度分布未知（本挑战集为人工困难集，L1 在 F.2 逐字分布下为 30/30）。触发 IMPLEMENT_L2 复评条件：F.4 真实 Golden Set 建立后量化真实 uncertain rate；judge prompt 调优实现正确 UNCERTAIN 输出；Strategy B/C 在真实分布下证明延迟可接受。

### F.2 Regression 确认

- F.2 offline eval 30/30 PASS；Phase E router eval 冻结指标保持（route 108/108、follow-up 66/66、ambiguous 0/8、scope conflict 10/10、leakage 0）；F.1 / deterministic verifier 零改动。

### Gate decision

**Phase F.3 = PASS。** Phase F overall = IN_PROGRESS（F.4 = NOT STARTED）。按合同 **STOP**：不实施 L2、不进入 F.4、不扩充最终 Golden Set，等待新的单独授权。

## Phase F.4 — Golden Set / Answer Quality / Release Quality Closure（2026-09-08）

- Status: **Engineering / Evaluation Closure PASS**（Phase F 实现与评估基础设施闭环；Product Quality DoD 见本文件末尾 Remediation 记录）
- 最终判定：**Phase F.4 工程/评估闭环 = PASS**。原「V3 Definition of Done = PASS」声明经 Final Truthfulness Audit 裁决为证据不足（overclaim）。
- 决策文档：`docs/V3_PHASE_F4_RELEASE_GATE.md`（实测指标 + Release Gate 冻结 + DoD audit + KB/Multi-doc Summary 裁决）

### 交付

- 新增 `eval/v3_final_golden.json`：**185 cases**（single_fact_qa 41 / locate 20 / compare 20 / multi_turn 20 / multi_document 20 / oos_hard_negative 29 / metadata_library 15 / citation_negative 20），8 类覆盖，ground truth 人工标注可复核，与 evaluator 分离。
- 新增 `scripts/eval_v3_release.py`：分层评测（Layer1 Retrieval / Layer2 Scope / Layer3 Router / Layer5 Answer / Layer6 Citation），`--layer fast`（确定性，无模型）与 `--layer answer`（需 Ollama，仅本地）。

### 实测指标（真实多文档库 documents.sqlite3，637 chunks）

- Retrieval recall@3 = **0.8158**；false-refusal = **0.0278**；route accuracy = **0.9189**（修正 GOLDEN_ERROR 后）。
- Answer fact accuracy = **0.65**（40 代表性样本，受 expected_answer_facts 关键词精确匹配限制）。
- Citation：**invalid citation = 0**（validity 100% 安全）；avg coverage = **0.6646**（66.5%）；deterministic support 分布 SUPPORTED 16.5% / UNSUPPORTED 49.6% / UNCERTAIN 33.8%。
- 纯离题 hard negative 7/7 正确拒答；语义陷阱类（negation/causal/comparison/缩写歧义/混入无关词）系统性 false-accept（22/29，EXPECTED_LIMITATION）。

### 关键决策

- **Citation Coverage 不采用 90% 硬阈值**（实测 66.5%），冻结为质量观察指标 + `invalid citation = 0` 为 HARD GATE。
- **L1 真实分布复评**：真实 uncertain rate = 33.8%（非零），L2 有理论价值空间，但 judge 契约 + 延迟未闭合，**维持 DEFER_L2**。
- **KB / Multi-document Summary 裁决 = Option B**：现有 multi-document QA 已满足核心需求，KB Summary 属 deferred 非核心增强（修订 DoD 范围，非阻断）。
- **文档级元数据查询 DEFERRED** 实测确认（11 条：5 条 scope 拒答、6 条错误放行）。

### Regression 确认

- F.2 offline eval 30/30 PASS；Phase E router eval 冻结指标保持；F.1 / F.3 / deterministic verifier 零改动；ruff 全过。

### Gate decision

**Phase F.4 工程/评估闭环 = PASS（实现与评估基础设施已完成）。** Product Quality DoD 与 V3 DoD 的最终状态经 Final Truthfulness Audit 重新裁决，见本文件末尾「Truthfulness Remediation」记录。按合同完成发布、CI 与 remote closure 后 STOP，不自动开启 L2 implementation / Phase G / 公网部署 / 新架构重构。

> **⚠️ 审计纠正（2026-09-09）**：上述 F.4「V3 DoD = PASS」声明在 Final Truthfulness Audit 中被判定为**证据不足（overclaim）**。F.4.1 关闭了工程/评估层面的 6 项缺口（144/144 answer、citation 用户可见、metadata guard、TTFT、DoD Option B 落实、文档真值），但**产品质量验收标准仍未独立满足**（answer fact accuracy 0.6111 与 citation coverage 0.5534 缺乏独立 quality acceptance threshold）。最终状态见本文件末尾「Truthfulness Remediation」记录。

## Phase F.4.1 — Final Closure Remediation（2026-09-09）

- Status: **PASS**
- 性质：Phase F.4 最小收口修复（关闭 Final Truthfulness Audit 确认的 6 项缺口，不重新实施 F.4）
- 决策文档：`docs/V3_PHASE_F4.1_CLOSURE.md` + `docs/V3_DOD_SCOPE_AMENDMENT.md`

### 关闭的 6 项缺口

1. **ANSWER_LEVEL_CLOSURE_INCOMPLETE** → 新增 `scripts/eval_v3_answer_full.py`（断点续跑 cache），**144/144 answer/citation 全量**（answer fact accuracy 0.611，missing fact rate 0.175）。
2. **CITATION_CLOSURE_INCOMPLETE** → `engine_v2.py`：deterministic UNSUPPORTED/invalid 时 `citation_verified=false`（answer 保留不删句，前端既有 warning 自动触发）。144-case citation：invalid=0、scope violation=0、coverage 0.553、UNSUPPORTED 346（其中 no_evidence 301=uncited claim + number_mismatch 35=high-confidence + missing_key_term 10=L1 false-negative）。
3. **Metadata deferred-query contract violation** → `query_router.py` 新增 `is_deferred_metadata_query` + `DEFERRED_METADATA_PATTERNS`：11 条文档级元数据查询全部 route=unsupported + ctx=0（不进 RAG），book_toc/book_overview 无回归，Phase E 108/108 保持。
4. **PERFORMANCE_DOD_EVIDENCE_INCOMPLETE** → MODEL TTFT p50 2.14s/p95 2.22s（streaming，标注 model-side）；E2E total answer latency p50 19.77s/p95 50.89s（144-case 实测）。
5. **DOD_SCOPE_AMENDMENT_AUTHORIZED_BUT_NOT_APPLIED** → 新增 `docs/V3_DOD_SCOPE_AMENDMENT.md`（Option B 正式落实）+ `V3_IMPROVEMENT_PLAN.md` 加 amendment note。
6. **Documentation truthfulness** → README（阶段表更新到 F.4.1 + 测试数 453）、ARCHITECTURE（F.3/F.4/F.4.1 AS-IS）、本文件（F.4 过度 PASS 审计纠正 + 本记录）。

### Regression

- ruff / compileall / node 全过；F.2 offline eval 30/30 PASS；Phase E router eval 108/108 冻结指标保持；F.1 / F.3 / deterministic verifier 零改动。

### Gate decision

**Phase F.4.1 = Closure PASS（6 项工程/评估缺口关闭）。** Product Quality DoD 与 V3 DoD 的最终状态经 Final Truthfulness Audit 重新裁决为 overclaim，见本文件末尾「Truthfulness Remediation」记录。按合同 STOP，等待新授权。

## Truthfulness Remediation — Quality Acceptance Contract Freeze（2026-09-09）

- Status: **Final Truthfulness Remediation = PASS（文档真值修复 + 质量合同冻结）**
- 性质：修正 Final Truthfulness Audit 确认的 overclaim；区分 Engineering Closure 与 Product Quality DoD；修正指标命名；建立非 post-hoc 的产品质量接受合同。**未修改 production code / tests / Golden / evaluator / threshold 实现。**

### 修正的 overclaim

- 原「V3 Definition of Done = PASS」→ 修正为 5 项独立状态（见下）。
- 原「Phase F overall = PASS」→ 修正为「Phase F Engineering / Evaluation Closure = PASS」（避免读者误以为 Product Quality 已达标）。
- 原「answer fact accuracy = 0.6111」与「fact present 259/314」混称「回答事实准确率」→ 修正为两个独立指标（见下）。

### 最终独立状态（Final Truthfulness Audit 冻结）

```text
Engineering Closure       = PASS
Evaluation Infrastructure = PASS
Quality Baseline          = FROZEN
Product Quality DoD       = NOT_YET_PASS
V3 Release Readiness      = CONDITIONALLY_READY
```

### 指标命名修正（Metric Glossary）

| 旧名 | 新名 | 值 | 定义 |
|---|---|---|---|
| answer fact accuracy | case_exact_fact_match_rate | 0.6111 | case 所有 expected facts 均命中且非拒答才算通过 |
| （混称） | fact_recall | 0.8248（259/314） | 单个 expected fact 命中比例 |
| （混称） | missing_fact_rate | 0.1752 | 1 - fact_recall |
| citation coverage | citation_coverage | 0.5534 | cited factual claims / factual claims |
| （新） | high_confidence_unsupported_rate | 0.0812（45/554） | (number_mismatch + missing_key_term) / total claims |

### Citation 指标拆分（禁止混称）

- Citation Validity：invalid citation = 0（hard gate，✅）
- Citation Scope Safety：scope violation = 0（hard gate，✅）
- Citation Coverage：0.5534（quality gate，待用户冻结阈值）
- Citation Deterministic Support：SUPPORTED 54 / UNSUPPORTED 346（no_evidence 301 + number_mismatch 35 + missing_key_term 10）/ UNCERTAIN 154

### 交付

- 新增 `docs/V3_QUALITY_ACCEPTANCE_CONTRACT.md`：产品质量接受合同（draft），区分 `CURRENT_REGRESSION_BASELINE` 与 `PRODUCT_QUALITY_THRESHOLD`，含 Metric Glossary、Candidate Quality Contract（Minimum/Target/Stretch 三档）、Threshold Provenance Table、阈值来源规则、Citation Coverage 专门裁决、L2 触发条件。
- 新增 `eval/v3_quality_acceptance.json`：机器可读合同（version `quality-contract-v1-draft`，frozen=false）。
- 新增 `tests/test_quality_acceptance.py`：合同 validator（14 项，校验 schema / 阈值语义分离 / hard gate 绝对零 / USER_DECISION_REQUIRED）。
- 修正 `README.md`（阶段状态 + 最终状态声明）、`docs/V3_PHASE_F4_RELEASE_GATE.md`（threshold provenance + 最终判定）、`docs/V3_PHASE_F4.1_CLOSURE.md`（Gate decision + threshold truthfulness）、`docs/ARCHITECTURE.md`（V3 DoD 状态）、本文件。

### 阈值来源（合法 / 禁止）

- 合法：原始 V3 计划目标（如 citation coverage 90%）、UX 要求、质量风险等级、可解释工程标准、人工审核需求。
- 禁止：「当前 baseline 是 X，所以 threshold 设为略低于 X」——只能叫 regression threshold，不能叫 quality acceptance threshold。

### 待用户决策（USER_DECISION_REQUIRED）

| Metric | 当前 baseline | 候选（Min / Target / Stretch） |
|---|---|---|
| case_exact_fact_match_rate | 0.6111 | ≥0.70 / ≥0.80 / ≥0.90 |
| fact_recall | 0.8248 | ≥0.85 / ≥0.90 / ≥0.95 |
| false_refusal_rate | 0.0278 | ≤0.05 / ≤0.03 / ≤0.01 |
| citation_coverage | 0.5534 | ≥0.70 / ≥0.80 / ≥0.90 |
| high_confidence_unsupported_rate | 0.0812 | ≤0.10 / ≤0.05 / ≤0.02 |

### Gate decision

**Final Truthfulness Remediation = PASS。** 产品状态保持：Engineering Closure = PASS / Evaluation Infrastructure = PASS / Quality Baseline = FROZEN / Product Quality DoD = NOT_YET_PASS / V3 Release Readiness = CONDITIONALLY_READY。按合同 STOP：不开始质量优化代码、不重跑 144-case、不修改 Prompt/Retriever/Citation、不实施 L2、不进入 Phase G。等待用户明确冻结 Product Quality Acceptance Contract。
