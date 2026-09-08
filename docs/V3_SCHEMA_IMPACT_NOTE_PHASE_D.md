# Phase D Schema Impact Note（v3.3 / KB-V3）

> 状态：`ACCEPTED_FOR_IMPLEMENTATION`（按 Phase D 授权合同 §4 输出；首次 schema 修改前的决策记录，随最终报告一并保留）
> 日期：2026-09-08
> 结论：**引入 schema v5（加性迁移）用于受管库 `documents.sqlite3`；教材库 `textbooks.sqlite3` 保持 v4 legacy 不迁移**。`SCHEMA_VERSION = 4` 常量含义收窄为"v4 核心 读 schema"，新增 `MANAGED_SCHEMA_VERSION = 5`。

---

## 1. 为什么 v4 不足（逐项真实消费需求）

| 需求 | v4 现状 | 真实消费者 | 为什么 v4 不够 |
|---|---|---|---|
| knowledge_base_id | 仅过渡值 `"default"`（`vector_store.DEFAULT_KNOWLEDGE_BASE_ID` 注释即声明是过渡值） | QueryScope 解析、Qdrant payload filter、Library Manager 列表 | 无 knowledge_bases 表，无法创建/列出/统计 KB；身份无法稳定持久化 |
| stable document identity | `document_id = sha256(canonical source path)`，仅存在于 documents.id | Library Manager 增删改查、relink、Citation | rename/move → 新身份（Phase C closure 已登记设计债）；重命名文件后旧 document 行成为孤儿 |
| mutable source_path | documents.source_name 仅存文件名；完整路径完全不持久化 | Relink、re-import、重复内容提示 | 无法判断"同一文档移动了位置"，也无法在导入时识别"此路径已有文档" |
| persistent lifecycle status | 只存在于 ImportResult DTO（进程内），落库后丢失 | Library Manager 状态列、DELETE_FAILED/FAILED_INDEX 的可见性与重试 | 删除中断/索引失败后用户无法看到真相；重试没有依据 |
| enable/disable | 无 | QueryScope 默认范围（READY+enabled）、Disable E2E | 无法在不删除数据的情况下临时排除文档 |
| tags | 无 | document_tags 关系查询、tag scope、Qdrant payload | 需要可查询的关系表（合同禁止只存 JSON 字符串） |
| timestamps / last_error | 无 | UI 更新时间、失败原因可见 | 无法展示"哪些文档失败、为什么" |

结论：以上都是 LibraryService / QueryScope 的**运行时读需求**，不是装饰性字段；v4 无法承载。

## 2. 拟新增（表 / 列 / 索引）

v5 全部为**加性**变更——v4 的 7 张表（metadata/documents/pages/chapters/chunks/chunk_fts/embeddings/summaries）DDL 一个字节都不改：

```sql
CREATE TABLE knowledge_bases (
    knowledge_base_id TEXT PRIMARY KEY,      -- 'kb-<stable-id>'
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,                -- UTC ISO
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE document_sources (              -- 文档生命周期注册表
    document_id TEXT PRIMARY KEY REFERENCES documents(id),
    knowledge_base_id TEXT NOT NULL REFERENCES knowledge_bases(knowledge_base_id),
    source_path TEXT NOT NULL DEFAULT '',    -- 可变属性；迁移遗留值可能仅为文件名
    source_type TEXT NOT NULL DEFAULT '',    -- md/txt/docx/pptx/pdf
    document_type TEXT NOT NULL DEFAULT '',  -- scope 用分类；默认取 source_type
    source_hash TEXT NOT NULL DEFAULT '',    -- 与 documents.sha256 保持同步
    status TEXT NOT NULL DEFAULT 'READY',    -- IMPORTING/READY/UPDATING/FAILED/FAILED_INDEX/DELETING/DELETE_FAILED
    enabled INTEGER NOT NULL DEFAULT 1,      -- soft disable；DISABLED 用 enabled=0 表达
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_error TEXT NOT NULL DEFAULT ''
);
CREATE TABLE tags (
    tag_id TEXT PRIMARY KEY,                 -- 'tag-<uuid4hex>'
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE document_tags (
    document_id TEXT NOT NULL REFERENCES documents(id),
    tag_id TEXT NOT NULL REFERENCES tags(tag_id),
    PRIMARY KEY (document_id, tag_id)
);
CREATE INDEX idx_document_sources_kb ON document_sources(knowledge_base_id);
CREATE INDEX idx_document_tags_tag ON document_tags(tag_id);
```

metadata：`schema_version` → `5`。

DISABLED 不作为独立 status：合同 §9 允许简化，但必须覆盖 disable 语义——`enabled=0` 与 status 正交，删除失败（DELETE_FAILED）与手工停用（enabled=0）可以同时表达，不互相覆盖。

`sections` 全量表：**继续推迟**（Phase C Schema Decision 维持）。理由：无运行时消费者（section_ids scope 本阶段 DEFERRED，见 §8/合同 §20），且为它迁移 617-chunk 教材库无收益。

## 3. Migration（v4 → v5）

- 单事务：`integrity_check`（before）→ `BEGIN` → 建 4 表 2 索引 → 插入 Default KB（`kb-default` / "Default Knowledge Base"，created/updated=迁移时刻）→ 为每个 documents 行插入 document_sources（status=READY、enabled=1、knowledge_base_id='kb-default'、source_type/document_type 取自 `import_source_type_<docid>` metadata、缺失则空串；source_path 取 source_name——Phase C 未持久化完整路径，best-effort 登记文件名，可通过 relink 修复）→ `schema_version=5` → 行数核对（documents/chunks/embeddings before==after）→ `integrity_check`（after）→ `COMMIT`。
- 幂等：v5 库重复执行为 no-op；空库（无 metadata 表）直接按 v5 全新建库。
- 实现位置：`core/library_service.py::ensure_managed_schema`（LibraryService 打开受管库时自动确保，显式报错优先于静默改版本）。
- CLI 入口：`scripts/migrate_library.py --library <path>`（含自动备份 + 失败恢复）。

## 4. Legacy compatibility（textbooks.sqlite3，617 chunks）

- **不迁移**。教材库继续 v4 legacy，继续由既有 build/rebuild 管线服务；Library Manager 本阶段不管理它（合同 §30 允许方案）。
- `LibraryStore` 版本检查放宽为 `version in {4, 5}`：v5 对 v4 是纯加性，v4 读路径（documents/chunks/FTS/embeddings/summaries/chapters）在 v5 库上全部有效；v4 库继续按原语义工作。Golden Set / regression 行为零变化。
- 明确登记：**current managed scope = documents.sqlite3（v5）；legacy scope = textbooks.sqlite3（v4）**。Phase E 统一路径：v5 document_sources 增加教材行 +kb 归属，Router 以 KB 为路由单位（不在本阶段做，不得宣称已统一）。

## 5. General documents migration（documents.sqlite3）

- 迁移前自动 byte copy 至 `data/library/documents.sqlite3.pre-v5.bak`（migrate_library.py 执行；测试内用临时目录验证）。
- 5 documents / 20 chunks / 20 embeddings 全部保留；document_id **原样保留**（即 Phase C 的 path-hash ID，成为迁移后的稳定 ID——合同 §6"不要为了 ID 更漂亮重写已有 document_id"）。
- 迁移后 VectorIndex 同步（仅 `VECTOR_BACKEND=qdrant` 时）：对 general_documents collection 逐文档 re-upsert（确定性 point ID 幂等覆盖），payload 增补 `document_type`/`tags` 并把 `knowledge_base_id` 从过渡值 `default` 改为 `kb-default`；`verify` 以 SQLite manifest 收敛校验。

## 6. Rollback

- 文件级：迁移失败（任何一步异常/行数不符/integrity_check 失败）→ 事务 ROLLBACK + 从 .bak 恢复字节副本，库保持 v4 原状。
- 源码级：恢复 `_phase_backups/kb-v3-phase-d-pre/`（SHA256 清单校验）。
- v5 → v4 无需降级路径：v5 是加性的，v4 代码可以直接读 v5 库（忽略新表）；唯一不可逆风险是"删除文档"这类业务操作，与本迁移无关。

## 7. Qdrant payload 同步

- `VectorRecord` 新增 `document_type: str = ""`、`tags: tuple[str, ...] = ()`；`_payload_of` 写入（空值不写，legacy 行为字节不变）；`VectorScope` 新增 `document_types`、`tags`；Qdrant filter 增加对应 must 子句；`PAYLOAD_INDEX_FIELDS` 增加 `document_type`、`tags`（keyword / keyword 数组）。
- 受管库导入（LibraryService 路径）在 upsert 时携带新 payload；迁移存量按 §5 re-upsert 同步。
- 教材 collection 不动：其 scope 解析走 SQLite 兜底（v4 库无 document_sources → 全部 READY 文档），dense filter 只有 document_ids/knowledge_base_ids，不引用缺失字段。
- tags/KB/type 的 SQLite 端变更由 LibraryService 触发同库 re-upsert 同步，避免 payload 漂移；`tests/test_library_service.py` 断言 payload 一致性。

## 8. Tests（migration fixtures / old database fixtures）

- `tests/test_schema_migration.py`：v4 fixture（含 documents/chunks/FTS/embeddings/summaries 行）→ 迁移 → 断言 4 新表、Default KB、逐文档 sources 行、行数不变、integrity ok、幂等二次迁移 no-op、空库直接建 v5、失败注入（迁移中 raise → 库内容回滚不变）。
- `tests/test_library_service.py`：KB CRUD / 稳定身份 / relink（hash 相同与不同）/ enable/disable / delete 全链路 / delete 失败注入（Qdrant 不可达、HTTP 500、malformed、部分残留）/ retry-index / tags / duplicate candidate 提示 / library_log 遥测隔离。
- Scope 链路：`tests/test_query_scope.py`（contract + 解析语义）+ `tests/test_scope_propagation.py`（FTS SQL pushdown、SQLiteVectorStore/QdrantVectorStore VectorScope 新字段、双后端一致性、isolation ALPHA_ONLY/BETA_ONLY 泄漏测试）。
- 真实 Qdrant：delete E2E / disable E2E / relink E2E 进 `tests/test_library_qdrant_e2e.py`（复用 skipUnless 模式，隔离 collection）。
- 既有 212 测试不删改弱化；受 `_fts_search`/`LibraryStore` 版本检查影响的模块按现有语义回归。

## 性能记录义务（合同 §17）

scope eval 中记录 scoped FTS（join 子查询）与非 scoped FTS 的 p50 耗时对比，写入最终报告。
