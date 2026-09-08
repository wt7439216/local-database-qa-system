"""Qdrant REST VectorStore — Python-stdlib HTTP adapter (QD-01 Option A).

Keeps the "runtime uses only the Python standard library" contract: no
``qdrant-client`` dependency.  Requests to loopback hosts (127.0.0.1,
localhost, ::1) always bypass HTTP(S) proxies; non-loopback hosts keep
urllib's default proxy behavior (see ``core.ollama_http.open_request``).

Qdrant is a fully rebuildable dense index only.  It never stores authoritative
chunk text and never writes SQLite business data.  The primary read path is
the modern Query API (``POST /collections/{c}/points/query``), not the legacy
``/points/search`` endpoint.

All HTTP access goes through an injectable transport (``HttpQdrantTransport``
in production, fakes in tests) with timeouts, HTTP-status validation, JSON
validation and Qdrant ``status`` validation mapped to typed errors.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from core import config
from core.ollama_http import open_request
from core.vector_store import (
    DEFAULT_KNOWLEDGE_BASE_ID,
    IndexManifest,
    IndexVerification,
    VectorBackendUnavailableError,
    VectorDimensionMismatchError,
    VectorHealth,
    VectorHit,
    VectorModelMismatchError,
    VectorProtocolError,
    VectorRecord,
    VectorScope,
    VectorStoreError,
    point_id_for,
    validate_query_vector,
)

# Payload fields requested from Qdrant during query/scroll; chunk text is
# deliberately NOT part of the payload (SQLite owns the text).
QUERY_PAYLOAD_FIELDS = ["chunk_id", "document_id"]
VERIFY_PAYLOAD_FIELDS = [
    "chunk_id",
    "document_id",
    "knowledge_base_id",
    "embedding_model",
    "embedding_dimension",
    "content_hash",
    "vector_input_hash",
]
# Keyword payload indexes created with the collection (plan 7.5; Phase D adds
# document_type + tags for scope pushdown).
PAYLOAD_INDEX_FIELDS = ("document_id", "knowledge_base_id", "embedding_model", "document_type", "tags")


class QdrantHTTPError(VectorStoreError):
    """Qdrant answered with a non-2xx HTTP status."""


class QdrantTransport:
    """Minimal transport boundary so every REST interaction can be faked."""

    def request(self, method: str, path: str, payload: dict | None = None, timeout: float | None = None) -> tuple[int, dict]:
        raise NotImplementedError


class HttpQdrantTransport(QdrantTransport):
    """urllib transport bound to one Qdrant base URL; loopback is proxy-free."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)

    def request(self, method: str, path: str, payload: dict | None = None, timeout: float | None = None) -> tuple[int, dict]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, headers=headers, method=method
        )
        try:
            with open_request(request, timeout=timeout or self.timeout) as response:
                raw = response.read()
                status = int(getattr(response, "status", response.getcode()))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                parsed = json.loads(exc.read().decode("utf-8", errors="replace"))
                detail = str(parsed.get("error") or parsed.get("status") or "")
            except Exception:
                pass
            suffix = f"：{detail}" if detail else ""
            raise QdrantHTTPError(f"Qdrant 请求失败（HTTP {exc.code}）{suffix}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise VectorBackendUnavailableError(
                f"无法连接 Qdrant（{self.base_url}）：{exc}"
            ) from exc
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise VectorProtocolError("Qdrant 返回了无法解析的数据。") from exc
        if not isinstance(data, dict):
            raise VectorProtocolError("Qdrant 返回的数据格式不正确。")
        return status, data


class QdrantVectorStore:
    """Dense index backed by a Qdrant collection over the REST Query API."""

    backend = "qdrant"
    # A configured Qdrant backend always intends dense retrieval; actual
    # availability is enforced at search time with explicit errors (never a
    # silent keyword fallback).  SQLite keeps the rebuild-source vectors.
    has_vectors = True

    def __init__(
        self,
        base_url: str | None = None,
        collection: str | None = None,
        timeout: float | None = None,
        transport: QdrantTransport | None = None,
    ):
        self.collection = collection or config.QDRANT_COLLECTION
        self.timeout = float(timeout if timeout is not None else config.QDRANT_TIMEOUT_SECONDS)
        self.transport = transport or HttpQdrantTransport(
            base_url or config.QDRANT_URL, timeout=self.timeout
        )
        self._dimension: int | None = None
        self._distance: str | None = None

    @classmethod
    def from_config(cls) -> "QdrantVectorStore":
        return cls(
            base_url=config.QDRANT_URL,
            collection=config.QDRANT_COLLECTION,
            timeout=config.QDRANT_TIMEOUT_SECONDS,
        )

    # -- transport helpers ----------------------------------------------------

    def _request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        return self.transport.request(method, path, payload, timeout=self.timeout)

    @staticmethod
    def _result_of(data: dict, path: str):
        status = data.get("status")
        if isinstance(status, str) and status != "ok":
            raise VectorProtocolError(f"Qdrant {path} 返回状态 {status}。")
        if "result" not in data:
            raise VectorProtocolError(f"Qdrant {path} 响应缺少 result 字段。")
        return data["result"]

    # -- collection management --------------------------------------------------

    def server_version(self) -> str:
        _, data = self._request("GET", "/")
        return str(data.get("version") or "")

    def collection_info(self) -> dict | None:
        """Collection config dict, or None when the collection does not exist."""
        try:
            _, data = self._request("GET", f"/collections/{self.collection}")
        except QdrantHTTPError as exc:
            if "404" in str(exc):
                return None
            raise
        result = self._result_of(data, "collections/{name}")
        return result if isinstance(result, dict) else None

    def collection_dimension(self) -> int:
        if self._dimension:
            return self._dimension
        info = self.collection_info()
        if info is None:
            raise VectorStoreError(
                f"Qdrant collection 不存在：{self.collection}。请先运行 scripts/rebuild_vector_index.py。"
            )
        vectors = info.get("config", {}).get("params", {}).get("vectors")
        if isinstance(vectors, dict):
            size = int(vectors.get("size") or 0)
            distance = str(vectors.get("distance") or "")
        else:  # named-vectors collections are out of scope for Phase A
            raise VectorStoreError("Qdrant collection 未使用单一向量配置，Phase A 不支持。")
        if size <= 0:
            raise VectorStoreError("Qdrant collection 向量维度无效。")
        self._dimension = size
        self._distance = distance
        return size

    def create_collection(self, dimension: int, distance: str = "Cosine") -> None:
        if dimension <= 0:
            raise VectorDimensionMismatchError(f"非法的 collection 维度：{dimension}")
        _, data = self._request(
            "PUT",
            f"/collections/{self.collection}",
            {"vectors": {"size": int(dimension), "distance": distance}},
        )
        self._result_of(data, "create collection")
        self._dimension = int(dimension)
        self._distance = distance

    def ensure_collection(self, dimension: int, distance: str = "Cosine") -> None:
        """Create the collection when missing; refuse silent re-creation or
        dimension/distance changes on an existing one."""
        info = self.collection_info()
        if info is None:
            self.create_collection(dimension, distance)
        else:
            vectors = info.get("config", {}).get("params", {}).get("vectors")
            size = int((vectors or {}).get("size") or 0)
            existing_distance = str((vectors or {}).get("distance") or "")
            if size != int(dimension) or existing_distance != distance:
                raise VectorDimensionMismatchError(
                    f"Qdrant collection 配置不匹配：现有 {size}/{existing_distance}，期望 {dimension}/{distance}。"
                    "如需更改请显式删除 collection 后重建。"
                )
            self._dimension = size
            self._distance = existing_distance
        self.ensure_payload_indexes()

    def ensure_payload_indexes(self) -> None:
        for field_name in PAYLOAD_INDEX_FIELDS:
            self._request(
                "PUT",
                f"/collections/{self.collection}/index",
                {"field_name": field_name, "field_schema": "keyword"},
            )

    def count_points(self) -> int:
        _, data = self._request(
            "POST", f"/collections/{self.collection}/points/count", {"exact": True}
        )
        result = self._result_of(data, "points/count")
        return int(result.get("count") or 0) if isinstance(result, dict) else 0

    def delete_collection(self) -> None:
        _, data = self._request("DELETE", f"/collections/{self.collection}")
        self._result_of(data, "delete collection")
        self._dimension = None
        self._distance = None

    # -- VectorStore contract ---------------------------------------------------

    def health(self) -> VectorHealth:
        try:
            _, data = self._request("GET", "/")
        except VectorStoreError as exc:
            return VectorHealth(ok=False, backend=self.backend, error=str(exc))
        version = str(data.get("version") or "")
        detail: dict = {"version": version, "url": getattr(self.transport, "base_url", "")}
        try:
            dimension = self.collection_dimension()
            info = self.collection_info() or {}
            detail.update(
                {
                    "collection": self.collection,
                    "dimension": dimension,
                    "distance": self._distance,
                    "points_count": info.get("points_count"),
                    "collection_status": info.get("status"),
                }
            )
        except VectorStoreError as exc:
            return VectorHealth(
                ok=False, backend=self.backend, error=str(exc), detail=detail
            )
        return VectorHealth(ok=True, backend=self.backend, dimension=dimension, detail=detail)

    def search(
        self,
        vector: list[float],
        *,
        limit: int,
        scope: VectorScope | None = None,
    ) -> list[VectorHit]:
        if limit <= 0:
            return []
        dimension = self.collection_dimension()
        normalized = validate_query_vector(vector, dimension)
        body: dict = {
            "query": normalized,
            "limit": int(limit),
            "with_payload": QUERY_PAYLOAD_FIELDS,
        }
        query_filter = _scope_filter(scope)
        if query_filter is not None:
            body["filter"] = query_filter
        _, data = self._request("POST", f"/collections/{self.collection}/points/query", body)
        result = self._result_of(data, "points/query")
        points = result.get("points", []) if isinstance(result, dict) else result
        hits: list[VectorHit] = []
        for point in points:
            payload = point.get("payload") or {}
            chunk_id = payload.get("chunk_id")
            if not chunk_id:
                raise VectorProtocolError("Qdrant 命中缺少 payload.chunk_id，无法回查 SQLite。")
            hits.append(
                VectorHit(
                    chunk_id=str(chunk_id),
                    document_id=str(payload.get("document_id") or ""),
                    dense_score=float(point.get("score") or 0.0),
                    backend=self.backend,
                )
            )
        return hits

    def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        model = str(records[0].embedding_model)
        dimension = int(records[0].embedding_dimension)
        for record in records:
            if int(record.embedding_dimension) != len(record.vector):
                raise VectorDimensionMismatchError(
                    f"记录 {record.chunk_id} 声明维度 {record.embedding_dimension} 与向量长度 {len(record.vector)} 不一致。"
                )
            if int(record.embedding_dimension) != dimension or str(record.embedding_model) != model:
                raise VectorModelMismatchError(
                    "同一批次内出现不同 embedding 模型或维度，拒绝混合写入。"
                )
        existing_dimension = self.collection_info()
        if existing_dimension is not None:
            stored_dimension = self.collection_dimension()
            if stored_dimension != dimension:
                raise VectorDimensionMismatchError(
                    f"Qdrant collection 维度为 {stored_dimension}，与记录维度 {dimension} 不一致。"
                )
        points = [
            {
                "id": point_id_for(record.chunk_id),
                "vector": [float(value) for value in record.vector],
                "payload": _payload_of(record, dimension),
            }
            for record in records
        ]
        for start in range(0, len(points), UPSERT_BATCH):
            batch = points[start : start + UPSERT_BATCH]
            _, data = self._request(
                "PUT",
                f"/collections/{self.collection}/points?wait=true",
                {"points": batch},
            )
            result = self._result_of(data, "points upsert")
            if isinstance(result, dict) and str(result.get("status") or "") not in {"completed", "acknowledged"}:
                raise VectorProtocolError(f"Qdrant upsert 未完成：{result.get('status')}")

    def delete_documents(self, document_ids: list[str]) -> None:
        ids = sorted({str(value) for value in document_ids if str(value)})
        if not ids:
            return
        body = {"filter": {"must": [{"key": "document_id", "match": {"any": ids}}]}}
        _, data = self._request(
            "POST", f"/collections/{self.collection}/points/delete?wait=true", body
        )
        result = self._result_of(data, "points/delete")
        if isinstance(result, dict) and str(result.get("status") or "") not in {"completed", "acknowledged"}:
            raise VectorProtocolError(f"Qdrant delete 未完成：{result.get('status')}")

    def delete_points(self, point_ids: list[str]) -> None:
        ids = [str(value) for value in point_ids if str(value)]
        if not ids:
            return
        _, data = self._request(
            "POST",
            f"/collections/{self.collection}/points/delete?wait=true",
            {"points": ids},
        )
        self._result_of(data, "points/delete")

    def scroll_payloads(self, batch: int = 256, query_filter: dict | None = None) -> list[dict]:
        """Enumerate point payloads (with_vector=false), optionally filtered."""
        offset = "start"
        payloads: list[dict] = []
        while offset:
            body: dict = {"limit": int(batch), "with_payload": True, "with_vector": False}
            if offset != "start":
                body["offset"] = offset
            if query_filter is not None:
                body["filter"] = query_filter
            _, data = self._request("POST", f"/collections/{self.collection}/points/scroll", body)
            result = self._result_of(data, "points/scroll")
            if not isinstance(result, dict):
                raise VectorProtocolError("Qdrant scroll 响应格式不正确。")
            for point in result.get("points", []):
                payloads.append(point.get("payload") or {})
            offset = result.get("next_page_offset")
        return payloads

    def verify(self, manifest: IndexManifest) -> IndexVerification:
        errors: list[str] = []
        info = self.collection_info()
        if info is None:
            return IndexVerification(
                expected=len(manifest.entries),
                actual=0,
                errors=[f"Qdrant collection 不存在：{self.collection}"],
            )
        vectors = info.get("config", {}).get("params", {}).get("vectors") or {}
        size = int(vectors.get("size") or 0)
        distance = str(vectors.get("distance") or "")
        if size != int(manifest.dimension):
            errors.append(
                f"collection 维度不匹配：Qdrant {size}，manifest {manifest.dimension}"
            )
        if distance != manifest.distance:
            errors.append(
                f"collection 距离不匹配：Qdrant {distance}，manifest {manifest.distance}"
            )
        model_mismatch: list[str] = []
        dimension_mismatch: list[str] = []
        content_mismatch: list[str] = []
        vector_input_mismatch: list[str] = []
        seen_chunk_ids: set[str] = set()
        actual = 0
        for payload in self.scroll_payloads():
            actual += 1
            chunk_id = str(payload.get("chunk_id") or "")
            if not chunk_id:
                errors.append("存在缺少 payload.chunk_id 的 point。")
                continue
            seen_chunk_ids.add(chunk_id)
            entry = manifest.entries.get(chunk_id)
            if entry is None:
                continue
            if str(payload.get("embedding_model") or "") != entry.embedding_model:
                model_mismatch.append(chunk_id)
            if int(payload.get("embedding_dimension") or 0) != entry.embedding_dimension:
                dimension_mismatch.append(chunk_id)
            if str(payload.get("content_hash") or "") != entry.content_hash:
                content_mismatch.append(chunk_id)
            if str(payload.get("vector_input_hash") or "") != entry.vector_input_hash:
                vector_input_mismatch.append(chunk_id)
        orphan = [chunk_id for chunk_id in seen_chunk_ids if chunk_id not in manifest.entries]
        return IndexVerification(
            expected=len(manifest.entries),
            actual=actual,
            missing=sorted(set(manifest.entries) - seen_chunk_ids),
            orphan=orphan,
            model_mismatch=model_mismatch,
            dimension_mismatch=dimension_mismatch,
            content_mismatch=content_mismatch,
            vector_input_mismatch=vector_input_mismatch,
            errors=errors,
        )


UPSERT_BATCH = 128


def _scope_filter(scope: VectorScope | None) -> dict | None:
    if scope is None or scope.is_empty():
        return None
    must = []
    if scope.document_ids:
        must.append({"key": "document_id", "match": {"any": sorted(set(scope.document_ids))}})
    if scope.knowledge_base_ids:
        must.append(
            {"key": "knowledge_base_id", "match": {"any": sorted(set(scope.knowledge_base_ids))}}
        )
    # Phase D scope pushdown: type/tag clauses restrict server-side.  Points
    # without the payload field simply never match these clauses — correct,
    # because only managed documents carry them.
    if scope.document_types:
        must.append({"key": "document_type", "match": {"any": sorted(set(scope.document_types))}})
    if scope.tags:
        must.append({"key": "tags", "match": {"any": sorted(set(scope.tags))}})
    return {"must": must} if must else None


def _payload_of(record: VectorRecord, dimension: int) -> dict:
    payload = {
        "chunk_id": record.chunk_id,
        "document_id": record.document_id,
        "knowledge_base_id": record.knowledge_base_id or DEFAULT_KNOWLEDGE_BASE_ID,
        "document_title": record.document_title,
        "chapter": record.chapter,
        "section": record.section,
        "pdf_page_start": int(record.pdf_page_start),
        "pdf_page_end": int(record.pdf_page_end),
        "embedding_model": record.embedding_model,
        "embedding_dimension": int(dimension),
        "content_hash": record.content_hash,
        "vector_input_hash": record.vector_input_hash,
    }
    if record.kind is not None:
        payload["kind"] = record.kind
    if record.quality_score is not None:
        payload["quality_score"] = float(record.quality_score)
    if record.source_version is not None:
        payload["source_version"] = record.source_version
    if record.document_type:
        payload["document_type"] = record.document_type
    if record.tags:
        payload["tags"] = sorted(set(record.tags))
    return payload
