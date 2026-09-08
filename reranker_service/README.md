# Reranker Sidecar (Phase B / v3.1)

可选的本地 cross-encoder 重排服务。主程序运行时仍然**只用 Python 标准库**；
torch / transformers 只存在于本目录的独立环境中，通过 loopback HTTP 调用。

## 安装（独立 venv，与主程序完全隔离）

```powershell
cd reranker_service
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

模型 `BAAI/bge-reranker-v2-m3` 首次运行时自动下载到 Hugging Face 用户缓存
（`%USERPROFILE%\.cache\huggingface`），约 2.3 GB，不会写入本仓库。

## 启动

```powershell
# CUDA（若显存允许）；显存不足时用 --device cpu
.venv\Scripts\python server.py --device auto --max-length 1024
# 默认 127.0.0.1:7998，loopback-only，不暴露局域网
```

## 接口

- `GET /health` → `{"status", "model", "device", "dtype", "max_length", "model_loaded"}`
- `GET /model` → `{"model", "revision", "cache_dir", "device", "dtype", "max_length", "max_model_length"}`
- `POST /rerank` → 请求 `{"query", "documents": [{"id", "text"}]}`，响应
  `{"model", "results": [{"id", "score"}], "truncated_candidates", "ms"}`

协议：结果 id 与请求 id 一一对应；重复 id → 400；响应缺 id / 多 id → 400；
NaN/inf 分数 → 422；malformed JSON → 400。

## 主程序侧

```text
RERANKER_ENABLED=false        # 默认关闭；关闭时检索与 Phase A 完全一致
RERANKER_URL=http://127.0.0.1:7998
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
RERANK_CANDIDATE_K=16
RERANK_TIMEOUT_SECONDS=30
RERANKER_FALLBACK=disabled    # sidecar 不可用时报错；=rrf 则回退 RRF 排序
```
