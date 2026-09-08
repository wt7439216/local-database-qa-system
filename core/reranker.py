"""Reranker protocol and adapters (Phase B / v3.1).

The main runtime keeps its stdlib-only contract: reranking happens in an
optional local sidecar process (``reranker_service/``) reached over loopback
HTTP, never via torch/transformers in-process and never via an Ollama
endpoint.  The reranker is a RELEVANCE ORDERER only — it never decides
scope/OOS, never owns chunk text and never writes business data.

Error contract: unavailable (down/timeout), HTTP failure, protocol violation
(duplicate/missing/unknown ids, NaN/inf scores, malformed JSON) and model
mismatch are distinct, typed errors so callers can decide fallback behavior
explicitly (``RERANKER_FALLBACK=disabled|rrf``).
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import urllib.error
import urllib.request
from typing import Protocol, runtime_checkable

from core import config
from core.ollama_http import open_request


class RerankerError(RuntimeError):
    """Base class for reranker failures."""


class RerankerUnavailableError(RerankerError):
    """The reranker sidecar cannot be reached (down, refused, timeout)."""


class RerankerHTTPError(RerankerError):
    """The sidecar answered with a non-2xx HTTP status."""


class RerankerProtocolError(RerankerError):
    """The sidecar response violates the rerank HTTP contract."""


class RerankerModelMismatchError(RerankerError):
    """The sidecar reports a different model than configured."""


@dataclass(frozen=True)
class RerankCandidate:
    id: str
    text: str


@dataclass(frozen=True)
class RerankedHit:
    id: str
    rerank_score: float


@dataclass(frozen=True)
class RerankerHealth:
    ok: bool
    model: str = ""
    device: str = ""
    dtype: str = ""
    max_length: int = 0
    loaded: bool = False
    error: str = ""


@runtime_checkable
class Reranker(Protocol):
    """Relevance orderer over candidates that already passed hybrid retrieval."""

    def health(self) -> RerankerHealth: ...

    def rerank(
        self,
        query: str,
        candidates: list[RerankCandidate],
        *,
        top_k: int | None = None,
    ) -> list[RerankedHit]: ...


class IdentityReranker:
    """Order-preserving no-op reranker (tests and explicit opt-in only).

    The disabled production path short-circuits in HybridRetriever without
    calling any reranker at all, guaranteeing byte-identical Phase A output.
    """

    def __init__(self, model: str = "identity"):
        self.model = model

    def health(self) -> RerankerHealth:
        return RerankerHealth(ok=True, model=self.model, device="none", dtype="none")

    def rerank(
        self,
        query: str,
        candidates: list[RerankCandidate],
        *,
        top_k: int | None = None,
    ) -> list[RerankedHit]:
        hits = [RerankedHit(id=candidate.id, rerank_score=float(-index)) for index, candidate in enumerate(candidates)]
        return hits if top_k is None else hits[:top_k]


def _finite_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise RerankerProtocolError(f"rerank score 不是数值：{value!r}") from exc
    if not math.isfinite(score):
        raise RerankerProtocolError(f"rerank score 非有限（NaN/inf）：{value!r}")
    return score


class HTTPReranker:
    """Cross-encoder reranker over the loopback sidecar HTTP contract.

    ``GET /health`` and ``POST /rerank`` per docs/reranker contract; result
    ids must correspond 1:1 with request ids (never by position).  Tie policy:
    scores are sorted descending with a stable sort, so equal scores keep the
    pre-rerank candidate order.
    """

    backend = "http"

    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        transport=None,
    ):
        self.url = (url or config.RERANKER_URL).rstrip("/")
        self.model = model or config.RERANKER_MODEL
        self.timeout = float(timeout if timeout is not None else config.RERANK_TIMEOUT_SECONDS)
        self.transport = transport
        self.last_truncated_candidates: int | None = None
        self.last_ms: float | None = None

    # -- transport ------------------------------------------------------------

    def _request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        if self.transport is not None:
            status, data = self.transport(method, path, payload, self.timeout)
            if not isinstance(data, dict):
                raise RerankerProtocolError("Reranker 返回的数据格式不正确。")
            return status, data
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = urllib.request.Request(
            f"{self.url}{path}", data=body, headers=headers, method=method
        )
        try:
            with open_request(request, timeout=self.timeout) as response:
                raw = response.read()
                status = int(getattr(response, "status", response.getcode()))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                parsed = json.loads(exc.read().decode("utf-8", errors="replace"))
                detail = str(parsed.get("error") or "")
            except Exception:
                pass
            suffix = f"：{detail}" if detail else ""
            raise RerankerHTTPError(f"Reranker 请求失败（HTTP {exc.code}）{suffix}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RerankerUnavailableError(f"无法连接 Reranker sidecar（{self.url}）：{exc}") from exc
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RerankerProtocolError("Reranker 返回了无法解析的数据。") from exc
        if not isinstance(data, dict):
            raise RerankerProtocolError("Reranker 返回的数据格式不正确。")
        return status, data

    # -- contract ---------------------------------------------------------------

    def health(self) -> RerankerHealth:
        try:
            _, data = self._request("GET", "/health")
        except RerankerError as exc:
            return RerankerHealth(ok=False, model=self.model, error=str(exc))
        model = str(data.get("model") or "")
        loaded = bool(data.get("model_loaded"))
        error = str(data.get("load_error") or "")
        if model != self.model:
            return RerankerHealth(
                ok=False,
                model=model,
                device=str(data.get("device") or ""),
                dtype=str(data.get("dtype") or ""),
                max_length=int(data.get("max_length") or 0),
                loaded=loaded,
                error=f"模型不匹配：sidecar={model or '(空)'}，配置={self.model}",
            )
        return RerankerHealth(
            ok=True,
            model=model,
            device=str(data.get("device") or ""),
            dtype=str(data.get("dtype") or ""),
            max_length=int(data.get("max_length") or 0),
            loaded=loaded,
            error=error,
        )

    def rerank(
        self,
        query: str,
        candidates: list[RerankCandidate],
        *,
        top_k: int | None = None,
    ) -> list[RerankedHit]:
        if not query.strip():
            raise RerankerProtocolError("rerank query 不能为空。")
        if not candidates:
            return []
        ids = [candidate.id for candidate in candidates]
        if len(set(ids)) != len(ids):
            raise RerankerProtocolError("rerank 候选存在重复 id。")
        payload = {
            "query": query,
            "documents": [{"id": candidate.id, "text": candidate.text} for candidate in candidates],
        }
        _, data = self._request("POST", "/rerank", payload)
        response_model = data.get("model")
        if response_model and response_model != self.model:
            raise RerankerModelMismatchError(
                f"sidecar 模型 {response_model} 与配置 {self.model} 不一致。"
            )
        results = data.get("results")
        if not isinstance(results, list):
            raise RerankerProtocolError("rerank 响应缺少 results 列表。")
        expected = set(ids)
        seen: dict[str, float] = {}
        for item in results:
            if not isinstance(item, dict) or "id" not in item or "score" not in item:
                raise RerankerProtocolError("rerank results 条目缺少 id 或 score。")
            result_id = item["id"]
            if result_id not in expected:
                raise RerankerProtocolError(f"rerank 响应包含未知 id：{result_id}")
            if result_id in seen:
                raise RerankerProtocolError(f"rerank 响应包含重复 id：{result_id}")
            seen[result_id] = _finite_score(item["score"])
        missing = [candidate_id for candidate_id in ids if candidate_id not in seen]
        if missing:
            raise RerankerProtocolError(f"rerank 响应缺少 id：{missing}")
        truncated = data.get("truncated_candidates")
        self.last_truncated_candidates = int(truncated) if truncated is not None else None
        self.last_ms = float(data["ms"]) if isinstance(data.get("ms"), (int, float)) else None
        # Stable sort: equal scores keep the pre-rerank candidate order.
        ordered = [RerankedHit(id=candidate_id, rerank_score=seen[candidate_id]) for candidate_id in ids]
        ordered.sort(key=lambda hit: hit.rerank_score, reverse=True)
        return ordered if top_k is None else ordered[:top_k]


def create_reranker() -> Reranker | None:
    """Build the configured reranker; ``None`` when disabled (default)."""
    if not config.RERANKER_ENABLED:
        return None
    return HTTPReranker()
