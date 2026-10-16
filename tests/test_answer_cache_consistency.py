"""Cache publication races through real SQLite, engine and HTTP server paths.

Only Ollama is replaced by the existing deterministic model fixture. Events
hold the real result's serialization window open while a real library mutation
commits and attempts its runtime callback. The old server publishes after that
callback; the fixed server completes publication before the callback clears it.
"""

from __future__ import annotations

import threading
from unittest import mock

from tests.test_importer import sample_markdown
from tests.test_runtime_integration import BODY_B, Q_B, RuntimeHarness


class DeferredResult:
    def __init__(self, result, before_serializing):
        self.result = result
        self.before_serializing = before_serializing

    def to_dict(self):
        self.before_serializing()
        return self.result.to_dict()


class AnswerCacheConsistencyTests(RuntimeHarness):
    def _submit(self, payload):
        status, created = self._request("POST", "/api/v2/jobs", payload, self.token)
        self.assertEqual(status, 202, created)
        job = self.server.get_job(created["job_id"])
        self.assertIsNotNone(job)
        return job

    def _wait_job(self, job):
        with job.condition:
            self.assertTrue(job.condition.wait_for(lambda: job.done, timeout=15), job.events)
        return job

    def _assert_cancelled(self, job):
        self._wait_job(job)
        self.assertEqual(job.status, "cancelled", job.events)
        self.assertTrue(self._events_contain(job, "cancelled"), job.events)
        self.assertFalse(self._events_contain(job, "final"), job.events)

    def _cancel(self, job):
        status, result = self._request("DELETE", f"/api/v2/jobs/{job.id}", token=self.token)
        self.assertEqual(status, 200, result)

    def _assert_miss(self, job):
        self.assertFalse(self._events_contain(job, "status", "命中缓存"), job.events)

    def _mutation_race(self, scope, mutation, *, unchanged_fingerprint=True):
        serialized = threading.Event()
        mutation_started = threading.Event()
        mutation_completed = threading.Event()
        callback = self.server._on_library_mutated
        real_answer = self.engine.answer
        answer_calls = []
        mutation_responses = []
        mutation_errors = []

        def notify():
            mutation_started.set()
            callback()
            mutation_completed.set()

        def serialization_window():
            serialized.set()
            if not mutation_started.wait(10):
                raise AssertionError("library mutation never reached its callback")
            # Before the fix the callback can clear the cache here, so hold the
            # old result until it has done so. With publication serialized by
            # the engine lock the callback waits; the bounded timeout lets the
            # answer finish and the waiting callback clear it afterward.
            mutation_completed.wait(1)

        def answer(*args, **kwargs):
            result = real_answer(*args, **kwargs)
            answer_calls.append(result)
            return DeferredResult(result, serialization_window) if len(answer_calls) == 1 else result

        def mutate():
            try:
                mutation_responses.append(mutation())
            except BaseException as exc:
                mutation_errors.append(exc)

        payload = {"question": Q_B}
        if scope is not None:
            payload["scope"] = scope
        fingerprint = self.server._engine_fingerprint
        self.service.on_mutated = notify
        with mock.patch.object(self.engine, "answer", side_effect=answer):
            old_job = self._submit(payload)
            self.assertTrue(serialized.wait(10), old_job.events)
            thread = threading.Thread(target=mutate, name="cache-race-library-mutation")
            thread.start()
            self.addCleanup(thread.join, 15)
            self.assertTrue(mutation_started.wait(10))
            old_result = self._final(self._wait_job(old_job))
            self.assertTrue(self._cited_documents(old_result), old_result)
            thread.join(15)
            self.assertFalse(thread.is_alive(), "library mutation deadlocked with answer publication")
            self.assertEqual(mutation_errors, [])
            self.assertEqual(mutation_responses[0][0], 200, mutation_responses)
            self.assertTrue(mutation_completed.is_set())
            if unchanged_fingerprint:
                self.assertEqual(fingerprint, self.server._engine_fingerprint)
            self.assertEqual(len(self.server._answer_cache), 0, "old result was reinserted after clear")
            fresh = self._run_job(payload)
            result = self._final(fresh)
            self._assert_miss(fresh)
            self.assertEqual(result["citations"], [], result)
            self.assertTrue(result["out_of_scope"], result)
            self.assertEqual(len(answer_calls), 2)

    def _disable_race(self, scope):
        _, imported = self._import("race.md", sample_markdown(BODY_B), tags=("信号处理",))
        document_id = imported["document_id"]
        self._mutation_race(scope, lambda: self._request(
            "POST", f"/api/v3/library/documents/{document_id}/disable", {}, self.token,
        ))

    def test_disable_cannot_reinsert_old_default_answer(self):
        self._disable_race(None)

    def test_disable_cannot_reinsert_old_knowledge_base_answer(self):
        self._disable_race({"knowledge_base_ids": ["kb-default"]})

    def test_disable_cannot_reinsert_old_tag_answer(self):
        self._disable_race({"tags": ["信号处理"]})

    def test_tag_change_cannot_reinsert_answer_for_removed_tag(self):
        _, imported = self._import("retag.md", sample_markdown(BODY_B), tags=("信号处理",))
        document_id = imported["document_id"]
        self._mutation_race({"tags": ["信号处理"]}, lambda: self._request(
            "POST", f"/api/v3/library/documents/{document_id}/tags", {"tags": ["其他"]}, self.token,
        ))

    def test_cache_lookup_waits_for_completed_runtime_refresh(self):
        _, imported = self._import("refresh.md", sample_markdown(BODY_B))
        self._answer(Q_B)
        refresh_entered = threading.Event()
        release_refresh = threading.Event()
        original_refresh = self.engine.library.refresh
        responses = []
        errors = []

        def refresh():
            refresh_entered.set()
            if not release_refresh.wait(10):
                raise AssertionError("test failed to release runtime refresh")
            return original_refresh()

        def mutate():
            try:
                responses.append(self._request(
                    "POST", f"/api/v3/library/documents/{imported['document_id']}/disable", {}, self.token,
                ))
            except BaseException as exc:
                errors.append(exc)

        self.addCleanup(release_refresh.set)
        with mock.patch.object(self.engine.library, "refresh", side_effect=refresh):
            thread = threading.Thread(target=mutate, name="cache-race-runtime-refresh")
            thread.start()
            self.addCleanup(thread.join, 15)
            self.assertTrue(refresh_entered.wait(10))
            # start/status events do not require the engine lock. Waiting for
            # one proves this request has reached the worker while refresh is
            # still paused, rather than merely sitting in the HTTP queue.
            job = self._submit({"question": Q_B})
            with job.condition:
                self.assertTrue(job.condition.wait_for(
                    lambda: self._events_contain(job, "status", "正在检索教材"), timeout=10,
                ))
            release_refresh.set()
            thread.join(15)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(responses[0][0], 200, responses)
            result = self._final(self._wait_job(job))
            self._assert_miss(job)
            self.assertEqual(result["citations"], [], result)

    def test_import_update_delete_invalidate_the_http_answer_cache(self):
        empty = self._run_job({"question": Q_B})
        self.assertEqual(self._final(empty)["citations"], [])
        cached_empty = self._run_job({"question": Q_B})
        self.assertTrue(self._events_contain(cached_empty, "status", "命中缓存"))
        source, imported = self._import("lifecycle.md", sample_markdown(BODY_B))
        document_id = imported["document_id"]
        after_import = self._run_job({"question": Q_B})
        self._assert_miss(after_import)
        self.assertEqual(self._cited_documents(self._final(after_import)), {document_id})
        source.write_text(sample_markdown(BODY_B + "新增内容：均衡器抽头系数更新。"), encoding="utf-8")
        _, updated = self._import("lifecycle.md", source.read_text(encoding="utf-8"))
        self.assertEqual(updated["document_id"], document_id)
        after_update = self._run_job({"question": Q_B})
        self._assert_miss(after_update)
        self.assertEqual(self._cited_documents(self._final(after_update)), {document_id})
        status, deleted = self._request("DELETE", f"/api/v3/library/documents/{document_id}", token=self.token)
        self.assertEqual(status, 200, deleted)
        after_delete = self._run_job({"question": Q_B})
        self._assert_miss(after_delete)
        self.assertEqual(self._final(after_delete)["citations"], [])

    def test_explicit_document_selection_still_allows_disabled_ready_document(self):
        _, imported = self._import("explicit.md", sample_markdown(BODY_B), tags=("信号处理",))
        document_id = imported["document_id"]
        scope = {"document_ids": [document_id]}
        self.assertEqual(self._cited_documents(self._answer(Q_B, scope)), {document_id})
        status, result = self._request(
            "POST", f"/api/v3/library/documents/{document_id}/disable", {}, self.token,
        )
        self.assertEqual(status, 200, result)
        self.assertEqual(self._answer(Q_B)["citations"], [])
        explicit = self._run_job({"question": Q_B, "scope": scope})
        self._assert_miss(explicit)
        self.assertEqual(self._cited_documents(self._final(explicit)), {document_id})

    def test_explicit_nothing_scope_does_not_share_default_scope_cache(self):
        _, imported = self._import("nothing.md", sample_markdown(BODY_B))
        for first_scope, second_scope in (({}, {"match_nothing": True}), ({"match_nothing": True}, {})):
            with self.subTest(first_scope=first_scope):
                self.server._on_library_mutated()
                first = self._run_job({"question": Q_B, "scope": first_scope})
                second = self._run_job({"question": Q_B, "scope": second_scope})
                self._assert_miss(second)
                for job, scope in ((first, first_scope), (second, second_scope)):
                    result = self._final(job)
                    expected = set() if scope.get("match_nothing") else {imported["document_id"]}
                    self.assertEqual(self._cited_documents(result), expected)

    def test_history_bypasses_cache_and_does_not_replace_single_turn_entry(self):
        self._import("history.md", sample_markdown(BODY_B))
        history = [{"question": Q_B, "answer": "均衡技术补偿信道失真。"}]
        with mock.patch.object(self.engine, "answer", wraps=self.engine.answer) as answer:
            self._final(self._run_job({"question": Q_B}))
            for _ in range(2):
                job = self._run_job({"question": Q_B, "history": history})
                self._final(job)
                self._assert_miss(job)
            single_turn = self._run_job({"question": Q_B})
            self._final(single_turn)
            self.assertTrue(self._events_contain(single_turn, "status", "命中缓存"))
            self.assertEqual(answer.call_count, 3)
            self.assertEqual(len(self.server._answer_cache), 1)

    def test_cancel_during_serialization_neither_caches_nor_completes(self):
        self._import("cancel.md", sample_markdown(BODY_B))
        serializing = threading.Event()
        release = threading.Event()
        real_answer = self.engine.answer

        def wait():
            serializing.set()
            if not release.wait(10):
                raise AssertionError("serialization not released")

        def answer(*args, **kwargs):
            return DeferredResult(real_answer(*args, **kwargs), wait)

        self.addCleanup(release.set)
        with mock.patch.object(self.engine, "answer", side_effect=answer):
            job = self._submit({"question": Q_B})
            self.assertTrue(serializing.wait(10))
            self._cancel(job)
            release.set()
            self._assert_cancelled(job)
        self.assertEqual(len(self.server._answer_cache), 0)
        fresh = self._run_job({"question": Q_B})
        self._final(fresh)
        self._assert_miss(fresh)

    def test_cancel_during_cache_lookup_does_not_emit_final(self):
        self._import("cancel-hit.md", sample_markdown(BODY_B))
        self._answer(Q_B)
        lookup_started = threading.Event()
        release = threading.Event()
        real_get = self.server._cache_get

        def lookup(key):
            result = real_get(key)
            lookup_started.set()
            if not release.wait(10):
                raise AssertionError("cache lookup not released")
            return result

        self.addCleanup(release.set)
        with mock.patch.object(self.server, "_cache_get", side_effect=lookup):
            job = self._submit({"question": Q_B})
            self.assertTrue(lookup_started.wait(10))
            self._cancel(job)
            release.set()
            self._assert_cancelled(job)
        self.assertEqual(len(self.server._answer_cache), 1)

    def test_cancelled_queued_job_does_not_call_engine_or_populate_cache(self):
        self._import("cancel-queue.md", sample_markdown(BODY_B))
        generating = threading.Event()
        release = threading.Event()
        real_answer = self.engine.answer

        def answer(*args, **kwargs):
            generating.set()
            if not release.wait(10):
                raise AssertionError("generation not released")
            return real_answer(*args, **kwargs)

        self.addCleanup(release.set)
        with mock.patch.object(self.engine, "answer", side_effect=answer) as call:
            first = self._submit({"question": Q_B})
            self.assertTrue(generating.wait(10))
            queued = self._submit({"question": "不应被执行的排队问题"})
            self._cancel(queued)
            release.set()
            self._final(self._wait_job(first))
            self._assert_cancelled(queued)
            self.assertEqual(call.call_count, 1)
        self.assertEqual(len(self.server._answer_cache), 1)
