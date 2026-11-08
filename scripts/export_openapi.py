"""Export the HTTP contract to docs/openapi.json (P1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop.api_contract import build_openapi  # noqa: E402


def main() -> int:
    target = ROOT / "docs" / "openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    document = build_openapi()
    print(f"wrote {target}  paths={len(document['paths'])}  schemas={len(document['components']['schemas'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
