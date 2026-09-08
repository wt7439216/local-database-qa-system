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

### Gate decision（本地初评）

**Phase D.1 本地验收 = PASS**（4 项 P0 关闭 + 回归锁定 + 311/311）。远端 CI 复核与发布记录见 D10。Phase E = NOT STARTED，等待用户单独授权。
