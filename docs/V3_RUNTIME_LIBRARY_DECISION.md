# Runtime Library Identity Decision (Phase D.1 / v3.3)

Status: accepted (implemented).  Scope: P0-01 / P0-02 closure — the Library
Manager and the QA engine must operate on ONE library at runtime.

## Problem

Before Phase D.1 the desktop server had two SQLite truth sources:

- `LibraryService` (Library Manager, `/api/v3/library`) wrote
  `data/library/documents.sqlite3` (managed library, v5 registry);
- `StructuredQAEngine` read `config.LIBRARY_DB`
  (`data/library/textbooks.sqlite3`, legacy v4).

Consequences (all reproduced before this change):

- **P0-01** — a document imported through the manager was invisible to the
  QA engine: import wrote file A, answers read file B.
- **P0-02** — the Qdrant index drifted: importer wrote the
  `general_documents` collection while the engine read
  `config.QDRANT_COLLECTION` (`local_knowledge_chunks`); snapshots were
  taken at construction, so imports/updates/deletes required a restart.

## Decision

One machine has ONE runtime library.  `core.runtime_library.resolve_runtime_library()`
picks it with static, explainable rules and both the engine and the manager
are constructed from that single path:

1. managed library (`documents.sqlite3`) exists → it is the runtime
   library, upgraded in place to the v5 registry if still v4;
2. only the legacy library (`config.LIBRARY_DB`) exists → it is upgraded
   **in place** (additive registry, content untouched — never copied) and
   adopted, so pre-existing textbook content keeps working with zero
   migration steps;
3. neither exists → a fresh empty managed library is created.

A machine that has both files keeps the managed library; legacy content is
re-imported through the manager (deleting the managed file flips the
selection back to the legacy file without losing a single v4 chunk).

Selection happens once at startup and never per-request; failures are loud
(`RuntimeError`), never a silent fallback to a different file.

## Why this is NOT a Phase E boundary violation

Phase E (not started at the time of writing) is about query-time behavior: intent routing,
pronoun resolution, retrieval/ranking strategy changes.  This change is a
**construction-time identity fix**:

- the selection is a startup-only, static function of which files exist —
  there is no per-query routing table, no intent classifier, no dynamic
  "multi-library Router";
- no query is ever answered from two libraries; the effective scope stays
  a single `QueryScope` resolved against one registry (one scope truth
  source);
- the Qdrant collection identity is bound to the QA SQLite identity via
  `create_vector_store(..., collection=...)` — managed library (schema v5)
  reads/writes `DEFAULT_GENERAL_COLLECTION`, legacy v4 keeps
  `config.QDRANT_COLLECTION`; there is no "write C / read D" path.

## Runtime sync boundary (P0-02)

`LibraryService` commits a mutation, then invokes its `on_mutated` callback
(the web server subscribes once at startup):

```
mutation (under LibraryService._mutation_lock)
  → commit
  → on_mutated()
      → under WebQAServer._engine_lock:
          engine.library.refresh()      # snapshots + dense index reload
          fingerprint recompute
          answer-cache clear
```

- no event bus, no background poller — an explicit callback chain keeps the
  refresh deterministic and testable;
- `_engine_lock` already serializes the answer path, so an in-flight answer
  finishes against the old consistent snapshot;
- the cache is cleared unconditionally on every mutation, so stale answers
  can never survive an import/update/disable/enable/delete even when the
  fingerprint itself is unchanged.

## Concurrency and FK discipline (P1, same change set)

- `document_sources.document_id` references `documents(id)`; with
  `PRAGMA foreign_keys = ON` on every `LibraryService` connection the
  import path inserts a placeholder `documents` row before the registry
  row (the importer keeps its own FK-off connection — its delete-replace
  write pattern predates the registry).
- All service mutations are serialized by `threading.RLock`, so two
  concurrent imports of the same path resolve to one persisted identity
  (the race previously produced two identities).

## Deferred: Windows data directory relocation (P1, no code change)

The managed/legacy libraries, telemetry and logs live in `data/` next to the
program (portable layout), which mirrors the pre-existing local edition.  If
the app is ever installed under a write-protected location (e.g.
`C:\Program Files`), that layout can fail.  Phase D.1 decision: keep the
portable `data/` layout; a move to `%LOCALAPPDATA%\LocalDatabaseQA\` is
registered as backlog (see V3_PROGRESS.md, Phase D.1 Backlog) and must be
designed together with the packaged-runtime (PyInstaller) story — no
behavior change in this phase.
