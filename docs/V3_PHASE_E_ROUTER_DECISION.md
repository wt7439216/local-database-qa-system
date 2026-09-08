# V3 Phase E Router Decision Record（v3.4）

> Phase E — Router / Query Rewrite / Follow-up Resolution 架构决策记录。
> 状态：v3.4 已实现，纯确定性实现，无 LLM 组件。

## 1. 决策：单一确定性 Routing Pipeline（无 LLM）

Phase E 实现为 **rules-first 的确定性管线**，全部集中在 `core/query_router.py`：

```text
raw question + normalized history + scope context
    → follow-up / pronoun / ellipsis resolution（确定性）
    → minimal semantic rewrite（禁止虚构事实）
    → rule-first intent classification
    → RouteDecision
```

**不使用 LLM Router**。依据（授权合同 §23–§26 允许而非要求 LLM-assisted）：

- 授权合同的核心验收是「明确问题 → deterministic fast path」；LLM 分类器只对长尾歧义有帮助，而歧义的处理原则是「宁可不猜」（§33），一个会猜的 LLM 反而有害；
- 实测确定性管线在 108 条 Golden Set 上 route accuracy 100%、follow-up 100%、ambiguous false-resolution 0%，无需 LLM 即可全部达标；
- 零延迟成本（约 16 µs/decision）与零外部依赖（LLM 不可达时无 fallback 问题）。

规则/LLM 边界：**当前无 LLM 层**。若未来引入 LLM-assisted 分类，边界固定在「仅 ambiguous cases → 二级分类器」，且必须满足 timeout + typed failure + deterministic fallback（§23–§25 合同保留）。

## 2. 数据合同

```python
@dataclass(frozen=True)
class RouteDecision:
    route: str                 # qa | compare | locate | locate_chapter | book_toc
                               # | book_overview | chapter_overview | unsupported
    confidence: str            # high | medium | low（路由置信，非检索置信）
    reason_code: str           # 如 BOOK_TOC_PATTERN、COMPARE_PATTERN、
                               #    CHAPTER_REFERENCE+FOLLOWUP_CHAPTER
    original_question: str     # 永远保留，可审计
    normalized_question: str   # 检索用（rewrite 后）
    resolution_status: str     # none | resolved | ambiguous | topic_shift
    referent: str              # 解析出的指代对象
    follow_up: bool
    scope_conflict: bool       # 问题点名了范围外文档（只报告，绝不扩 scope）
```

- `ambiguous` 保持原问题，engine 输出澄清提示（不检索、不猜）；
- `unsupported`（问候/无内容输入）输出固定引导语，不检索；
- `scope_conflict` 时 engine 输出「当前查询范围不包含你提到的文档」提示（§8 安全不变量）。

## 3. 追问解析（E3）规则顺序

1. 裸章节追问（`那第二章呢` → `第2章主要讲了什么`）；
2. `和前面的相比` → 用最近两轮话题构造 compare；
3. `前者/后者` → 上一轮 compare 两侧；
4. `它们有什么区别` → 上一轮 compare 两侧（无两侧 → AMBIGUOUS）；
5. 序数指代（`第二个`）→ 上一轮回答的编号列表/「第X个」短语；定位失败时
   `个` → AMBIGUOUS，内容型单位（`第二层`）→ 冻结兼容的旧合并行为；
6. 代词（`它/这个/那个/其`）：compare 之后的「它」= AMBIGUOUS（无唯一所指）；
   章节话题的裸「它」→ 同章模板；book 话题 → 「本书」；其余 → salient referent；
7. 无主语延续（`然后呢`）：章节话题 → 下一章模板；否则 salient referent；
8. 方面追问（`那缺点呢`、`刚才说的技术有什么缺点`）→ `referent有什么缺点`，
   仅当剩余部分完全由「载体名词 + 方面词 + 胶水词」构成（`调制方式` 这类
   自含复合术语不会被误拆）；
9. 追问标记但自带内容（`那TCP和UDP有什么区别`）→ topic_shift，不继承旧话题。

Referent 提取（`salient_topic`）优先级：结构化 `referent` 字段（history_entry
往返）> 结构化 compare_entities > 拉丁实体（OFDM/GSM…）> 中文脚手架剥离。
问候语、单字噪声词（讲/说/看…）不会成为 referent；`帧`、`码` 等真实术语单字保留。

## 4. 结构化 history（最小扩展）

客户端 history 项仍是 `{question, answer}` 必填；engine 在 `final` 结果中新增
`history_entry`（route / chapter / document_ids / compare_entities / referent），
前端整体往返存储。旧客户端不回传时 router 自动退化为纯文本解析。
`normalize_history` 的 `{question, answer}` 输出合同与 3 轮上限保持字节级冻结
（tests 锁定）。`sanitize_history` 白名单透传上述字段，类型不符即丢弃。

## 5. 安全不变量（实现保证）

- **QueryScope 零改动**：router 不持有、不修改 scope；scope 解析仍由
  `library.resolve_scope` 执行，检索 pushdown 与 citation 门卫照旧；
- **scope before rewrite == scope after rewrite**：rewrite 只改问题文本；
- **§8 Doc B 案例**：问题点名范围外文档 → `scope_conflict=true` → 范围提示，
  绝不静默读取；改写即使提到范围外文档，检索层 scope 门限仍拦截（eval 实测
  leakage=0）；
- **citation contract 不削弱**：`CitationScopeViolationError` 与
  `citation_support_verified` 路径未动；ambiguous/unsupported/scope_conflict
  三条新路径均不产生 citations（citation_verified=true，无引用可越界）；
- **telemetry**：新增 `route_reason` / `resolution_status` /
  `rewritten_question`（加性字段，无路径、无 token）。

## 6. 行为变化登记

| 变化 | 之前 | 现在 | 依据 |
|---|---|---|---|
| `那第二章呢` | qa（naive 合并检索） | chapter_overview（`第2章主要讲了什么`） | §4/§12 |
| `它有什么优点` | qa（naive 合并检索） | qa（`OFDM有什么优点` 确定性改写） | §14 |
| `有哪些章节`（无「本书」） | qa | book_toc | §12 明确模式 |
| `帮我找一下…的地方` | qa | locate（LOCATION_WORDS 扩展「找一下/找到」） | §4 |
| `哪几章讲了X` | qa | locate_chapter | §4 定位语义 |
| 问候/无内容输入 | qa 检索 → 拒答 | unsupported 固定引导语 | §11（如确有必要） |
| 明确指代的 ambiguity | 无法区分 | AMBIGUOUS → 澄清提示 | §33 |
| 提到范围外文档 | 泛化 out_of_scope | 明确范围提示（scope_conflict） | §8 |

**冻结保留**：`第二层` 无列表可对应时的旧合并行为（既有测试合同）；
classify_route 全部既有映射；naive 合并被确定性解析替换但合并文本仍作为
序数兜底存在。

## 7. 评测合同

- Golden Set：`eval/phase_e_router_golden.json`，108 cases / 12 类
  （direct/compare/book/chapter/locate/pronoun/follow_up/ellipsis/topic_shift/
  ambiguous/scope_sensitive/adversarial），含中文真实问法；
- `scripts/eval_phase_e_router.py`：离线确定性（无 LLM/无外部服务），
  含 engine 级 scope leakage 检查（真实临时 v5 库 + fake embedder）；
- 阈值（授权合同 §35/§48）：route ≥95%、follow-up ≥90%、
  ambiguous false-resolution ≤2%、scope leakage = 0；
- 实测（2026-09-08）：route 108/108=100%、follow-up 66/66=100%、
  ambiguous false-resolution 0/8、scope conflict 10/10、leakage 0。

## 8. 遗留限制

- 纯文本 history（旧客户端）下链式代词追问退化：Q2=「它有什么优点」、
  Q3=「那缺点呢」时 referent 依赖 history_entry 往返；文本降级路径会
  AMBIGUOUS（宁可澄清）；
- 「前面讲的」类指代只看文本位置，不做深层语义对齐；
- 文档级元问题（小节数/标题/幻灯片数/列目录，`docs/deferred_meta_queries.json`
  4 条）仍 DEFERRED：需要文档级元数据查询路径，超出本轮 route 枚举
  （qa/compare/locate/locate_chapter/book_toc/book_overview/chapter_overview）；
- LLM-assisted routing 未启用（见 §1 边界）。

## 9. 回滚

- 源码：`..\_phase_backups\kb-v3-phase-e-pre\`（121 文件 + SHA256SUMS.txt）；
- 行为：删除 `core/query_router.py` 并恢复 engine_v2/web_server/app.js 即可回到
  Phase D.1.1 行为；数据库零改动（无 schema/数据迁移）。
