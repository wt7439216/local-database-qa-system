"""Local cross-encoder reranker sidecar (Phase B / v3.1).

An isolated OPTIONAL runtime: torch + transformers live only in this
service's own environment (``reranker_service/requirements.txt``, own venv).
The main application keeps its stdlib-only contract and talks to this sidecar
over loopback HTTP.  Loopback requests bypass system proxies (the server also
binds 127.0.0.1 only and is never exposed to the LAN).

Endpoints
  GET  /health  {"status", "model", "device", "dtype", "max_length",
                 "model_loaded", "load_error"}
  GET  /model   {"model", "revision", "cache_dir", "device", "dtype",
                 "max_length", "max_model_length"}
  POST /rerank  body  {"query": str, "documents": [{"id": str, "text": str}]}
                resp  {"model", "results": [{"id", "score"}],
                       "truncated_candidates", "ms"}

Protocol guarantees (mirrored by core/reranker.py):
  - result ids correspond 1:1 with request ids (never positional)
  - duplicate request ids -> 400
  - every request id appears exactly once in the response
  - scores must be finite (NaN/inf -> 422)
  - malformed JSON / missing fields -> 400

Scoring follows the BAAI/bge-reranker-v2-m3 model card:
AutoModelForSequenceClassification + sigmoid(logit) in [0, 1].

Run:
    python server.py --host 127.0.0.1 --port 7998 \
        --model BAAI/bge-reranker-v2-m3 --max-length 1024 --device auto
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_LENGTH_CAP = 8192

_state_lock = threading.Lock()
_state = {
    "model": None,       # transformers model
    "tokenizer": None,
    "device": "",
    "dtype": "",
    "max_length": 0,     # configured max sequence length actually used
    "max_model_length": 0,
    "loaded": False,
    "load_error": "",
    "revision": "",
    "cache_dir": "",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="本地 cross-encoder reranker sidecar")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7998)
    parser.add_argument("--model", default="BAAI/bge-reranker-v2-m3")
    parser.add_argument(
        "--max-length", type=int, default=1024,
        help="configured max query+passage tokens (clamped to the model's own limit)",
    )
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument(
        "--lazy", action="store_true",
        help="defer model loading until the first /rerank instead of at startup",
    )
    parser.add_argument("--dtype", default="auto", choices=["auto", "float16", "float32"])
    args = parser.parse_args()
    if not (1 <= args.max_length <= MAX_LENGTH_CAP):
        parser.error(f"--max-length 必须在 1..{MAX_LENGTH_CAP} 之间")
    return args


def _resolve_device(args) -> tuple[str, str]:
    import torch

    if args.device == "cpu":
        return "cpu", "float32"
    cuda_available = torch.cuda.is_available()
    if args.device == "cuda" and not cuda_available:
        raise RuntimeError("CUDA 不可用（--device cuda），请改用 --device cpu。")
    if cuda_available:
        return "cuda", "float16" if args.dtype == "auto" else args.dtype
    return "cpu", "float32" if args.dtype == "auto" else args.dtype


def load_model(args) -> None:
    """Load the cross-encoder once; failures are recorded for /health."""
    with _state_lock:
        if _state["loaded"] or _state["load_error"]:
            return
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            device, dtype_name = _resolve_device(args)
            dtype = {"float16": torch.float16, "float32": torch.float32}[dtype_name]
            tokenizer = AutoTokenizer.from_pretrained(args.model)
            model = AutoModelForSequenceClassification.from_pretrained(
                args.model, torch_dtype=dtype
            ).to(device)
            model.eval()
            model_max = tokenizer.model_max_length
            if model_max is None or model_max > MAX_LENGTH_CAP or model_max <= 0:
                model_max = MAX_LENGTH_CAP  # guard against sentinel values (1e30)
            configured = min(args.max_length, model_max)
            _state.update(
                {
                    "model": model,
                    "tokenizer": tokenizer,
                    "device": device,
                    "dtype": dtype_name,
                    "max_length": int(configured),
                    "max_model_length": int(model_max),
                    "loaded": True,
                    "revision": str(getattr(model.config, "_commit_hash", "") or ""),
                    "cache_dir": str(getattr(model.config, "name_or_path", "") or args.model),
                }
            )
            print(f"[OK] model loaded: {args.model} on {device} ({dtype_name}), "
                  f"max_length={configured}/{model_max}", flush=True)
        except Exception as exc:  # pragma: no cover - depends on runtime env
            _state["load_error"] = f"{type(exc).__name__}: {exc}"
            print(f"[FAIL] model load failed: {_state['load_error']}", flush=True)


def handler_factory(args):
    class Handler(BaseHTTPRequestHandler):
        server_version = "LocalReranker/1"

        def _json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _health_payload(self) -> dict:
            with _state_lock:
                return {
                    "status": "ok" if not _state["load_error"] else "error",
                    "model": args.model,
                    "device": _state["device"] or args.device,
                    "dtype": _state["dtype"],
                    "max_length": _state["max_length"] or args.max_length,
                    "max_model_length": _state["max_model_length"],
                    "model_loaded": _state["loaded"],
                    "load_error": _state["load_error"],
                }

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self._json(200, self._health_payload())
                return
            if self.path == "/model":
                with _state_lock:
                    self._json(200, {
                        "model": args.model,
                        "revision": _state["revision"],
                        "cache_dir": _state["cache_dir"],
                        "device": _state["device"],
                        "dtype": _state["dtype"],
                        "max_length": _state["max_length"],
                        "max_model_length": _state["max_model_length"],
                    })
                return
            self._json(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            if self.path != "/rerank":
                self._json(404, {"error": "not found"})
                return
            if not _state["loaded"]:
                if _state["load_error"]:
                    self._json(503, {"error": f"model load failed: {_state['load_error']}"})
                    return
                load_model(args)
                if not _state["loaded"]:
                    self._json(503, {"error": "model not ready"})
                    return
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._json(400, {"error": f"malformed JSON body: {exc}"})
                return
            error = _validate(body)
            if error:
                self._json(400, {"error": error})
                return

            started = time.perf_counter()
            outcome = _score(body["query"], body["documents"])
            if isinstance(outcome, str):
                self._json(422, {"error": outcome})
                return
            scores, truncated = outcome
            results = [
                {"id": doc["id"], "score": round(score, 6)}
                for doc, score in scores
            ]
            self._json(200, {
                "model": args.model,
                "results": results,
                "truncated_candidates": truncated,
                "ms": round((time.perf_counter() - started) * 1000, 1),
            })

        def log_message(self, format, *args):  # noqa: A002
            return

    return Handler


def _validate(body) -> str | None:
    if not isinstance(body, dict):
        return "body must be a JSON object"
    query = body.get("query")
    if not isinstance(query, str) or not query.strip():
        return "query must be a non-empty string"
    documents = body.get("documents")
    if not isinstance(documents, list) or not documents:
        return "documents must be a non-empty list"
    seen_ids = set()
    for doc in documents:
        if not isinstance(doc, dict) or not isinstance(doc.get("id"), str) or not doc["id"]:
            return "every document needs a non-empty string id"
        if not isinstance(doc.get("text"), str) or not doc["text"].strip():
            return "every document needs a non-empty string text"
        if doc["id"] in seen_ids:
            return f"duplicate document id: {doc['id']}"
        seen_ids.add(doc["id"])
    return None


def _score(query: str, documents: list[dict]):
    """Cross-encoder scoring; returns ([(doc, score)] sorted desc, truncated) or an error string."""
    import math

    import torch

    model, tokenizer = _state["model"], _state["tokenizer"]
    max_length = _state["max_length"]
    device = _state["device"]

    lengths = []
    for doc in documents:
        token_count = len(tokenizer(query, doc["text"], add_special_tokens=True)["input_ids"])
        lengths.append(token_count)
    truncated = sum(1 for value in lengths if value > max_length)

    encoded = tokenizer(
        [query] * len(documents),
        [doc["text"] for doc in documents],
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    ).to(device)
    with torch.no_grad():
        logits = model(**encoded).logits
        if logits.dim() > 1:
            logits = logits[:, 0]
        scores = torch.sigmoid(logits.float()).squeeze(-1).tolist()
    if any(not math.isfinite(score) for score in scores):
        return "model produced a non-finite score (NaN/inf)"
    # Stable sort: request order wins on exact ties.
    ranked = sorted(zip(documents, scores), key=lambda pair: pair[1], reverse=True)
    return ranked, truncated


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), handler_factory(args))
    server.daemon_threads = True
    print(f"[OK] reranker sidecar listening on http://{args.host}:{args.port} "
          f"(model={args.model}, device={args.device}, lazy={args.lazy})", flush=True)
    if not args.lazy:
        load_model(args)
        if _state["load_error"]:
            return 1
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
