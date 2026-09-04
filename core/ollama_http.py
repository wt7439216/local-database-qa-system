"""Small stdlib-only Ollama client used by the packaged applications."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterator

from core import config


class OllamaError(RuntimeError):
    """A user-facing Ollama connection or response error."""


class OllamaClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or config.OLLAMA_URL).rstrip("/")

    def list_models(self, timeout: float = 5.0) -> list[dict[str, Any]]:
        data = self._request("/api/tags", timeout=timeout)
        models = data.get("models", [])
        return models if isinstance(models, list) else []

    def embed(
        self,
        inputs: str | list[str],
        model: str | None = None,
        timeout: float = 180.0,
    ) -> list[list[float]]:
        values = [inputs] if isinstance(inputs, str) else list(inputs)
        if not values:
            return []

        data = self._request(
            "/api/embed",
            {
                "model": model or config.EMBEDDING_MODEL,
                "input": values,
                "truncate": True,
                "keep_alive": "10m",
            },
            timeout=timeout,
        )
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(values):
            raise OllamaError("Ollama 返回的向量数量不正确。")
        return embeddings

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> str:
        data = self._request(
            "/api/generate",
            {
                "model": model or config.ANSWER_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 1,
                    "repeat_penalty": 1.2,
                    "num_predict": config.ANSWER_NUM_PREDICT,
                },
            },
            timeout=timeout,
        )
        answer = data.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise OllamaError("Ollama 没有返回有效答案。")
        return answer.strip()

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 600.0,
    ) -> str:
        data = self._request(
            "/api/chat",
            {
                "model": model or config.ANSWER_MODEL,
                "messages": messages,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 1,
                    "repeat_penalty": 1.15,
                    "num_predict": config.ANSWER_NUM_PREDICT,
                    "num_ctx": config.ANSWER_CONTEXT_WINDOW,
                },
            },
            timeout=timeout,
        )
        message = data.get("message")
        answer = message.get("content") if isinstance(message, dict) else None
        if not isinstance(answer, str) or not answer.strip():
            raise OllamaError("Ollama 没有返回有效答案。")
        return answer.strip()

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        timeout: float = 600.0,
    ) -> Iterator[str]:
        payload = {
            "model": model or config.ANSWER_MODEL,
            "messages": messages,
            "stream": True,
            "keep_alive": "10m",
            "options": {
                "temperature": 0,
                "top_p": 1,
                "top_k": 1,
                "repeat_penalty": 1.15,
                "num_predict": config.ANSWER_NUM_PREDICT,
                "num_ctx": config.ANSWER_CONTEXT_WINDOW,
            },
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Accept": "application/x-ndjson", "Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    data = json.loads(raw_line.decode("utf-8"))
                    if data.get("error"):
                        raise OllamaError(f"Ollama 错误：{data['error']}")
                    message = data.get("message")
                    content = message.get("content") if isinstance(message, dict) else None
                    if content:
                        yield str(content)
        except urllib.error.HTTPError as exc:
            raise OllamaError(f"Ollama 请求失败（HTTP {exc.code}）") from exc
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaError(f"Ollama 流式请求失败：{exc}") from exc

    def _request(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method="POST" if body is not None else "GET",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                parsed = json.loads(exc.read().decode("utf-8", errors="replace"))
                detail = str(parsed.get("error") or "")
            except Exception:
                pass
            suffix = f"：{detail}" if detail else ""
            raise OllamaError(f"Ollama 请求失败（HTTP {exc.code}）{suffix}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise OllamaError(
                f"无法连接 Ollama（{self.base_url}）。请先启动 Ollama。"
            ) from exc

        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaError("Ollama 返回了无法解析的数据。") from exc
        if not isinstance(data, dict):
            raise OllamaError("Ollama 返回的数据格式不正确。")
        if data.get("error"):
            raise OllamaError(f"Ollama 错误：{data['error']}")
        return data
