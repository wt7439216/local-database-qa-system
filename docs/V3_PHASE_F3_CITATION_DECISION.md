# V3 Phase F.3 — Semantic Citation Verifier Decision Gate

> 阶段性质：EVALUATION / DECISION GATE（只读分析 + 隔离临时评测资产，未修改 production code）
> 日期：2026-09-08
> 最终决策：**DEFER_L2**

---

## 1. 核心问题与结论

本阶段回答两个问题：

1. F.2 deterministic Layer-1 Citation verifier 是否已足够满足 KB-V3 的实际 Citation Support 需求？
2. 引入 L2 semantic verifier（本地 LLM judge）是否值得承担新增延迟/资源/复杂度/评测风险？

**结论：**
- L1 在「逐字/确定性信号」场景已足够，但在「语义改写/同义/缩写/单位等价/否定/因果/比较/条件省略」场景有系统性盲区。
- L2（qwen2.5:7b judge）在语义挑战集上**显著优于 L1**（accuracy 0.74 vs 0.28，false-support 0.04 vs 0.10），证明存在明确收益。
- 但当前 L2 judge 契约**未闭合**：从不输出 UNCERTAIN（把 7 个真 UNCERTAIN 强行分类全错）、2 个 false-support（条件省略）未消除、通信领域知识不足（单位/数值等价判错）、延迟 2.7s/case 且与 answer 共用模型。
- 且真实回答级的语义难度分布未知（本挑战集是人工构造的语义困难集），L2 的**真实净收益**必须依赖 F.4 真实回答级 Golden Set 才能量化。

因此决策为 **DEFER_L2**：不否定 L2 的价值，但当前证据不足以支撑正式实现，应先完成 F.4 并在其间优化 judge 契约（UNCERTAIN 引导、领域知识、延迟策略）。

---

## 2. Preflight（冻结基线）

- ACTIVE DEVELOPMENT WORKSPACE：`Local Database Q&A System本地版v3`（无 git，正常）
- GIT PUBLISH WORKSPACE：`Local Database Q&A System上传版`（.git）
- HEAD == origin/main == `f9fad23c58e76b224ce3397b1e5ba349af85e199`，ahead/behind 0/0，worktree clean
- F.2 GitHub Actions run `34236802383` = success
- F.2 测试规模：453 tests；F.2 deterministic citation eval：30/30 PASS
- F.2 verifier version：`f2-v2`
- 关键 F.2 文件（citation_verifier.py / engine_v2.py / test_citation_verifier.py / phase_f_citation_golden.json / eval_phase_f_citation.py）Active 与 Publish **SYNC（无漂移）**
- Ollama 在线：qwen2.5:7b（completion，7.6B，Q4_K_M，32768 ctx）、llama3（completion，8B）、bge-m3（embedding）

## 3. F.2 Frozen Baseline（L1 现状）

F.2 deterministic Layer-1（`core/citation_verifier.py`，`f2-v2`）：
- 四值 support：SUPPORTED / UNSUPPORTED / UNCERTAIN / NOT_APPLICABLE
- 判定链：claim segmentation → validity（范围+present_ids）→ number/unit check → Latin key-term → CJK key-term（缺失仅 UNCERTAIN）
- F.2 deterministic eval：30/30 PASS（代表「逐字/确定性」真实分布）

## 4. L1 Capability Matrix（语义边界实测）

在 50-case 语义挑战集上的逐类行为（L1 结果 vs Ground Truth）：

| 类别 | L1 典型结果 | Ground Truth | 是否正确 | 原因 |
|---|---|---|---|---|
| 逐字一致（Latin/CJK/数字） | SUPPORTED | SUPPORTED | ✓ | token 精确匹配 |
| CJK 同义（符号间干扰=码间串扰） | UNCERTAIN | SUPPORTED | ✗ | CJK run 不重合 → 保守 UNCERTAIN |
| 英文/中文 paraphrase | UNCERTAIN | SUPPORTED | ✗ | 同义改写，token 不重合 |
| 缩写↔全称（OFDM↔正交频分复用） | UNSUPPORTED | SUPPORTED | ✗ | 缩写 token 缺失 → missing key term |
| 单位等价（5 GHz=5000 MHz） | UNSUPPORTED | SUPPORTED | ✗ | number 5≠5000 → number mismatch |
| 数值等价（50%=0.5） | UNSUPPORTED | SUPPORTED | ✗ | number 50≠0.5 |
| 否定丢失（支持↔不支持） | SUPPORTED | UNSUPPORTED | ✗（危险） | token 匹配，无法识别否定 |
| 因果颠倒（A→B vs B→A） | SUPPORTED | UNSUPPORTED | ✗（危险） | token 匹配，无法识别方向 |
| 比较颠倒（大于↔小于） | SUPPORTED | UNSUPPORTED | ✗（危险） | token 匹配，无法识别比较词 |
| 条件省略（丢「高SNR」限定） | SUPPORTED/UNCERTAIN | UNSUPPORTED | ✗（危险） | 无法识别条件限定丢失 |
| 多 evidence 联合 | SUPPORTED | SUPPORTED | ✓ | 联合 combined 文本，token 匹配 |
| 相关但不蕴含（hard negative） | UNCERTAIN/SUPPORTED | UNSUPPORTED | 部分✗ | 主题相关但无蕴含关系无法识别 |
| 矛盾（大量↔少量） | UNCERTAIN | UNSUPPORTED | 部分 | CJK 反义无法识别 |
| 部分支持 | UNCERTAIN | UNCERTAIN | ✓ | 保守正确 |

**L1 的关键结论**：L1 的「保守 UNCERTAIN」是**安全的**（不会伪造 SUPPORTED），但其**危险错误**集中在「否定/因果/比较/条件省略」——这些 token 恰好匹配、但语义相反/不蕴含，L1 会判 SUPPORTED（即 false-support，最高风险）。

## 5. Semantic Challenge Set

- 文件：`eval/phase_f3_semantic_challenge.json`（隔离评估集，非 F.2 golden、非 F.4 最终 Golden Set）
- 规模：**50 cases**，人工标注 ground truth（SUPPORTED 23 / UNSUPPORTED 20 / UNCERTAIN 7），reason 可人工复核
- 覆盖 15 类：direct_supported / cjk_paraphrase / english_paraphrase / abbreviation / unit_equivalence / numeric_equivalence / negation / causal_reversal / comparison / condition_omission / multi_citation / related_not_supported / contradiction / partial_support / genuinely_uncertain
- Ground Truth **未使用待评估 LLM 生成**，全部人工标注

## 6. Candidate L2 与冻结 Judge 合同

- Candidate A：Local Ollama Judge，复用现有 `qwen2.5:7b`（未引入新模型）
- 冻结合同（`scripts/eval_phase_f3.py` 内 `JUDGE_SYSTEM` / `JUDGE_PROMPT_VERSION="judge-f3-v1"`）：
  - model = qwen2.5:7b；temperature=0 / top_p=1 / top_k=1（最低确定性设置）
  - 输入：system（判断器指令）+ user（「结论：…\n证据：…」）
  - 输出：严格 JSON `{"label": "SUPPORTED|UNSUPPORTED|UNCERTAIN", "confidence": 0..1, "reason_code": "..."}`
  - timeout=120s；malformed JSON fallback = UNCERTAIN
  - 禁止 judge 修改证据/重写结论/生成新事实

## 7. L1 vs L2 量化比较（50-case 语义挑战集）

| 指标 | L1（deterministic） | L2（qwen2.5:7b judge） |
|---|---|---|
| **accuracy** | **0.28** | **0.74** |
| false-support rate | 0.10（5） | **0.04（2）** |
| false-reject rate | 0.14（7） | 0.08（4） |
| uncertain rate | 0.54（27） | **0.00（0）** |
| supported precision / recall | 0.53 / 0.35 | 0.83 / 0.83 |
| unsupported precision / recall | 0.13 / 0.05 | 0.67 / 0.90 |

confusion（L2）：
```
              SUPPORTED UNSUPPORTED UNCERTAIN
  SUPPORTED          19           2         2
UNSUPPORTED           4          18         5
  UNCERTAIN           0           0         0
```

## 8. False Support Analysis（最高风险）

L2 的 2 个 false-support（GT=UNSUPPORTED 但判 SUPPORTED）均为**条件省略**：
- f3-031：「系统性能接近理论极限」 vs 「在高信噪比条件下…」（丢失「高 SNR」条件）
- f3-032：「循环前缀可以完全消除干扰」 vs 「当长度大于最大多径时延时…」（丢失条件）

→ L2 未消除「条件省略导致的过度概括」，仍存在 2 个最高风险错误（比 L1 的 5 个少，但未归零）。

## 9. Uncertain Resolution Analysis（L2 真正价值）

- L1 标 UNCERTAIN：27 cases；其中 GT=SUPPORTED 8、GT=UNSUPPORTED 14、GT=UNCERTAIN 5
- L2 从不输出 UNCERTAIN，把 27 个全部强行分类：**正确 19 个，错误 8 个**（resolution accuracy = 0.70）
- 错误 8 个 = 7 个真 UNCERTAIN 全错 + 1 个 GT 判错（f3-005 CJK 同义被 L2 误判 UNSUPPORTED）

→ **关键结论**：L2 能正确解决 19/27 的 L1-UNCERTAIN（有真价值），但「把 7 个 genuinely-UNCERTAIN 强行二值化全部错误」说明当前 judge 未实现四值契约的 UNCERTAIN 输出能力，需 prompt 引导调优。

## 10. Latency / Resource

- L2 judge 单次：**p50 = 2.74s，p95 = 2.79s**（36 次实测，模型已加载后稳定）
- 与 answer 共用 `qwen2.5:7b`（config.ANSWER_MODEL），judge 是 answer 之外的**第二次串行 generation**，会与 answer 争抢 GPU/CPU
- 产品延迟模型：
  - Strategy A（每回答一次 judge）：每个回答 +~2.7s，且与 answer 串行争抢 → **不可接受**
  - Strategy B（仅 L1==UNCERTAIN）：取决于真实 uncertain rate；本语义挑战集 L1 uncertain rate=0.54，但真实回答分布的 uncertain rate 未知（F.2 deterministic 分布下为 0）
  - Strategy C（仅 release eval / debug / strict mode）：零运行时延迟，推荐用于 L2 的定位

## 11. Runtime / Dependency Impact

- L2 复用现有 Ollama + qwen2.5:7b，**零新 runtime dependency、零新模型下载**（满足第 10 节「不默认评估新 NLI 模型」）
- 若实现需 feature flag：`CITATION_SEMANTIC_VERIFIER_ENABLED=false`（默认）+ `CITATION_SEMANTIC_VERIFIER_MODE=uncertain_only`（本阶段未接线，仅设计）

## 12. CI Impact

- L2 不得进入普通 GitHub Actions 强依赖；普通 CI 继续只覆盖 deterministic verifier + F.2 offline eval（`eval_phase_f3.py --mode l1` 可离线，`--mode l2` 依赖 Ollama，不进 CI）

## 13. 决策依据（对照决策标准）

### 为什么不 IMPLEMENT_L2
IMPLEMENT_L2 需同时满足 7 条，本阶段**不满足**：
1. 显著优于 L1 ✓（accuracy +0.46）
2. False Support 不明显恶化 ✓（0.04 < 0.10）
3. 能正确解决大量 L1 UNCERTAIN —— **部分**（19/27 正确，但 7 个真 UNCERTAIN 全错，未实现四值契约）
4. latency/resource 可接受 —— **✗**（2.7s/case 且与 answer 共用模型，Strategy A 不可接受）
5. 无危险新 runtime dependency ✓
6. 可 feature flag ✓
7. failure 有安全 fallback ✓

### 为什么不 DO_NOT_IMPLEMENT_L2
- L2 提升**不是**「很小」：accuracy +0.46、false-support -0.06、false-reject -0.06，证明存在真实价值，不应一票否决。

### 为什么 DEFER_L2
- **当前模型无法可靠判断**：从不输出 UNCERTAIN（契约未实现）+ 领域知识不足（0 dBm=1 mW、20 dB=100 倍、2000 kHz=2 MHz 判错）。
- **应先完成 F.4 实际回答级 Golden Set**：本挑战集是人工构造的语义困难集，L1 uncertain rate=0.54 不代表真实回答分布（F.2 逐字分布下 L1=30/30）。L2 的**真实净收益**与 Strategy B 的延迟代价都必须用真实 Golden Set 量化。

## 14. 决策

**DEFER_L2**

证据摘要：
- L2 有明确价值（accuracy 0.28→0.74，false-support 0.10→0.04），但 judge 契约未闭合（从不输出 UNCERTAIN、2 个 false-support 未消除、领域知识不足）且真实分布未知。
- 触发 IMPLEMENT_L2 复评的条件（满足至少一项再评估，其他变量冻结）：① F.4 真实回答级 Golden Set 建立后量化真实 uncertain rate 与 L2 净收益；② judge prompt 调优实现正确 UNCERTAIN 输出（resolution accuracy 显著提升且 false-support 归零/接近零）；③ 延迟策略（Strategy B/C）在真实分布下证明可接受。

## 15. NLI Model Candidate（登记，不在本阶段评估）

- 若未来 F.4 复评证明 Ollama judge 不足，可提出 `NLI_MODEL_CANDIDATE`（本地 NLI 模型），但**不得在本阶段正式安装进项目**。

## 16. F.2 Regression 确认

- F.2 offline eval：30/30 PASS（未受 F.3 评估影响）
- Phase E router eval：冻结指标保持（route 108/108、follow-up 66/66、ambiguous 0/8、scope conflict 10/10、engine scope leakage 0）
- F.1 summary lifecycle / deterministic verifier：**未因本阶段评估发生任何改变**（F.3 未修改 production code）

## 17. Gate Decision

**Phase F.3 = PASS**（评估与决策完成，结论 DEFER_L2；未跨阶段实施 L2）

**STOP**：不实施 L2、不进入 F.4、不扩充最终 Golden Set、不实现 Answer quality judge / Release quality gate，等待新的单独授权。
