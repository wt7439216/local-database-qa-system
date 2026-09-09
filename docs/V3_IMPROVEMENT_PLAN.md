# 本地知识库问答系统 V3 改进与实施规范

> **文档类型**：Agent / Codex 执行规范（TO-BE）  
> **推荐仓库路径**：`docs/V3_IMPROVEMENT_PLAN.md`  
> **项目仓库**：`wt7439216/local-database-qa-system`  
> **基线分支**：`main`  
> **基线提交**：`d0ad1bef46c822b97e4f2b37ea22ba36e06c2a34`  
> **基线日期**：2026-09-06  
> **初始状态**：`PLANNED / NOT_AUTHORIZED`  
> **目标定位**：从“本地教材问答系统”演进为“通用本地知识库问答系统”  
> **核心原则**：本地优先、证据优先、结构化真相源、索引可重建、增量演进、可测试、可回滚。

---

> **⚠️ DoD Scope Amendment（`dod-amendment-v1`，2026-09-09）**：原 §13.1 与 §23.3 要求的 **KB Summary / Multi-document Summary** 已按 Phase F.4 授权 §24 的 **Option B** 正式裁决为 **DEFERRED（非阻断）**。裁决理由、非阻断依据与复评条件见 `docs/V3_DOD_SCOPE_AMENDMENT.md`。本文件其余部分仍是 TO-BE 合同，未改为执行日志。

## 0. 本文档如何使用

本文档不是对当前项目已经实现能力的描述，也不是要求 Agent 一次性完成全部 V3 改造。

它是一份 **阶段化实施合同**。

任何 Agent、Codex、ChatGPT Work 或人工开发者在执行 V3 工作时，都必须先读取当前仓库，再读取本文档，并严格遵循阶段 Gate。

### 0.1 三份文档的职责必须分离

仓库后续建议保持以下语义：

```text
docs/
├─ ARCHITECTURE.md
│  └─ AS-IS：当前代码已经真实实现的架构
│
├─ V3_IMPROVEMENT_PLAN.md
│  └─ TO-BE：未来目标、阶段边界、验收与回滚规范
│
├─ V3_PROGRESS.md
│  └─ TRANSITION：当前执行到哪个阶段、证据、结果、阻塞
│
└─ reference/
   └─ 本地知识库问答系统_v3_详细改进方案.docx
      └─ 人类阅读/归档参考版，不作为代码事实的最高权威
```

**禁止**把计划能力直接写入 `ARCHITECTURE.md`，除非对应代码、测试与验收已经真实完成。

### 0.2 权威来源优先级

若本文档、旧文档与当前代码存在冲突，按以下顺序判断：

1. **当前授权基线的仓库代码、测试和实际数据结构**
2. `docs/ARCHITECTURE.md` 中与代码一致的 AS-IS 描述
3. 本文档 `docs/V3_IMPROVEMENT_PLAN.md`
4. `docs/reference/本地知识库问答系统_v3_详细改进方案.docx`
5. Agent 自己的推断

Agent 不得为了“符合计划”而否认仓库事实。

若发现冲突，必须：

- 标出冲突；
- 说明真实代码行为；
- 评估对本阶段设计的影响；
- 选择最小风险方案；
- 若冲突会扩大本阶段 Scope，则停止该冲突项并请求后续授权。

### 0.3 本文档中的状态词

| 状态 | 含义 |
|---|---|
| `PLANNED` | 已规划，尚未授权执行 |
| `AUDITING` | 正在进行只读现状审计 |
| `READY_FOR_AUTHORIZATION` | 方案与基线已核对，可以请求授权 |
| `AUTHORIZED` | 用户明确授权当前阶段实施 |
| `IN_PROGRESS` | 当前阶段正在修改代码 |
| `BLOCKED` | 出现无法在本阶段安全解决的阻塞 |
| `VALIDATING` | 实现结束，正在执行测试/回归/性能验证 |
| `PASS` | 当前阶段全部验收条件满足 |
| `FAIL` | 验收失败，禁止进入下一阶段 |
| `ROLLED_BACK` | 已回到阶段开始前稳定状态 |
| `DEFERRED` | 明确推迟，不影响当前 Gate |

**只有 `PASS` 才允许进入下一阶段。**

---

# 1. V2 基线与不可破坏资产

## 1.1 当前系统的真实基线

以基线提交为准，当前项目已经具备以下重要能力：

- SQLite v4 结构化知识库；
- `documents / pages / chapters / chunks / summaries / metadata` 等结构；
- FTS5 正文与标题全文检索；
- 中文 2/3-gram 等词法处理；
- Dense Embedding 检索；
- Lexical + Dense 的 RRF 融合；
- OCR 质量折扣、标题增强、去重、范围判断；
- 书籍/章节/定位/比较/普通 QA 等确定性路由；
- 多轮历史的有限支持；
- Ollama 本地 Embedding / LLM；
- 流式回答；
- 页码/章节级 Citation；
- 引用编号清洗与部分支持性校验；
- telemetry；
- Web/桌面访问；
- 局域网配对、安全响应头、Host 校验等；
- Golden Set / regression 工具；
- 单元测试与 GitHub Actions CI；
- 原子式知识库重建，失败时保护旧库。

这些能力是 V3 的资产，不是需要“为了现代化”推翻的旧代码。

## 1.2 当前最关键的结构性不足

V3 主要解决以下问题：

1. Dense Retrieval 当前仍适合小库，长期不应依赖 O(N) 全库逐向量扫描。
2. 数据与 Router 语义明显偏教材，需要通用化为文档/章节/区块/页面/标签/知识库 Scope。
3. 缺少知识库、文档、标签等正式 Query Scope。
4. 缺少独立二阶段 Reranker。
5. 多轮追问主要依赖拼接，缺少可测试的 standalone query rewrite / coreference resolution。
6. Embedding 模型、维度、阈值、索引元数据需要形成一致性合同。
7. Summary 体系需要层次化。
8. Citation 仍需要覆盖率与证据支持验证。
9. Golden Set 需要扩展到多文档、多格式、跨文档、追问、难负例。
10. 缺少 Library Manager，知识库还没有形成完整的“导入—处理—索引—管理—问答”生命周期。

---

# 2. V3 总体目标架构

## 2.1 推荐架构

```text
PDF / DOCX / PPTX / TXT / Markdown
                 │
                 ▼
      Parser Adapter + OCR Fallback
                 │
                 ▼
       Normalized Document Model
                 │
                 ▼
       Structure-aware Chunking
                 │
        ┌────────┴─────────┐
        │                  │
        ▼                  ▼
┌────────────────┐  ┌─────────────────┐
│     SQLite     │  │     Qdrant      │
│ Source of Truth│  │ Rebuildable ANN │
│                │  │ Vector Index    │
│ documents      │  │                 │
│ sections       │  │ vector          │
│ pages/blocks   │  │ chunk_id        │
│ chunks         │  │ document_id     │
│ summaries      │  │ KB/scope fields │
│ metadata       │  │ model/version   │
│ FTS5 / BM25    │  │ filter payload  │
└───────┬────────┘  └────────┬────────┘
        │                    │
        └──────────┬─────────┘
                   ▼
             Hybrid Retriever
        FTS5 + Dense ANN + RRF
                   │
                   ▼
                Reranker
                   │
                   ▼
             Scope / OOS Gate
                   │
                   ▼
             Context Builder
                   │
                   ▼
             Local Ollama LLM
                   │
                   ▼
       Citation / Evidence Verifier
                   │
                   ▼
          Local Web / Desktop UI
```

## 2.2 存储职责必须明确

### SQLite：唯一业务真相源

SQLite 至少负责：

- 知识库；
- 文档；
- 文档哈希；
- 导入状态；
- 页面/区块；
- 层级结构；
- Chunk 原文；
- FTS 索引；
- Summary；
- 标签与元数据；
- 处理版本；
- 索引版本引用；
- 文档删除/更新状态。

### Qdrant：可重建的 Dense Vector Index

Qdrant 负责：

- Dense vector；
- ANN search；
- 查询过滤需要的最小 payload；
- `chunk_id` / `document_id` / `knowledge_base_id` 等定位信息；
- embedding model/version/dimension 等索引一致性元数据。

### 绝对约束

> **Qdrant 不是第二个业务真相源。**

以下情况必须成立：

```text
SQLite 存在 + Qdrant 丢失
→ 可以完整重建 Qdrant
→ 不丢失知识库业务数据

Qdrant 存在 + SQLite 丢失
→ 不视为完整知识库
→ 不允许仅依靠 Qdrant 恢复业务真相
```

---

# 3. 全局工程不变量（所有阶段都适用）

以下不变量优先级高于单阶段便利性。

## 3.1 数据不变量

- `chunk_id` 必须稳定、唯一、可追踪。
- 原始 Chunk 文本以 SQLite 为权威。
- Qdrant point 必须能通过稳定 ID 回查 SQLite。
- 删除文档时，不允许产生“SQLite 已删除但检索仍可命中幽灵向量”的长期静默状态。
- 更新文档时必须有明确的旧索引清理/替换策略。
- embedding model、dimension、normalization strategy 必须可识别。
- 不允许不同 embedding 模型的向量无标记混存在同一逻辑索引中。
- Index 不一致必须能够被 `verify` 检测。
- Index 必须能够被 `rebuild` 修复。

## 3.2 行为不变量

- 已有 v2 问答路径不能在无证据情况下被悄悄改变。
- Existing Golden Set 必须先冻结基线，再比较新实现。
- 不允许通过降低阈值、删除难例或弱化测试来“获得 PASS”。
- 不允许用 LLM 猜测数据库状态。
- 离题问题继续拒答，不因引入 Qdrant/Reranker 而取消 Scope Gate。
- Citation 不能自动伪造。
- 最终传给 LLM 的上下文必须能映射到真实 Chunk。

## 3.3 工程不变量

- 一个阶段只做一个主要架构目标。
- 每个阶段必须可独立回滚。
- 新后端在验证前必须 Feature Flag / Adapter 化。
- 不允许在实现 V3.0 时顺手重写 UI。
- 不允许在实现 V3.1 时顺手引入 LLM Router。
- 不允许在实现 V3.2 时删除原 PDF 路径，除非新 Parser Contract 已通过回归。
- 不允许“为了更漂亮”进行与当前阶段无关的大规模重命名。
- 不允许删除现有测试。
- Schema change 必须给出迁移或重建路径。
- `main` 应保持可运行；推荐阶段工作使用独立 feature branch。

## 3.4 文档不变量

阶段 `PASS` 后才能：

- 更新 `ARCHITECTURE.md` 为新 AS-IS；
- 将对应功能从“计划”表述改成“已实现”；
- 在 README 中宣传；
- 更新简历项目描述。

---

# 4. Agent 执行合同

## 4.1 每次执行前必须先做只读 Preflight

Agent 在任何阶段修改代码前必须输出：

1. 当前分支；
2. 当前 HEAD；
3. 工作树是否干净；
4. Python 版本；
5. 关键服务可用性；
6. 当前测试结果；
7. 当前阶段 Scope；
8. 明确列出 Out of Scope；
9. 本阶段预期修改文件；
10. 回滚点。

若工作树存在不明修改，不得直接覆盖。

## 4.2 授权边界

用户只授权一个 Phase 时：

```text
允许：
当前 Phase Scope 内的必要代码、测试、文档

禁止：
提前实现下一 Phase
大规模顺手重构
自行改变产品目标
删除兼容路径
未经授权升级所有依赖
```

如果 Agent 认为必须跨 Phase 才能安全完成：

- 停止该部分；
- 标为 `BLOCKED`;
- 解释依赖；
- 给出最小跨阶段建议；
- 等待授权。

## 4.3 每轮完成后的统一报告

Agent 必须按以下结构输出：

```text
A. 本轮授权范围
B. 实际修改文件清单
C. 核心设计变化
D. 数据/Schema/API 变化
E. 测试命令与结果
F. 回归指标对比
G. 性能数据（若适用）
H. 失败/警告/已知限制
I. 回滚方式
J. 阶段状态：PASS / FAIL / BLOCKED
K. 下一阶段建议（只建议，不执行）
```

---

# 5. 阶段总览与 Gate

| Phase | 版本 | 目标 | 初始状态 | 下一阶段前必须通过 |
|---|---|---|---|---|
| Phase 0 | Audit | 冻结 v2 事实与基线 | REQUIRED | 审计报告、测试基线、性能基线 |
| Phase A | v3.0 | Vector Backend 解耦 + Qdrant | PLANNED | 双后端、索引一致性、回归、回滚 |
| Phase B | v3.1 | Hybrid Retriever + Reranker | PLANNED | Rerank 增益、无明显拒答回归、可关闭 |
| Phase C | v3.2 | 通用文档导入 + 通用结构 | PLANNED | 多格式 Parser Contract、增量导入 |
| Phase D | v3.3 | Knowledge Library Manager | PLANNED | CRUD 生命周期、安全删除、状态可见 |
| Phase E | v3.4 | Router + Query Rewrite + 多轮 | PLANNED | 路由/Rewrite 独立评测、规则优先 |
| Phase F | v3.5 | Summary + Citation + Eval 闭环 | PLANNED | 多文档质量门槛、Citation 质量闭环 |

---

# 6. Phase 0 — V3 前置只读审计

**状态**：`REQUIRED`  
**性质**：只读，不修改代码。  
**目标**：禁止基于旧记忆或方案文档直接动手。

## 6.1 Scope

Agent 必须核对：

- `README.md`
- `docs/ARCHITECTURE.md`
- `core/`
- `scripts/`
- `desktop/`
- `web/`
- `tests/`
- `.github/workflows/`
- `requirements*.txt`
- `.env.example`
- `rebuild_all.py`
- 当前数据库 Schema 构建逻辑
- Golden Set / regression / telemetry

## 6.2 必须输出 Gap Matrix

至少包含：

| 项目 | 当前实现 | V3 目标 | Gap | Phase |
|---|---|---|---|---|
| Dense backend | 实测 | Qdrant ANN | ... | v3.0 |
| FTS | 实测 | 保留/解耦 | ... | v3.0 |
| Reranker | 实测 | 二阶段 | ... | v3.1 |
| Parser | 实测 | 多格式 | ... | v3.2 |
| Scope | 实测 | KB/doc/tag | ... | v3.2/v3.3 |
| Router | 实测 | Rule-first + LLM fallback | ... | v3.4 |
| Rewrite | 实测 | standalone query | ... | v3.4 |
| Summary | 实测 | hierarchical | ... | v3.5 |
| Citation | 实测 | coverage + support | ... | v3.5 |
| CI/Eval | 实测 | 分层质量 Gate | ... | v3.5 |

## 6.3 基线冻结

至少记录：

- 当前全部单元测试数量与结果；
- 当前 regression/golden 指标；
- 典型 10～20 个 Query 的 Top-K；
- 当前 Dense latency；
- 当前 FTS latency；
- 当前 end-to-end latency；
- 当前数据库 chunk 数；
- embedding 模型、维度；
- 当前配置默认值；
- 当前库 fingerprint；
- 当前拒答样例结果。

**注意**：测试数量必须从当前运行结果读取，不把历史“52 tests”写死成永久门槛。

## 6.4 Exit Criteria

Phase 0 只有在以下条件满足时才 `PASS`：

- [ ] 没有修改项目文件；
- [ ] 基线 HEAD 明确；
- [ ] Gap Matrix 完成；
- [ ] 测试基线完成；
- [ ] Retrieval 基线完成；
- [ ] 当前数据 Schema 已核实；
- [ ] 第一阶段文件级方案与实际代码一致；
- [ ] 未发现必须先解决的高危未提交状态。

---

# 7. Phase A — v3.0 Vector Backend 解耦与 Qdrant

**状态**：`PLANNED`  
**优先级**：P0  
**主要目标**：把 Dense Retrieval 从 `LibraryStore` 中解耦，并引入 Qdrant，但不破坏当前 SQLite 路径。

---

## 7.1 Scope

本阶段只做：

1. 冻结 v2 Retrieval baseline；
2. 抽象 Vector Backend；
3. 保留现有 SQLite/in-memory brute-force backend；
4. 新增 Qdrant backend；
5. 把 Hybrid Retrieval 与 SQLite Storage 解耦；
6. 提供 Qdrant collection bootstrap；
7. 提供索引 build/rebuild/verify；
8. 支持 `document_id` 和 `knowledge_base_id` 等必要过滤；
9. 提供 backend health；
10. 用 Feature Flag 选择 backend；
11. 进行双后端回归对比；
12. 更新文档但不宣传后续未实现功能。

## 7.2 Out of Scope

本阶段禁止：

- Reranker；
- LLM Router；
- Query Rewrite；
- Library Manager UI；
- DOCX/PPTX Parser；
- Citation NLI；
- 大规模 Schema 通用化；
- 把 Sparse Retrieval 一起迁到 Qdrant；
- 删除旧 Dense backend；
- 改写回答 Prompt；
- 重做前端。

---

## 7.3 推荐文件边界

以下是目标结构，不要求 Agent 机械照搬文件名；若当前代码结构更适合其他拆法，必须解释。

```text
core/
├─ library_store.py
│  └─ SQLite：业务记录、FTS、summary、metadata、Chunk 回查
│
├─ vector_store.py              # 新
│  └─ VectorStore Protocol / DTO / error contract
│
├─ sqlite_vector_store.py       # 新或适配现有逻辑
│  └─ 保留原始 brute-force baseline
│
├─ qdrant_store.py              # 新
│  └─ Qdrant collection/search/upsert/delete/health
│
├─ hybrid_retriever.py          # 新
│  └─ lexical + vector + RRF + dedup + scope
│
└─ config.py
   └─ backend 配置、URL、collection、timeout 等

scripts/
├─ rebuild_vector_index.py      # 新
├─ verify_vector_index.py       # 新
└─ benchmark_retrieval.py       # 新或扩展已有脚本

tests/
├─ test_vector_store_contract.py
├─ test_qdrant_store.py
├─ test_hybrid_retriever.py
└─ regression tests
```

---

## 7.4 VectorStore Contract

最低建议接口：

```python
class VectorStore(Protocol):
    def health(self) -> VectorHealth:
        ...

    def search(
        self,
        vector: list[float],
        *,
        limit: int,
        scope: VectorScope | None = None,
    ) -> list[VectorHit]:
        ...

    def upsert(self, records: list[VectorRecord]) -> None:
        ...

    def delete_documents(self, document_ids: list[str]) -> None:
        ...

    def verify(self, expected: IndexManifest) -> IndexVerification:
        ...
```

DTO 至少包含：

```text
VectorRecord
- chunk_id
- document_id
- vector
- knowledge_base_id (准备字段，可允许 default)
- document_type (可选)
- section/chapter (可选)
- page_start/page_end
- embedding_model
- embedding_dimension
- embedding_version/fingerprint

VectorHit
- chunk_id
- document_id
- dense_score
- backend
```

**VectorStore 不负责保存权威 Chunk 原文。**

---

## 7.5 Qdrant Point Contract

最低 payload：

| 字段 | 要求 |
|---|---|
| `chunk_id` | 必须，keyword |
| `document_id` | 必须，keyword + filter index |
| `knowledge_base_id` | 必须或使用稳定 default，keyword + filter index |
| `document_type` | 建议 |
| `section_id` / chapter | 可选 |
| `page_start` / `page_end` | 建议 |
| `embedding_model` | 必须 |
| `embedding_dimension` | 必须 |
| `source_version` | 建议 |
| `content_hash` | 强烈建议，用于一致性检查 |

Point ID 应由稳定 `chunk_id` 确定性派生，不使用每次随机 UUID。

---

## 7.6 Qdrant 一致性模型

### 正常构建

```text
SQLite Chunk 已成功写入
→ 获取/复用 embedding
→ Upsert Qdrant
→ 验证 point
→ 更新 index manifest/status
```

### Qdrant 不可用

必须满足：

- SQLite 不损坏；
- 旧 Qdrant 不被错误清空；
- 新索引状态标记为 `INDEX_DIRTY` / equivalent；
- 用户得到明确错误；
- 服务恢复后可以重试或 rebuild。

### 重新构建

```text
SQLite
→ 枚举有效 chunks
→ 读取/重新生成 embedding
→ batch upsert
→ count + model + hash verify
→ READY
```

---

## 7.7 运行时依赖决策 Gate：QD-01

当前项目基线明确追求“运行时 Python 标准库 + 独立 Ollama”。

因此引入 Qdrant 时必须先明确以下选择之一：

### Option A — 标准库 HTTP Adapter

优点：

- 保留当前 runtime dependency policy；
- 减少打包复杂度；
- 便于 Windows 独立运行包。

缺点：

- 需要自行维护 Qdrant REST request/response contract；
- typed client 能力较少。

### Option B — `qdrant-client` 作为可选运行依赖

优点：

- 官方客户端；
- collection/filter/model API 更方便；
- 减少协议层手写代码。

缺点：

- 改变“运行时只用标准库”的现有承诺；
- 增加依赖、打包与兼容矩阵。

### Gate 要求

Agent 不能默认选择并静默加入依赖。

必须输出：

```text
选择：
原因：
对 requirements.txt 的影响：
对 build_windows.ps1 的影响：
对 CI 的影响：
对安装体验的影响：
回滚方式：
```

本阶段推荐优先考虑 **保留现有依赖策略**，除非实际实现成本/可靠性证明使用官方 client 更合适。

---

## 7.8 HybridRetriever 解耦

当前目标链：

```text
Query
 ├─ SQLite FTS5      → lexical candidates
 └─ VectorStore      → dense candidates
            │
            ▼
            RRF
            │
            ▼
 quality / heading / dedup / scope logic
            │
            ▼
        final hits
```

本阶段不要改变核心 Ranking 语义，优先做 **行为等价迁移**。

先证明：

```text
旧 LibraryStore retrieval
≈
新 HybridRetriever + sqlite-vector backend
```

再比较：

```text
sqlite-vector backend
vs
qdrant backend
```

---

## 7.9 建议配置

禁止在业务代码散落 magic values。

例如：

```text
VECTOR_BACKEND=sqlite|qdrant
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=local_knowledge_chunks
QDRANT_TIMEOUT_SECONDS=...
DENSE_CANDIDATE_K=...
LEXICAL_CANDIDATE_K=...
RRF_CANDIDATE_K=...
```

Embedding model、dimension 与 gate 由统一注册表或库元数据管理。

---

## 7.10 测试

### Contract Tests

同一组测试必须能运行在：

- SQLite vector backend；
- Qdrant backend（可用服务时）。

测试：

- empty query/vector；
- dimension mismatch；
- normal Top-K；
- deterministic point id；
- repeated upsert；
- document filter；
- knowledge base filter；
- delete document；
- missing chunk；
- unavailable backend；
- malformed response；
- model mismatch；
- index verification。

### Integration Tests

至少：

```text
SQLite seed data
→ build vector index
→ query Qdrant
→ receive chunk_id
→ SQLite回查
→ hybrid fusion
→ final SearchResult
```

### Failure Tests

- Qdrant 未启动；
- 中途 upsert 失败；
- collection 不存在；
- vector dimension 错误；
- 部分 points 缺失；
- 多余 orphan points；
- model 版本不一致；
- SQLite 数据变化而 Qdrant 未同步。

---

## 7.11 性能基线

至少测试：

- 1k chunks；
- 10k chunks；
- 条件允许时 50k chunks。

记录：

```text
FTS p50/p95
Dense p50/p95
Hybrid p50/p95
memory usage
index size
startup time
```

性能标准不预先伪造绝对数字。

核心验收是：

> 在 10k+ chunk 规模下，Qdrant Dense Retrieval 不再表现为应用侧 O(N) Python 全库逐向量扫描。

---

## 7.12 Acceptance Criteria

全部满足才 `PASS`：

- [ ] 旧 SQLite vector backend 仍可使用；
- [ ] VectorStore contract 存在；
- [ ] Hybrid Retrieval 已与 Storage 解耦；
- [ ] Qdrant backend 支持 search/upsert/delete/health；
- [ ] Qdrant point 可稳定回查 SQLite；
- [ ] `document_id` filter 通过；
- [ ] `knowledge_base_id` filter 通过或有正式过渡策略；
- [ ] model/dimension mismatch 可检测；
- [ ] index verify 可检测 missing/orphan/mismatch；
- [ ] rebuild 不修改权威 SQLite 内容；
- [ ] Qdrant 停机不会破坏 SQLite；
- [ ] 旧测试全部继续通过；
- [ ] 新增 Contract/Integration tests；
- [ ] Golden Set 核心指标不显著下降；
- [ ] 性能基线已记录；
- [ ] 默认 backend 切换经过明确验证；
- [ ] 回滚到 SQLite backend 可在不改数据的情况下完成。

---

## 7.13 Rollback

最低回滚路径：

```text
VECTOR_BACKEND=sqlite
```

并满足：

- 不需要回退 SQLite 数据；
- 不需要恢复旧 Chunk；
- Qdrant 可停止；
- 问答核心功能仍可运行；
- 任何新 schema 字段若已加入，应向后兼容或提供恢复说明。

---

# 8. Phase B — v3.1 Reranker 与检索质量升级

**状态**：`PLANNED`  
**优先级**：P0

## 8.1 Goal

将 Retrieval Pipeline 升级为：

```text
FTS5 Top-K
+
Qdrant Dense Top-K
        │
        ▼
       RRF
        │
        ▼
   candidate 16~24
        │
        ▼
     Reranker
        │
        ▼
      Top 6~8
        │
        ▼
  Context Builder / LLM
```

## 8.2 Scope

- 新增 Reranker Adapter；
- 支持本地模型；
- CPU/GPU backend 可配置；
- Reranker 可关闭；
- 记录 reranker latency；
- 对比 RRF-only baseline；
- 校准最终 context_k；
- 校准 Scope Gate 与 Reranker 的职责边界。

## 8.3 Out of Scope

- 不做 Router；
- 不做 Query Rewrite；
- 不做 Library Manager；
- 不换 Sparse Backend；
- 不允许为了 reranker 增益破坏 OOS 判定。

## 8.4 关键设计

Reranker 是 **相关性排序器**，不是业务真相判断器。

不能：

```text
低质量/离题召回
→ reranker 给出某个最高分
→ 因为“总有第一名”就强行回答
```

Scope Gate 仍必须独立。

## 8.5 模型资源风险

如果选择较大 reranker，在 8GB Laptop GPU 场景下必须评估：

- 与 7B LLM 同时驻留是否 OOM；
- CPU rerank 是否可接受；
- 按需加载；
- 模型量化；
- 较小模型 fallback。

## 8.6 Eval

至少比较：

```text
RRF-only
vs
RRF + reranker
```

指标：

- Recall@K；
- MRR；
- nDCG@K；
- Top1/Top3 document accuracy；
- compare entity coverage；
- false accept；
- false refusal；
- latency。

## 8.7 Acceptance

- [ ] Reranker 可 feature flag 关闭；
- [ ] 无 Reranker 时系统仍能运行；
- [ ] Reranker contract tests 通过；
- [ ] Golden Set 排序指标有稳定增益或至少无退化且有明确价值；
- [ ] False Accept 不恶化到门槛之外；
- [ ] 资源占用可接受；
- [ ] CPU fallback 可用或有明确替代方案；
- [ ] telemetry 可拆分 retriever/reranker latency。

## 8.8 Rollback

```text
RERANKER_ENABLED=false
```

必须直接恢复 RRF-only 行为。

---

# 9. Phase C — v3.2 通用知识导入

**状态**：`PLANNED`  
**优先级**：P1

## 9.1 Goal

把系统从：

```text
教材 PDF
```

扩展为：

```text
PDF / DOCX / PPTX / TXT / Markdown
```

并建立统一 Parser Contract。

## 9.2 核心原则

不要让每种 Parser 直接生成最终数据库记录。

应先统一成 Normalized Document Model。

## 9.3 Parser Contract

建议：

```python
class DocumentParser(Protocol):
    def can_parse(self, path: Path) -> bool:
        ...

    def parse(self, path: Path) -> ParsedDocument:
        ...
```

统一结构至少：

```text
ParsedDocument
- source_path
- source_name
- document_type
- title
- sha256
- metadata
- blocks[]

ParsedBlock
- ordinal
- block_type
- heading_level
- heading
- text
- page_or_slide
- parent_hint
- source_method
- quality_score
```

## 9.4 格式要求

### PDF

保留：

- page_no；
- embedded text / OCR source；
- quality；
- page boundary；
- 尽可能保留 heading / block 信息。

### DOCX

最低：

- Heading 层级；
- 普通段落；
- 表格文本；
- 文档顺序。

### PPTX

最低：

- slide_no；
- 标题；
- 文本框；
- 顺序；
- Notes 可后置。

### TXT

最低：

- 编码处理；
- 全文；
- 简单 heading heuristics 可选。

### Markdown

最低：

- `#` 层级；
- 正文；
- list/code block；
- 链接文本；
- section path。

## 9.5 通用结构模型

教材专用 `chapters` 不能继续成为唯一层级。

建议演进到：

```text
documents
sections
blocks/pages
chunks
summaries
```

`sections`：

```text
id
document_id
parent_id
level
heading
ordinal
page_start
page_end
path
metadata_json
```

教材的 chapter/section 是 `sections` 的一种表现。

## 9.6 Compatibility

旧教材库必须：

- 可通过 migration 读取；或
- 提供明确 rebuild；
- 不允许悄悄变成不可用。

如果选择 rebuild 而不是复杂 migration，必须在文档中明确：

```text
旧 DB schema version
新 DB schema version
重建命令
原始数据要求
备份策略
```

## 9.7 Chunking

优先：

1. heading boundary；
2. paragraph boundary；
3. list/table/code block boundary；
4. 最后才按长度切。

必须保留：

- section path；
- page/slide；
- document；
- chunk ordinal；
- quality；
- content hash。

## 9.8 Import State Machine

建议：

```text
NEW
  ↓
PARSING
  ↓
NORMALIZED
  ↓
CHUNKED
  ↓
EMBEDDING
  ↓
INDEXING
  ↓
READY
```

异常：

```text
PARSING / EMBEDDING / INDEXING
        ↓
       ERROR
```

索引不同步：

```text
READY
 ↓
INDEX_DIRTY
```

更新：

```text
READY → REIMPORTING → READY
```

删除：

```text
READY → DELETING → REMOVED
```

## 9.9 Incremental Import

必须通过 SHA/content hash 判断：

- 文件未变化：跳过；
- 文件变化：只处理受影响内容；
- Chunk 未变化：复用 embedding；
- Chunk 删除：清理 Qdrant point；
- 新 Chunk：upsert。

## 9.10 Acceptance

- [ ] 至少 PDF/DOCX/TXT/MD 通过 Parser Contract；
- [ ] PPTX 若延期必须明确 `DEFERRED`，不能声称已支持；
- [ ] 旧 PDF 回归不下降；
- [ ] section hierarchy 可用于 Citation；
- [ ] 增量导入可识别 unchanged file；
- [ ] 修改一个文档不触发全库无意义 rebuild；
- [ ] 删除文档不产生幽灵 Chunk；
- [ ] 失败可重试；
- [ ] Parser 错误不会破坏其他 READY 文档。

---

# 10. Query Scope — 从单教材到知识库

Query Scope 是知识库化的核心，不应只是 UI 过滤条件。

## 10.1 建议对象

```python
@dataclass(frozen=True)
class QueryScope:
    knowledge_base_ids: tuple[str, ...] = ()
    document_ids: tuple[str, ...] = ()
    document_types: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    section_ids: tuple[str, ...] = ()
```

## 10.2 Scope 必须贯穿

```text
UI
→ API
→ Engine
→ Router
→ FTS
→ Qdrant filter
→ Reranker candidates
→ Citation
→ Telemetry
```

不能只在最终结果阶段做过滤，否则：

- Dense 候选浪费；
- 排序失真；
- OOS 判断失真；
- 跨文档问题容易误答。

## 10.3 默认 Scope

必须定义清楚：

- 当前知识库；
- 全部知识库；
- 当前选择文档；
- 当前会话 Scope。

禁止让空 Scope 在不同模块中含义不同。

---

# 11. Phase D — v3.3 Knowledge Library Manager

**状态**：`PLANNED`  
**优先级**：P1

## 11.1 Goal

让系统真正形成“知识库生命周期”。

## 11.2 Minimum Features

### Knowledge Base

- 创建；
- 重命名；
- 删除；
- 描述；
- 统计；
- 状态。

### Documents

- 导入；
- 列表；
- 选择；
- 标签；
- 状态；
- 重试；
- 删除；
- rebuild index；
- 查看 parser/index error。

### Query Scope

- 选择知识库；
- 选择一个或多个文档；
- 清除过滤；
- 当前 Scope 明确可见。

## 11.3 UI Recommendation

```text
左侧：
- Knowledge Bases
- Documents
- Scope selector

中间：
- Conversation

右侧：
- Evidence
- Citations
- Current Scope

顶部：
- Ollama health
- Qdrant health
- Current models

开发模式：
- Retrieval telemetry
```

## 11.4 Destructive Operations

文档/知识库删除必须：

- 二次确认；
- 先 SQLite 业务状态；
- 再清理索引；
- 失败时可识别 `DELETE_DIRTY`;
- 不静默丢失其他文档。

## 11.5 Acceptance

- [ ] KB CRUD；
- [ ] 文档导入；
- [ ] 状态可见；
- [ ] 失败原因可见；
- [ ] Scope 可选择；
- [ ] 删除有确认；
- [ ] 删除/重建具有一致性测试；
- [ ] 当前问答明确显示 Scope；
- [ ] 用户不会因索引失败误以为文档 READY。

---

# 12. Phase E — v3.4 Router + Query Rewrite + Multi-turn

**状态**：`PLANNED`  
**优先级**：P1

## 12.1 Goal

从“教材关键词 Router”升级为“知识库意图 Router”。

## 12.2 原则：Rule-first + LLM fallback

高置信、结构化意图继续规则处理：

- “有哪些文档”；
- “第几页”；
- 显式文档名；
- 明确 compare；
- 明确 metadata query；
- 明确选择 Scope。

LLM Router 只负责：

- 长尾语义表达；
- 模糊意图；
- 多文档综合；
- 需要 rewrite 的追问；
- 规则无法安全判断的 query。

原因：

- 可测；
- 延迟低；
- 不依赖 LLM 才能列数据库；
- 避免 LLM 幻觉产生不存在文档/Route。

## 12.3 Route Schema

最低建议：

```json
{
  "route": "QA",
  "confidence": 0.86,
  "entities": ["OFDM"],
  "document_hints": [],
  "needs_rewrite": true,
  "reason_code": "semantic_qa"
}
```

Route 枚举建议：

```text
METADATA_QUERY
DOCUMENT_SUMMARY
GLOBAL_SUMMARY
LOCATE
COMPARE
QA
MULTI_DOCUMENT_QA
OUT_OF_SCOPE
```

教材专属 route 可以作为兼容别名或子类型，不应继续是整个系统的唯一语义。

## 12.4 Query Rewrite

目标：

```text
history + current turn
→ standalone query
```

例如：

```text
Q1: 介绍 OFDM
Q2: 它为什么要加循环前缀？

Rewrite:
OFDM 为什么需要加入循环前缀？
```

要求：

- 不添加对话中不存在的实体；
- 不擅自改变用户意图；
- 保留比较对象；
- 切换话题时不能错误继承旧实体；
- Rewrite 失败必须 fallback 到安全原 query 策略。

## 12.5 Router / Rewrite 必须单独评测

不要只看最终回答。

### Router Metrics

- route accuracy；
- confusion matrix；
- OOS precision/recall；
- metadata query accuracy。

### Rewrite Metrics

- entity retention；
- pronoun resolution accuracy；
- topic switch robustness；
- hallucinated entity rate。

## 12.6 Acceptance

- [ ] Rule-first 存在；
- [ ] LLM fallback 可关闭；
- [ ] Router 输出严格结构化；
- [ ] malformed JSON 有 fallback；
- [ ] Query Rewrite 可关闭；
- [ ] 追问 Golden Set 显著扩展；
- [ ] topic switch 不错误继承；
- [ ] Router 不直接绕过 Scope Gate；
- [ ] Metadata query 不需要 RAG 时不强行调用 RAG。

---

# 13. Phase F — v3.5 Summary、Citation 与质量闭环

**状态**：`PLANNED`  
**优先级**：P2

## 13.1 Hierarchical Summary

目标：

```text
Chunk/Block
  ↓
Section Summary
  ↓
Document Summary
  ↓
Knowledge Base / Multi-document Summary
```

Summary 必须记录：

- source IDs；
- source hashes；
- model；
- prompt/version；
- generated_at；
- invalidation dependency。

文档变化后，依赖的 summary 必须失效或重建。

## 13.2 Summary 禁止行为

禁止：

```text
机械摘要
→ LLM 换一种说法
→ 当作完整文档摘要
```

摘要应从实际 source chunks/section summaries 聚合。

## 13.3 Citation Coverage

定义：

> 回答中需要证据支持的事实性 Claim，是否有至少一个有效 Citation。

建议指标：

```text
Citation Coverage >= 90%
```

具体门槛必须在真实 Golden Set 上冻结，不应为了达标而把非事实句全部排除。

## 13.4 Citation Support / Entailment

可采用分层验证：

### Layer 1 — Deterministic

- citation id 合法；
- chunk 存在；
- document/scope 合法；
- 关键技术实体在 Evidence 中出现；
- 数字/单位可检查时进行匹配。

### Layer 2 — Optional Verifier

```text
claim + cited chunks
→ supported / unsupported / uncertain
```

Verifier 可以是：

- 本地 NLI；
- 本地 LLM judge；
- 冻结 Prompt 的 verifier。

Verifier 不能修改原 Evidence。

## 13.5 Unsupported Claim Handling

推荐：

- 对明显 unsupported claim 删除/要求重新生成；
- `uncertain` 不直接伪装为 supported；
- telemetry 记录；
- Golden Set 统计。

## 13.6 Acceptance

- [ ] Summary 有层次化依赖；
- [ ] Document Summary 来自真实 Section/Chunk；
- [ ] Multi-document Summary 可追溯；
- [ ] Citation Coverage 可计算；
- [ ] Citation support 可计算；
- [ ] 无 Citation 的事实性输出有检测；
- [ ] Citation 指向 Scope 外文档时可阻止；
- [ ] Golden Set 包含 Citation negative cases。

---

# 14. Golden Set 与评测体系

## 14.1 目标规模

V3 完成前建议至少扩展到 150～300 条，覆盖多个真实文档。

最低类别建议：

| 类别 | 建议数量 |
|---|---:|
| 单事实 QA | 40+ |
| 定位 | 20+ |
| 比较 | 20+ |
| 多轮追问 | 20+ |
| 多文档综合 | 20+ |
| OOS / hard negatives | 30+ |
| Metadata / Library | 15+ |
| Citation 验证 | 20+ |

数量可重叠，但必须有类别标签。

## 14.2 Hard Negatives

必须增加：

- 名词相似但库内没有答案；
- 仅一个字/二字残留命中；
- 文档 A 有术语但问题问的是文档 B；
- 数字相近；
- 缩写歧义；
- 旧版本知识与新版本冲突；
- “最近/今天”等明显不属于静态库的问题；
- Query 中故意混入无关技术词。

## 14.3 指标

### Retrieval

- Recall@K；
- MRR；
- nDCG@K；
- Top1/Top3 document accuracy；
- Top1/Top3 section accuracy；
- compare entity coverage。

### Scope

- False Accept Rate；
- False Refusal Rate。

### Router

- Route accuracy；
- confusion matrix。

### Rewrite

- entity preservation；
- coreference resolution；
- hallucinated entity rate。

### Answer

- correctness；
- completeness；
- refusal correctness。

### Citation

- citation validity；
- citation coverage；
- unsupported claim rate。

### Performance

- FTS latency；
- dense latency；
- rerank latency；
- LLM TTFT；
- total latency。

---

# 15. CI 分层策略

不要让每个 CI Job 都依赖本机 Ollama/Qdrant/GPU。

建议：

## Tier 1 — Always-on Unit CI

不需要外部服务：

- syntax；
- Ruff；
- unit tests；
- parser fixtures；
- vector contract mock；
- router deterministic tests；
- citation deterministic tests；
- config validation。

## Tier 2 — Service Integration

可选服务：

- Qdrant container；
- seed dataset；
- upsert/search/filter/delete；
- index verify；
- HybridRetriever integration。

可以在 GitHub Actions service container 中运行，前提是稳定。

## Tier 3 — Local Model Regression

依赖真实本地模型：

- embedding；
- reranker；
- LLM；
- full Golden Set。

不应假装普通 CI 已覆盖。

可作为：

- release gate；
- 手工 pre-release；
- 本地脚本；
- self-hosted runner（未来）。

---

# 16. 配置与模型版本合同

必须统一管理：

```text
answer_model
embedding_model
embedding_dimension
embedding_normalization
reranker_model
router_model
summary_model
citation_verifier_model
```

禁止：

- README 一个模型；
- `.env.example` 一个模型；
- `config.py` 一个模型；
- 数据库 metadata 又一个模型。

## 16.1 Embedding Gate

每个 embedding model 的阈值必须通过 eval calibration。

建议 registry：

```python
EmbeddingProfile(
    model="bge-m3",
    dimension=1024,
    normalize=True,
    dense_candidate_floor=...,
    scope_strong=...,
    scope_accept=...,
    calibration_version="...",
)
```

若运行库的 model 不在 registry：

- 不应静默使用未经验证的“看起来差不多”的阈值；
- 应提示 fallback 风险；
- 最好要求 calibration。

---

# 17. Context Budget

当前后续改进应把“字符长度预算”升级为模型更可靠的 token budget。

## 17.1 原则

```text
system prompt
+ history
+ query
+ evidence
+ answer reserve
<= context window
```

如果没有正式 tokenizer：

- 使用模型近似估算器；
- 安全 margin；
- telemetry 记录估算。

禁止只依赖 Python `len(text)` 并声称为真实 token 数。

---

# 18. Telemetry

建议事件字段：

```text
request_id
timestamp
route
route_confidence
query
rewritten_query
scope
embedding_model
vector_backend
lexical_hits
dense_hits
rrf_top_ids
reranker_scores
final_context_ids
scope_confidence
out_of_scope
citation_count
citation_coverage
embedding_ms
lexical_ms
dense_ms
rerank_ms
llm_ttft_ms
llm_total_ms
total_ms
error_code
```

隐私要求：

- 默认不写入原始版权文档全文；
- 日志不要泄露会话 token；
- 明确日志保留策略；
- 用户关闭 telemetry 时仍能问答。

---

# 19. 安全边界

V3 仍定位为本地/可信局域网应用。

继续保持：

- Host 校验；
- pairing；
- token expiration；
- CSP；
- X-Frame-Options；
- MIME protection；
- static path traversal protection；
- request body limit；
- pairing rate limit。

若未来公网访问：

> 必须另立安全阶段。

至少需要：

- TLS；
- 正式身份认证；
- CSRF/Session 安全评估；
- 更完整的访问控制；
- secret 管理；
- 审计日志；
- 公网攻击面评估。

不得把当前 LAN pairing 宣传为公网安全认证。

---

# 20. 文件级改造总表

以下是目标规划，不代表必须一次创建。

| 文件/模块 | 目标动作 | Phase |
|---|---|---|
| `core/library_store.py` | 保留 SQLite 真相源/FTS/summary；逐步移出 Dense 扫描职责 | v3.0 |
| `core/vector_store.py` | VectorStore Protocol、DTO、错误合同 | v3.0 |
| `core/sqlite_vector_store.py` | 兼容旧 brute-force backend | v3.0 |
| `core/qdrant_store.py` | Qdrant backend | v3.0 |
| `core/hybrid_retriever.py` | FTS + Dense + RRF + dedup + scope | v3.0 |
| `core/config.py` | backend/model/version 配置统一 | v3.0+ |
| `scripts/rebuild_vector_index.py` | Qdrant rebuild | v3.0 |
| `scripts/verify_vector_index.py` | SQLite/Qdrant consistency | v3.0 |
| `scripts/benchmark_retrieval.py` | retrieval/performance baseline | v3.0 |
| `core/reranker.py` | Reranker adapter | v3.1 |
| `core/parsers/base.py` | Parser Protocol | v3.2 |
| `core/parsers/pdf.py` | PDF adapter | v3.2 |
| `core/parsers/docx.py` | DOCX adapter | v3.2 |
| `core/parsers/pptx.py` | PPTX adapter | v3.2 |
| `core/parsers/text.py` | TXT adapter | v3.2 |
| `core/parsers/markdown.py` | Markdown adapter | v3.2 |
| `core/document_model.py` | Normalized Document Model | v3.2 |
| `core/import_pipeline.py` | Import state machine | v3.2 |
| `core/scope.py` | QueryScope | v3.2/v3.3 |
| `desktop/web_server.py` | Library API / status / scope API | v3.3 |
| `web/` | Library Manager | v3.3 |
| `core/router.py` | Rule-first + LLM fallback | v3.4 |
| `core/query_rewriter.py` | standalone rewrite | v3.4 |
| `core/summary.py` | hierarchical summary | v3.5 |
| `core/citation_verifier.py` | coverage/support | v3.5 |
| `scripts/eval_recall.py` | 多文档/多指标评测 | 全阶段 |
| `scripts/golden_set.json` | 扩充 Golden Set | 全阶段 |
| `docs/ARCHITECTURE.md` | 只在 Phase PASS 后更新 AS-IS | 全阶段 |
| `docs/V3_PROGRESS.md` | 阶段执行证据 | 全阶段 |

---

# 21. Backlog（可拆 GitHub Issues）

## P0

- `P0-01` 冻结 V2 基线
- `P0-02` VectorStore Protocol
- `P0-03` SQLite Vector compatibility adapter
- `P0-04` Qdrant backend
- `P0-05` Qdrant payload/filter index
- `P0-06` Vector index rebuild
- `P0-07` Vector index verify
- `P0-08` HybridRetriever 解耦
- `P0-09` Backend feature flag
- `P0-10` 双后端 regression
- `P0-11` Retrieval benchmark
- `P0-12` Embedding profile 一致性
- `P0-13` Reranker adapter
- `P0-14` Reranker offline eval

## P1

- `P1-01` Document Parser Protocol
- `P1-02` Normalized Document Model
- `P1-03` DOCX parser
- `P1-04` Markdown parser
- `P1-05` TXT parser
- `P1-06` PPTX parser
- `P1-07` sections 通用化
- `P1-08` Incremental import
- `P1-09` Knowledge Base model
- `P1-10` QueryScope
- `P1-11` Library API
- `P1-12` Library UI
- `P1-13` Rule-first Router
- `P1-14` LLM Router fallback
- `P1-15` Query Rewrite
- `P1-16` Multi-turn regression

## P2

- `P2-01` Hierarchical summaries
- `P2-02` Summary invalidation
- `P2-03` Citation coverage
- `P2-04` Citation support verifier
- `P2-05` Multi-document Golden Set
- `P2-06` Answer quality eval
- `P2-07` performance dashboard/telemetry analysis
- `P2-08` release quality gate

---

# 22. 主要风险与回滚

| 风险 | 影响 | 缓解 | 回滚 |
|---|---|---|---|
| Qdrant 引入增加部署复杂度 | 启动失败 | health check / bootstrap / clear error | `VECTOR_BACKEND=sqlite` |
| Qdrant 与 SQLite 不一致 | 错误检索 | verify/rebuild/content hash | rebuild index |
| 新 backend 检索退化 | 回答质量下降 | 双后端 Golden Set | 切回 sqlite backend |
| Reranker 占显存 | OOM | CPU/小模型/按需加载 | disable reranker |
| Schema 通用化破坏旧库 | 数据不可读 | backup + schema gate + rebuild | 旧程序/旧 DB |
| Parser 质量不一 | 坏 Chunk | contract + quality score | disable parser type |
| Query Rewrite 幻觉 | 意图改变 | strict JSON + fallback | disable rewrite |
| LLM Router 不稳定 | 错路由 | rule-first + confidence | rule-only |
| Summary 陈旧 | 全局回答错误 | dependency hash invalidation | rebuild summary |
| Citation verifier 误杀 | 回答被过度删减 | uncertain state + offline eval | deterministic-only |
| UI 删除操作误删 | 数据损失 | confirm + transactional state | restore backup |
| 过度并行开发 | 难以定位回归 | phase gate | rollback current phase |

---

# 23. V3 完成定义（Definition of Done）

项目只有满足以下条件，才适合正式称为“通用本地知识库问答系统 V3”。

## 23.1 Knowledge Lifecycle

- [ ] 可创建知识库；
- [ ] 可导入多种文档；
- [ ] 可看到导入/索引状态；
- [ ] 可删除/更新；
- [ ] 可重建索引；
- [ ] 可选择 Query Scope。

## 23.2 Retrieval

- [ ] FTS5 lexical；
- [ ] Qdrant Dense ANN；
- [ ] RRF；
- [ ] Reranker；
- [ ] document/KB filters；
- [ ] OOS gate；
- [ ] 可回滚 backend。

## 23.3 Multi-document

- [ ] 单文档 QA；
- [ ] 跨文档 QA；
- [ ] 比较；
- [ ] 定位；
- [ ] 文档 Summary；
- [ ] Knowledge Base Summary。

## 23.4 Conversation

- [ ] Route 可测试；
- [ ] Rule-first；
- [ ] LLM fallback；
- [ ] standalone query rewrite；
- [ ] topic switch regression。

## 23.5 Evidence

- [ ] page/section/document citation；
- [ ] citation validity；
- [ ] coverage；
- [ ] support verification；
- [ ] Scope 外 Citation 阻止。

## 23.6 Engineering

- [ ] 单元 CI；
- [ ] Qdrant integration；
- [ ] multi-document Golden Set；
- [ ] performance baseline；
- [ ] telemetry；
- [ ] failure/recovery tests；
- [ ] docs 与真实代码一致。

---

# 24. 明确不建议的路线

## 24.1 不建议退化成教程式 RAG

禁止把项目简化为：

```text
PDF
→ Chunk
→ Vector DB
→ Top-K
→ LLM
```

这会丢失当前已经有价值的：

- 页码；
- 章节；
- FTS；
- structured metadata；
- RRF；
- scope gate；
- citation；
- quality；
- telemetry；
- regression；
- security。

## 24.2 不建议一次性全部迁移到 Qdrant

v3.0 不迁移 Sparse/FTS。

原因：

- 同时替换 lexical + dense，回归原因难定位；
- 当前 FTS 已有较多中文优化；
- 先替换最明显的扩展瓶颈更安全。

## 24.3 不建议全 LLM Router

数据库元数据查询、显式章节/页码、列文档等不应依赖 LLM。

## 24.4 不建议过早引入分布式复杂度

暂不需要：

- Kubernetes；
- 多节点 Qdrant；
- SaaS multi-tenant；
- cloud auth；
- 微服务拆分。

---

# 25. 推荐 Agent 首次审计 Prompt

将本文档放到 `docs/V3_IMPROVEMENT_PLAN.md` 后，首次不要授权编码。

可直接发送：

```text
请对当前 local-database-qa-system 项目进行 V3 架构升级前的完整只读审计。

权威规则：
1. 当前 main 分支代码和测试是 AS-IS 事实的最高权威。
2. docs/ARCHITECTURE.md 描述当前已实现架构。
3. docs/V3_IMPROVEMENT_PLAN.md 是 TO-BE 实施规范，不代表全部已经实现。
4. 如文档与代码冲突，以代码事实为准并报告冲突。

本轮禁止修改任何文件。

请：
- 读取 README、ARCHITECTURE、V3_IMPROVEMENT_PLAN；
- 审计 core/scripts/desktop/web/tests/CI/requirements/config；
- 冻结当前测试、retrieval、performance、embedding/schema 基线；
- 逐项制作 V3 Gap Matrix；
- 核对 Phase A(v3.0) 的文件级设计是否适合当前代码；
- 特别评估当前“运行时只用 Python 标准库”的约束与 Qdrant 接入方式；
- 不允许提前实施 Qdrant、Reranker 或其他 V3 功能。

最终输出：
A. 当前基线
B. Gap Matrix
C. Phase A 修订版文件级方案
D. 测试与性能基线
E. 风险/阻塞
F. 本轮未修改任何文件的确认

完成后停止，等待授权。
```

---

# 26. Phase A 授权 Prompt 模板

Phase 0 审计通过后：

```text
现在只授权实施 docs/V3_IMPROVEMENT_PLAN.md 中的 Phase A / v3.0。

禁止提前实现 Phase B 及以后功能。

执行前先确认：
- 当前 HEAD
- 工作树
- baseline tests
- baseline retrieval
- rollback point
- QD-01 依赖决策

核心合同：
- SQLite 继续是 Source of Truth；
- Qdrant 只是可重建 Dense Index；
- 保留旧 sqlite vector backend；
- FTS5 不迁移；
- 当前 RRF/Scope 语义先保持行为等价；
- Qdrant point 必须稳定回查 SQLite；
- 必须有 index verify/rebuild；
- Qdrant 失败不得损坏 SQLite；
- 不删除或弱化现有测试；
- 不做 UI/Router/Reranker/Parser 等范围外工作。

只有所有 Phase A Acceptance Criteria 满足，才能标记 PASS。

完成后按本文档第 4.3 节格式报告并停止。
```

---

# 27. `V3_PROGRESS.md` 建议记录格式

本文档本身只记录计划，不频繁把执行日志写进本文件。

建议创建：

```markdown
# V3 Progress

## Baseline
- branch:
- commit:
- date:
- tests:
- golden:
- embedding:
- schema:
- chunks:

## Phase 0
Status:
Evidence:
Risks:
Decision:

## Phase A — v3.0
Status:
Authorized commit:
Branch:
Changes:
Tests:
Regression:
Performance:
Known issues:
Rollback:
Gate decision:

## Phase B — v3.1
...
```

每个 Phase 的 `PASS` 必须有可复核证据，而不是只写“已完成”。

---

# 28. 最终项目定位

V3 完整达到 DoD 后，推荐项目名称：

> **基于 Hybrid RAG 的本地知识库问答系统**  
> **Local Knowledge Base QA System**

推荐技术描述：

> 设计本地优先的多文档知识库问答系统，以 SQLite 作为结构化知识 Source of Truth，使用 FTS5 与 Qdrant Dense ANN 实现可过滤的 Hybrid Retrieval，经 RRF 与本地 Reranker 二阶段排序后构造证据上下文；支持多格式文档增量导入、知识库 Scope、多轮 Query Rewrite、结构化路由、层次摘要、页码级 Citation 与证据一致性校验，并通过 Golden Set、回归测试、性能基准和 CI 建立可量化质量闭环。

在对应功能尚未真正完成前，禁止提前使用上述完整表述。

---

# 29. 当前推荐的唯一下一步

**不要直接开始改代码。**

下一步顺序固定为：

```text
1. 将本文档保存到：
   docs/V3_IMPROVEMENT_PLAN.md

2. 将人类阅读版放到：
   docs/reference/本地知识库问答系统_v3_详细改进方案.docx

3. 让 Agent 执行 Phase 0 只读审计

4. 审计报告通过后

5. 用户明确授权 Phase A / v3.0

6. v3.0 PASS 后再讨论 v3.1
```

---

## 附录 A — 一句话架构原则

> **保留 V2 已验证的 Evidence-first、SQLite/FTS、页码 Citation、Scope Gate、测试和安全资产；先将 Dense Retrieval 专业化并解耦，再逐步扩展多文档生命周期、Reranker、Router、Rewrite、Summary 与 Citation 质量闭环。**

## 附录 B — Agent 停止条件

出现以下任一情况，Agent 应停止扩大修改：

- 当前工作树存在未知用户改动；
- 计划与实际代码发生结构性冲突；
- 需要跨越未授权 Phase；
- 需要删除现有稳定兼容路径；
- Schema migration 无安全回滚；
- Qdrant 同步可能损坏 SQLite；
- 测试下降且原因不明确；
- Golden Set 显著退化；
- 新依赖改变部署合同但未明确批准；
- 需要公开网络暴露服务；
- 需要删除用户数据；
- 需要修改未授权的安全机制。

停止时输出：

```text
BLOCKED
原因：
影响：
当前已完成：
未修改/未继续修改的范围：
最小解决方案：
是否需要新的用户授权：
```

---

**END OF V3 IMPLEMENTATION SPEC**
