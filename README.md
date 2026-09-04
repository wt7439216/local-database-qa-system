# Local Textbook QA

一个完全本地运行、答案可追溯到原文页码的教材问答系统。

系统把 PDF 整理成单个 SQLite 知识库，使用 FTS5 全文检索与 Ollama 向量检索召回内容，经 RRF 融合、近重复过滤和范围判断后，再由本地模型生成带引用的回答。桌面和手机共用响应式 Web 界面，教材内容无需上传云端。

## 特性

- 文档、PDF 页、正文页、章节、小节、全文索引和向量统一存储；
- 支持多 PDF，文档和页码互不串联；
- 支持普通问答、对比、位置查询和全书概括；
- 回答附带原文片段及准确位置；
- 离题问题会直接拒答；
- 流式输出、任务排队和取消；
- 临时会话令牌与配对失败限速；
- 知识库原子更新，失败不会覆盖上一个可用版本；
- 运行时仅使用 Python 标准库。

## 项目结构

```text
core/                    检索、结构化知识库、Ollama 客户端、问答引擎
desktop/                 本地 Web 服务与桌面启动入口
web/                     响应式浏览器界面
scripts/                 PDF/OCR 导入、建库和真实检索回归
tests/                   不依赖教材与 Ollama 的单元测试
docs/                    架构说明
data/pdf/                本地 PDF（Git 忽略）
data/raw/                OCR/文本抽取结果（Git 忽略）
data/library/            SQLite 知识库（Git 忽略）
```

## 环境要求

- Python 3.11+
- [Ollama](https://ollama.com/)
- 默认模型：`qwen2.5:7b`、`nomic-embed-text`

```powershell
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

## 导入教材

PDF、OCR 文本和生成的数据库可能包含受版权保护的内容，因此仓库不会提交这些文件。

1. 安装导入依赖：

```powershell
python -m pip install -r requirements-ingest.txt
```

2. 把有权使用的 PDF 放入 `data/pdf/`。

3. 提取文本并构建知识库：

```powershell
python rebuild_all.py
```

若已经有符合页标记格式的 `data/raw/book.txt`，可直接执行：

```powershell
python -X utf8 scripts/build_library.py
```

再次构建时会按片段 ID 复用未变化的向量。

## 运行

```powershell
python -m desktop
```

浏览器将打开 `http://127.0.0.1:8765`。本机自动完成配对；如需在同一可信局域网内通过手机访问，可设置：

```powershell
$env:QA_DESKTOP_HOST="0.0.0.0"
python -m desktop
```

不要把该 HTTP 服务直接暴露到公网。退出时在本机页面打开“连接设置”，点击“停止本地服务”。

可配置项见 [.env.example](.env.example)。程序读取同名环境变量，不会自动加载 `.env` 文件。

## Windows 打包

```powershell
python -m pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

打包前必须先生成 `data/library/textbooks.sqlite3`。产物写入 `desktop/dist/`，不会提交到 Git。

## 验证

不需要教材和 Ollama：

```powershell
python -B -m unittest discover -v
python -B -m compileall -q core desktop scripts tests
node --check web/app.js
```

已有真实知识库和 Ollama 时：

```powershell
python -X utf8 scripts/regression_test.py
```

架构和安全边界参见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 发布前说明

仓库当前未附带开源许可证。公开发布前请根据你的授权意图选择许可证；没有许可证时，其他人默认无权复制、修改或分发代码。
