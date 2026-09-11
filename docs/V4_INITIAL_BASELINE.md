# V4 Initial Baseline（继承锚点）

> 本文记录 KB-V4 的**唯一起点锚点与继承 provenance**。它是 V3→V4 冻结事实的 V4 侧单一来源。
> 它**不**描述 V4 的开发进展（那是 `docs/V4_MASTER_REQUIREMENTS_AND_ROADMAP.md`）。

## 1. V3 provenance（Git fact，唯一权威）

```text
V3 tag              = v3-final   (annotated tag object d3c9d37f3665ee5fe4f38112ef38604c49dc10e3)
V3 final commit     = 117ebfa044ee3905322b3f7a932defd8a373ec66
GitHub              = https://github.com/wt7439216/local-database-qa-system (branch main)
publish workspace   = Local Database Q&A System上传版
```

`docs/V3_FINAL_BASELINE.md` 内记录的 `b6164115ff72b0187fe2d6deaf6b3a35011deecf`
属于 **commit-SHA backfill chain**（`e7d5d9b → b616411 → 117ebfa`，每笔 docs 提交只能回填父提交 SHA）。
它是历史文档语义，**不改变**上述 Git fact（Git tag/commit 优先于 prose 文档）。

## 2. V4 继承事实

```text
V4_INITIAL_BASELINE = COPY_OF_V3_FINAL_BASELINE = 117ebfa044ee3905322b3f7a932defd8a373ec66
```

- V4.0 已用 relative-path + SHA256 全量比对确认：V3 与 V4 内部内容 **byte-exact 一致**
  （全量 28155 文件一致；source-level 19568 文件一致；0 added / 0 removed / 0 modified；无 junction）。
- V4 初始基线是**继承**，不是新的 Git commit。

## 3. no-git 工作区模型

```text
V3  无 .git    → 正常（冻结历史基线）
V4  无 .git    → 正常（active development workspace）
Publish 有 .git → Git publication workspace
```

- **禁止** 在 V4 执行 `git init`；不得因 `.git` 缺失判定环境异常。
- 双工作区发布流程（V4 → 校验 → sync → diff gate → commit → push → CI）保持不变；V4.2 不触发该流程。

## 4. V4.2 对继承基线的影响（measurement only）

V4.2 只建立测量基线，**未改变**：
- production behaviour（`core/desktop/web` 源码未改；由 production_source_hash 锁定）
- Golden case semantics（仅修正 meta 计数，见 `docs/V4_EVALUATION_INTEGRITY.md`）
- Contract Target 阈值

## 5. Baseline Lineage 与不可变规则（V4.4.1 确立）

```text
Historical stage baselines are IMMUTABLE.
A later remediation creates a NEW baseline artifact.
It never rewrites an earlier stage baseline.
```

因此**不再**存在 "rolling baseline" 覆盖语义：

| baseline_id | stage | role | artifact | production_source_hash | status |
|---|---|---|---|---|---|
| `V4_INITIAL_BASELINE` | V4.2 | 任何 V4 remediation 之前的初始状态 | `eval/v4_initial_baseline.json` | `ceb4e124…` | **IMMUTABLE_HISTORICAL** |
| `V4_4_SCOPE_REMEDIATION_BASELINE` | V4.4 | POST_V4_4_SCOPE_REMEDIATION | `eval/v4_4_scope_remediation_baseline.json` | `dc35c6eb…` | CURRENT_PRODUCT_STATE |

- **current pointer 与历史 artifact 分离**：当前指针只存在于
  `eval/v4_baseline_lineage.json → current_baseline_id`，**不得**通过覆盖 `eval/v4_initial_baseline.json` 表达。
- 后续 V4.5/V4.6/… 必须**追加**新 baseline artifact（使用
  `python scripts/eval_v4_baseline.py --out eval/<stage>_baseline.json --baseline-id … --baseline-role … --production-changed`），
  而不是覆盖旧 baseline。
- V4.4 曾发生的覆盖事故与恢复过程记录于
  `eval/v4_baseline_lineage.json → clobbered_in_v4_4`（含恢复来源 SHA256）。

## 6. 机器可读锚点

```text
production provenance = eval/v4_initial_baseline.json → production_provenance
baseline lineage      = eval/v4_baseline_lineage.json
```
