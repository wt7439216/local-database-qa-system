# Local Textbook QA

一个完全本地运行、答案可追溯到原文页码的教材问答系统。

系统把 PDF 整理成单个 SQLite 知识库，使用 FTS5 全文检索与 Ollama 向量检索双路召回，经 RRF 融合、质量加权和范围判断后，由本地模型生成带原文引用的回答。桌面和手机共用响应式 Web 界面，教材内容无需上传云端。

## 核心特性

### 检索与知识库

- 多 PDF 统一入库：文档、页、章节目录、结构化切片、FTS5 全文索引（正文 + 标题双列，bm25 列加权）、向量统一存储；
- 向量检索使用 bge-m3（1024 维），嵌入输入携带章节/小节路径（上下文嵌入），语义排序更准；
- RRF 融合（语义 1.25 / 词法 1.0），OCR 质量分折扣、标题精确命中加分、近重复过滤、同小节限额、密度候选地板；
- 离题拒答：词法强度 + 密度门限双重判断，门限按嵌入模型注册表自动切换；二字概念问题（"什么是衰落"）按集中命中度放行；
- 章节摘要支持 LLM 预生成（`--llm-summaries`），失败自动回退机械摘要；
- 建库原子替换：临时库通过完整性、片段数、向量数校验后才替换，失败不破坏旧库；
- 增量重建：片段 ID 与内容和页码绑定，未变化片段的向量直接复用。

### 问答与对话

- 意图路由：全书目录、全书介绍、单章概括（中文数字章节号到九十九）、页码/章节定位、比较（按双方分侧检索）、普通问答；书籍级问题不调用模型；
- 多轮追问：追问与上一问合并用于路由和检索，最近 3 轮对话进入模型消息；回答仍只依据本轮材料，历史只用于理解指代；
- 引用纪律：范围/列表引用展开、越界剔除、`[450]MHz` 类非引用保护、拉丁实体核验（先核验后重编号）、按首次出现重编号；
- 材料预算：按上下文窗口自动裁剪尾部材料，杜绝静默截断与幻觉引用；
- 相同问题命中 LRU 缓存（64 条，按教材指纹失效），追问不缓存。

### 界面与服务

- 会话式回答记录、清空会话、引用点击跳转证据卡、markdown 渲染、按动画帧合帧的流式输出、任务排队与取消、SSE 心跳；
- 复制回答在局域网 HTTP（非安全上下文）自动回退兼容方案；未通过核验的引用会弹出提示；
- 安全：六位配对码 + 限速 + 12 小时会话令牌、Host 校验防 DNS rebinding、CSP 等安全响应头、慢连接超时、Windows 端口防抢占；
- 观测：telemetry JSONL（`data/logs/qa_log.jsonl`）+ 可选服务端日志（`QA_LOG_FILE`）。

### 工程化

- 运行时仅用 Python 标准库；52 个不依赖教材与 Ollama 的单元测试；
- `scripts/eval_recall.py` + `golden_set.json`：真实库的召回率/范围门控/路由回归门禁；
- ruff 静态检查、GitHub Actions CI、PyInstaller 一键打包。

## 项目结构

```text
core/                    检索、结构化知识库、Ollama 客户端、问答引擎
desktop/                 本地 Web 服务与桌面启动入口
web/                     响应式浏览器界面（含 markdown.js）
scripts/                 PDF/OCR 导入、建库、召回评估与回归
tests/                   不依赖教材与 Ollama 的单元测试
docs/                    架构说明
data/pdf|raw|library/    教材、提取文本、知识库（本地数据，不入库）
```

## 环境要求

- Python 3.11+（运行时）；[Ollama](https://ollama.com/)
- 模型：`qwen2.5:7b`（回答）、`bge-m3`（向量，当前知识库使用；`nomic-embed-text` 为兼容默认值）

```powershell
ollama pull qwen2.5:7b
ollama pull bge-m3
```

## 快速开始

```powershell
# 1. 提取教材并建库（需要 requirements-ingest.txt 依赖和 Ollama）
python rebuild_all.py

# 2. 源码运行（浏览器打开 http://127.0.0.1:8765，本机自动配对）
python -m desktop

# 3. 打包 Windows 运行包（-SkipIndex 保留当前知识库与 LLM 摘要）
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -SkipIndex
```

配置项、问法示例、多轮追问、手机访问与日志调优的详细说明见下文各节。

## 验证

不需要教材和 Ollama：

```powershell
python -B -m unittest discover -v
python -B -m compileall -q core desktop scripts tests
node --check web/app.js
python -m ruff check core desktop scripts tests
```

已有真实知识库和 Ollama 时：

```powershell
python -X utf8 scripts/eval_recall.py
python -X utf8 scripts/regression_test.py
```

架构和安全边界参见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)；可配置项见 [.env.example](.env.example)。

## 发布前说明

仓库当前未附带开源许可证。公开发布前请根据你的授权意图选择许可证；没有许可证时，其他人默认无权复制、修改或分发代码。
