# 单仓库收敛记录（P5, 2026-11-09）

## 结论

`Local Database Q&A System v4.1/` 是**唯一的开发仓库、唯一的 git 仓库、唯一的发布源**。原「上传版」目录已从工作区移除。

## 迁移了什么

| 资产 | 迁移前 | 迁移后 |
|---|---|---|
| git 历史（36 commits / 4 tags / `main` = `origin/main` = `69f62c5`） | 上传版 `.git` | 本仓库 `.git`，并新增 2 个 P5 提交（共 38） |
| 可移植历史备份 | 无 | `Archive/20261109_p5_convergence/git_history.bundle`（`git bundle --all`，12.5 MB） |
| 上传版完整副本（含 `.git`，1185 文件） | 工作区兄弟目录 | `Archive/20261109_p5_convergence/upload_snapshot/` |
| 原上传版文件快照（无 `.git`） | 同上 | `Archive/20261109_p5_convergence/upload_retired/` + `RETIRED.md` |
| `PUBLICATION_EVIDENCE.json`、V3/V4 阶段文档、46 个 eval 证据、冻结治理测试与 fixtures | 上传版 | 上述两个归档副本 + git 历史（可用 `git show v4.0.0-alpha.3:<path>` 找回） |
| `publication_*` 双副本同步机制 | 活跃脚本 | `Archive/20261109_p5_convergence/files/`（14 个文件，附 `RESTORE.ps1`） |

## 为什么

`scripts/publication_sync.py` 把 `.github` 永久划归「上传版所有」，并要求同步目标存在 `.git`，导致 CI、冻结治理测试与发布证据永远无法同步收敛。P0 的历史解锁只解除了源码哈希冻结，双副本制度仍在。P5 把它整体退役，改为标准单仓库流程：

```
开发 → git commit → git tag → GitHub Actions (CI) → GitHub Release asset
```

## 发布流程（现在）

1. `make check`（或 `powershell -File scripts/check.ps1`）全绿。
2. `python -X utf8 scripts/build.py --plan` 确认构建计划，`make build` 产出 `dist/` 候选。
3. `python -X utf8 scripts/activate_candidate.py --bundle-root <dir> --apply` 生成候选指针。
4. `git tag -a v4.x.x -m "..."` + `git push origin main --tags`；在 GitHub Release 附上构建产物。
5. 历史阶段证据若需查阅，用归档副本或 `git show`；不要再创建第二份源码目录。

## 回滚

- 归档脚本：`Archive/20261109_p5_convergence/RESTORE.ps1`（恢复 14 个退役脚本）；`Archive/20261107_refactor_unbind/RESTORE.ps1`（恢复 142 个历史绑定资产）。
- git 历史：`git clone Archive/20261109_p5_convergence/git_history.bundle <dir>` 可还原全部 refs。
- 原目录：`upload_retired/` 可直接移回工作区；`upload_snapshot/` 含完整 `.git`，移回后即为原仓库。
- 旧基线 `Archive/20261107_refactor_unbind/BASELINE_FILES.json` 中记录的原上传版路径已失效，属历史证据，保留原样不改写。

## 验证

`Archive/20261109_p5_convergence/CONVERGENCE_REPORT.json` 记录迁移前后的 HEAD、commit 数、tag 列表、bundle SHA256 与最终 `git status --porcelain = ""`。

## 首次发布（2026-11-09）

| 项 | 结果 |
|---|---|
| 代码推送 | `git push origin main`：`69f62c5..2deede7`，远端与本地一致（`ahead=0`） |
| 里程碑 tag | `refactor-p0-p5-20261109`（描述性标签，不虚构版本号） |
| GitHub Release | 同 tag 的 **pre-release**，附 `LocalDatabaseQA-4.0.0-alpha.3-20261109.zip`（142,982,305 字节 / 264 文件，SHA256 `9cb3d170…`） |
| Windows 候选 | `scripts/build.py` 完整构建（Python 3.12.13 / PyInstaller 6.21.0），`production_source_hash=d8e7a29e…` 与当前源码一致 |
| 激活 | 旧包重命名保留为 `runtime/LocalDatabaseQA_legacy_20261016`；新包复制到 `runtime/LocalDatabaseQA`，`activate_candidate.py --apply` 重生成指针；三条启动链 `-ValidateOnly` 全通过，真实 EXE bootstrap/static 200 |

发布说明与完整验证见 `Archive/20261109_p5_convergence/RELEASE_NOTES.md` 与 `P6_发布与推送报告.md`。该候选 Full-144 三项主指标未达标，故明确标记为 pre-release / NOT V4 Final。
