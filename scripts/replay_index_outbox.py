"""Replay pending index-outbox events after a crash (P2 ops entry).

    python -X utf8 scripts/replay_index_outbox.py            # dry-run: show stats
    python -X utf8 scripts/replay_index_outbox.py --apply    # consume pending events

Events are idempotent: Qdrant point ids are deterministic, so replaying a
DOCUMENT_UPSERTED / DOCUMENT_DELETED event is always safe.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config  # noqa: E402
from core.library_service import LibraryService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--apply", action="store_true", help="consume pending events")
    args = parser.parse_args()
    service = LibraryService(args.library)
    before = service.outbox_stats()
    print("outbox_before:", before)
    if args.apply:
        print("replay:", service.replay_outbox())
        print("outbox_after:", service.outbox_stats())
    else:
        print("dry-run: pass --apply to consume pending events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
